from django.db import transaction

from dash import constants
from dash import forms
from dash import models
from dash import upload_plus

from dash.views import helpers

from utils import api_common
from utils import exc


class MultipleAdsUpload(api_common.BaseApiView):

    def _update_ad_group_batch_settings(self, request, ad_group, cleaned_fields):
        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.description = cleaned_fields['description']
        new_settings.display_url = cleaned_fields['display_url']
        new_settings.brand_name = cleaned_fields['brand_name']
        new_settings.call_to_action = cleaned_fields['call_to_action']
        new_settings.save(request)

    def _augment_candidates_data(self, cleaned_fields):
        # TODO: move this into form when it's no longer in use for old upload
        for content_ad in cleaned_fields['content_ads']:
            if 'description' not in content_ad:
                content_ad['description'] = cleaned_fields['description']
            if 'brand_name' not in content_ad:
                content_ad['brand_name'] = cleaned_fields['brand_name']
            if 'display_url' not in content_ad:
                content_ad['display_url'] = cleaned_fields['display_url']
            if 'call_to_action' not in content_ad:
                content_ad['call_to_action'] = cleaned_fields['call_to_action']

        return cleaned_fields['content_ads']

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        current_settings = ad_group.get_current_settings()
        return self.create_api_response({
            'defaults': {
                'display_url': current_settings.display_url,
                'brand_name': current_settings.brand_name,
                'description': current_settings.description,
                'call_to_action': current_settings.call_to_action or 'Read More'
            }
        })

    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        form = forms.AdGroupAdsUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        batch_name = form.cleaned_data['batch_name']
        content_ads = form.cleaned_data['content_ads']
        self._augment_candidates_data(form.cleaned_data)

        with transaction.atomic():
            self._update_ad_group_batch_settings(request, ad_group, form.cleaned_data)
            batch, candidates = upload_plus.insert_candidates(content_ads, ad_group, batch_name)
        for candidate in candidates:
            upload_plus.invoke_external_validation(candidate)
        errors = upload_plus.validate_candidates(candidates)
        return self.create_api_response({
            'batch_id': batch.id,
            'candidates': [c.id for c in candidates],
            'errors': errors,
        })


class UploadStatus(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        candidates = models.ContentAdCandidate.objects.filter(
            ad_group=ad_group,  # to check user has access
            batch_id=batch_id,
        )

        candidate_ids = request.GET.get('candidates')
        if candidate_ids:
            candidates = candidates.filter(id__in=candidate_ids)

        result = {}
        for candidate in candidates:
            result[candidate.id] = {
                'image_status': candidate.image_status,
                'url_status': candidate.url_status,
            }

        return self.create_api_response({
            'candidates': result
        })


class UploadSave(api_common.BaseApiView):

    def post(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        upload_plus.persist_candidates(ad_group, batch_id)
        helpers.log_useraction_if_necessary(request, constants.UserActionType.UPLOAD_CONTENT_ADS,
                                            ad_group=ad_group)

        return self.create_api_response({})
