import json

from django.db import transaction
from django.template.defaultfilters import pluralize

from dash import constants
from dash import forms
from dash import models
from dash import upload

from dash.views import helpers

from utils import api_common
from utils import exc


class UploadCsv(api_common.BaseApiView):

    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        form = forms.AdGroupAdsUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        batch_name = form.cleaned_data['batch_name']
        candidates_data = form.cleaned_data['candidates']
        filename = request.FILES['candidates'].name

        with transaction.atomic():
            batch, candidates = upload.insert_candidates(
                candidates_data,
                ad_group,
                batch_name,
                filename,
            )

        for candidate in candidates:
            upload.invoke_external_validation(candidate, batch)

        candidates_result = upload.get_candidates_with_errors(candidates)
        return self.create_api_response({
            'batch_id': batch.id,
            'candidates': candidates_result,
        })


class UploadStatus(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
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
                             in upload.get_candidates_with_errors(candidates)}
        return self.create_api_response({
            'candidates': candidates_result,
        })


class UploadSave(api_common.BaseApiView):

    def post(self, request, ad_group_id, batch_id):
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
                content_ads = upload.persist_candidates(batch)
            except (upload.InvalidBatchStatus, upload.CandidateErrorsRemaining) as e:
                raise exc.ValidationError(message=e.message)

            upload.create_redirect_ids(content_ads)
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

        return self.create_api_response({
            'num_successful': len(content_ads),
        })


class UploadCancel(api_common.BaseApiView):

    def post(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        try:
            upload.cancel_upload(batch)
        except upload.InvalidBatchStatus:
            raise exc.ValidationError(errors={
                'cancel': 'Cancel action unsupported at this stage',
            })

        return self.create_api_response({})


class CandidatesDownload(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        batch_name = batch.name
        if 'batch_name' in request.GET:
            batch_name = request.GET['batch_name']

        content = upload.get_candidates_csv(batch)
        return self.create_csv_response(batch_name, content=content)


class Candidate(api_common.BaseApiView):

    def put(self, request, ad_group_id, batch_id, candidate_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')

        resource = json.loads(request.body)

        try:
            upload.update_candidate(resource['candidate'], resource['defaults'], batch)
        except models.ContentAdCandidate.DoesNotExist:
            raise exc.MissingDataError('Candidate does not exist')

        return self.create_api_response({
            'candidates': upload.get_candidates_with_errors(batch.contentadcandidate_set.all()),
        })

    def delete(self, request, ad_group_id, batch_id, candidate_id):
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
