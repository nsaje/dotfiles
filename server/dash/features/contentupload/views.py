import json

from django.db import transaction
from django.http import Http404

from dash import constants
from dash import forms
from dash import models
from dash.views import helpers
from utils import api_common
import utils.exc

import upload
import exc


class UploadBatch(api_common.BaseApiView):

    def post(self, request, ad_group_id):
        helpers.get_ad_group(request.user, ad_group_id)  # check access permission

        resource = json.loads(request.body)
        form = forms.AdGroupAdsUploadBaseForm(resource)
        if not form.is_valid():
            raise utils.exc.ValidationError(errors=form.errors)

        batch = models.UploadBatch.objects.create(
            request.user, form.cleaned_data['batch_name'], ad_group_id)

        candidate = upload.add_candidate(batch)
        return self.create_api_response({
            'batch_id': batch.id,
            'batch_name': batch.name,
            'candidates': [candidate.to_dict()],
        })


class UploadCsv(api_common.BaseApiView):

    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        form = forms.AdGroupAdsUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise utils.exc.ValidationError(errors=form.errors)

        batch_name = form.cleaned_data['batch_name']
        candidates_data = form.cleaned_data['candidates']
        filename = request.FILES['candidates'].name

        batch, candidates = upload.insert_candidates(
            request.user,
            candidates_data,
            ad_group,
            batch_name,
            filename,
        )

        candidates_result = upload.get_candidates_with_errors(candidates)
        return self.create_api_response({
            'batch_id': batch.id,
            'batch_name': batch.name,
            'candidates': candidates_result,
        })


class UploadStatus(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError('Upload batch does not exist')

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

    def _execute_save(self, request, ad_group, batch):
        resource = {
            'batch_name': batch.name,
        }
        resource.update(json.loads(request.body))
        form = forms.AdGroupAdsUploadBaseForm(resource)
        if not form.is_valid():
            raise utils.exc.ValidationError(errors=form.errors)

        with transaction.atomic():
            batch.name = form.cleaned_data['batch_name']
            batch.save()

            try:
                content_ads = upload.persist_batch(batch)
            except (exc.InvalidBatchStatus, exc.CandidateErrorsRemaining) as e:
                raise utils.exc.ValidationError(message=e.message)

        return content_ads

    def _execute_update(self, request, batch):
        try:
            return upload.persist_edit_batch(request, batch)
        except (exc.InvalidBatchStatus, exc.CandidateErrorsRemaining) as e:
            raise utils.exc.ValidationError(message=e.message)

    def post(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError('Upload batch does not exist')

        if batch.type != constants.UploadBatchType.EDIT:
            content_ads = self._execute_save(request, ad_group, batch)
        elif request.user.has_perm('zemauth.can_edit_content_ads'):
            content_ads = self._execute_update(request, batch)
        else:
            raise Http404('Permission denied')

        return self.create_api_response({
            'num_successful': len(content_ads),
        })


class UploadCancel(api_common.BaseApiView):

    def post(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError('Upload batch does not exist')

        try:
            upload.cancel_upload(batch)
        except exc.InvalidBatchStatus:
            raise utils.exc.ValidationError(errors={
                'cancel': 'Cancel action unsupported at this stage',
            })

        return self.create_api_response({})


class CandidatesDownload(api_common.BaseApiView):

    def get(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError('Upload batch does not exist')

        batch_name = batch.name
        if 'batch_name' in request.GET:
            batch_name = request.GET['batch_name']

        content = upload.get_candidates_csv(batch)
        return self.create_csv_response(batch_name, content=content)


class CandidateUpdate(api_common.BaseApiView):

    def _get_ad_group_batch(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError('Upload batch does not exist')

        return ad_group, batch

    def post(self, request, ad_group_id, batch_id, candidate_id):
        _, batch = self._get_ad_group_batch(request, ad_group_id, batch_id)
        resource = json.loads(request.POST['data'])

        try:
            updated_fields, errors = upload.update_candidate(
                resource['candidate'], resource['defaults'], batch, request.FILES)
        except models.ContentAdCandidate.DoesNotExist:
            raise utils.exc.MissingDataError('Candidate does not exist')

        return self.create_api_response({
            'updated_fields': updated_fields,
            'errors': errors,
        })


class Candidate(api_common.BaseApiView):

    def _get_ad_group_batch(self, request, ad_group_id, batch_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        try:
            batch = ad_group.uploadbatch_set.get(id=batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError('Upload batch does not exist')

        return ad_group, batch

    def get(self, request, ad_group_id, batch_id, candidate_id=None):
        if candidate_id:
            raise utils.exc.ValidationError('Not supported')
        _, batch = self._get_ad_group_batch(request, ad_group_id, batch_id)

        return self.create_api_response({
            'candidates': upload.get_candidates_with_errors(batch.contentadcandidate_set.all()),
        })

    def post(self, request, ad_group_id, batch_id, candidate_id=None):
        if candidate_id:
            raise utils.exc.ValidationError('Not supported')
        _, batch = self._get_ad_group_batch(request, ad_group_id, batch_id)
        candidate = upload.add_candidate(batch)

        return self.create_api_response({
            'candidate': candidate.to_dict(),  # don't add errors for new candidate
        })

    def delete(self, request, ad_group_id, batch_id, candidate_id):
        _, batch = self._get_ad_group_batch(request, ad_group_id, batch_id)
        try:
            candidate = batch.contentadcandidate_set.get(id=candidate_id)
        except models.ContentAdCandidate.DoesNotExist:
            raise utils.exc.MissingDataError('Candidate does not exist')

        upload.delete_candidate(candidate)
        return self.create_api_response({})
