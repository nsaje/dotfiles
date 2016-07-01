import json
import os
from urlparse import urlparse

import boto.exception
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404
from django.template.defaultfilters import pluralize

from dash import constants
from dash import forms
from dash import models
from dash import upload_plus

from dash.views import helpers

from utils import api_common
from utils import exc
from utils import s3helpers
from utils import redirector_helper


class UploadCsv(api_common.BaseApiView):

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
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

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
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        form = forms.AdGroupAdsUploadExtendedForm(request.POST, request.FILES)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        batch_name = form.cleaned_data['batch_name']
        content_ads = form.cleaned_data['content_ads']
        filename = request.FILES['content_ads'].name
        self._augment_candidates_data(form.cleaned_data)

        with transaction.atomic():
            self._update_ad_group_batch_settings(request, ad_group, form.cleaned_data)
            batch, candidates = upload_plus.insert_candidates(content_ads, ad_group, batch_name, filename)
        for candidate in candidates:
            upload_plus.invoke_external_validation(candidate, batch)
        errors = upload_plus.validate_candidates(candidates)
        return self.create_api_response({
            'batch_id': batch.id,
            'candidates': [c.id for c in candidates],
            'errors': errors,
        })


class UploadMultiple(api_common.BaseApiView):

    def _augment_candidates_data(self, ad_group, cleaned_fields):
        ad_group_settings = ad_group.get_current_settings()
        for content_ad in cleaned_fields['content_ads']:
            if 'display_url' not in content_ad or not content_ad['display_url']:
                content_ad['display_url'] = urlparse(content_ad['url']).netloc
            if 'brand_name' not in content_ad or not content_ad['brand_name']:
                content_ad['brand_name'] = ad_group_settings.brand_name
            if 'call_to_action' not in content_ad or not content_ad['call_to_action']:
                content_ad['call_to_action'] = 'Read more'

        return cleaned_fields['content_ads']

    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.can_upload_with_picker'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        form = forms.AdGroupAdsUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        batch_name = form.cleaned_data['batch_name']
        content_ads = form.cleaned_data['content_ads']
        filename = request.FILES['content_ads'].name

        self._augment_candidates_data(ad_group, form.cleaned_data)
        with transaction.atomic():
            batch, candidates = upload_plus.insert_candidates(
                content_ads,
                ad_group,
                batch_name,
                filename,
            )

        for candidate in candidates:
            upload_plus.invoke_external_validation(candidate, batch)

        candidates_result = upload_plus.get_candidates_with_errors(candidates)
        return self.create_api_response({
            'batch_id': batch.id,
            'candidates': candidates_result,
        })


class UploadStatus(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        candidates = batch.contentadcandidate_set.all()
        candidate_ids = request.GET.get('candidates')

        if candidate_ids:
            candidate_ids = candidate_ids.strip().split(',')
            candidates = candidates.filter(id__in=candidate_ids)

        candidates_result = {candidate['id']: candidate for candidate
                             in upload_plus.get_candidates_with_errors(candidates)}
        return self.create_api_response({
            'candidates': candidates_result,
        })


class UploadSave(api_common.BaseApiView):

    def _create_redirect_ids(self, content_ads):
        redirector_batch = redirector_helper.insert_redirects_batch(content_ads)
        for content_ad in content_ads:
            content_ad.url = redirector_batch[str(content_ad.id)]["redirect"]["url"]
            content_ad.redirect_id = redirector_batch[str(content_ad.id)]["redirectid"]
            content_ad.save()

    def post(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        resource = {
            'batch_name': batch.name,
        }
        resource.update(json.loads(request.body))
        form = forms.AdGroupAdsUploadBaseForm(resource)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        with transaction.atomic():
            batch.name = form.cleaned_data['batch_name']
            batch.save()

            try:
                content_ads = upload_plus.persist_candidates(batch)
            except upload_plus.InvalidBatchStatus as e:
                raise exc.ValidationError(message=e.message)

            self._create_redirect_ids(content_ads)
            changes_text = 'Imported batch "{}" with {} content ad{}.'.format(
                batch.name,
                len(content_ads),
                pluralize(len(content_ads)),
            )
            ad_group.write_history(
                changes_text,
                user=request.user,
                action_type=constants.HistoryActionType.CONTENT_AD_CREATE)
            helpers.log_useraction_if_necessary(request, constants.UserActionType.UPLOAD_CONTENT_ADS,
                                                ad_group=ad_group)

        error_report = None
        if batch.error_report_key:
            error_report = reverse('upload_plus_error_report',
                                   kwargs={'ad_group_id': ad_group_id, 'batch_id': batch.id})
        return self.create_api_response({
            'num_successful': len(content_ads),
            'num_errors': batch.num_errors,
            'error_report': error_report,
        })


class UploadCancel(api_common.BaseApiView):

    def post(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        try:
            upload_plus.cancel_upload(batch)
        except upload_plus.InvalidBatchStatus:
            raise exc.ValidationError(errors={
                'cancel': 'Cancel action unsupported at this stage',
            })

        return self.create_api_response({})


class CandidatesDownload(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        batch_name = batch.name
        if 'batch_name' in request.GET:
            batch_name = request.GET['batch_name']

        content = upload_plus.get_candidates_csv(batch)
        return self.create_csv_response(batch_name, content=content)


class UploadErrorReport(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        if batch.status != constants.UploadBatchStatus.DONE:
            raise exc.ValidationError()

        if not batch.error_report_key:
            raise exc.ValidationError()

        try:
            content = s3helpers.S3Helper().get(batch.error_report_key)
        except boto.exception.S3ResponseError:
            raise exc.MissingDataError('Error report does not exist')

        basefnm, _ = os.path.splitext(
            os.path.basename(batch.error_report_key))

        name = basefnm.rsplit('_', 1)[0] + '_errors'
        return self.create_csv_response(name, content=content)


class Candidate(api_common.BaseApiView):

    def put(self, request, ad_group_id, batch_id, candidate_id):
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        resource = json.loads(request.body)

        try:
            upload_plus.update_candidate(resource['candidate'], resource['defaults'], batch)
        except models.ContentAdCandidate.DoesNotExist:
            raise exc.MissingDataError('Candidate does not exist')

        return self.create_api_response({
            'candidates': upload_plus.get_candidates_with_errors(batch.contentadcandidate_set.all()),
        })

    def delete(self, request, ad_group_id, batch_id, candidate_id):
        if not request.user.has_perm('zemauth.can_use_improved_ads_upload'):
            raise Http404('Forbidden')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        try:
            candidate = batch.contentadcandidate_set.get(id=candidate_id)
        except models.ContentAdCandidate.DoesNotExist:
            raise exc.MissingDataError('Candidate does not exist')

        candidate.delete()
        return self.create_api_response({})
