import json

from django.db import transaction
from django.http import Http404

import utils.exc
from dash import constants
from dash import forms
from dash import models
from dash.views import helpers
from utils import api_common

from . import exc
from . import upload


def _get_account_ad_group(user, form):
    account = helpers.get_account(user, form.cleaned_data["account_id"])  # check access permission
    ad_group = None
    if form.cleaned_data["ad_group_id"]:
        ad_group = helpers.get_ad_group(user, form.cleaned_data["ad_group_id"])
    return account, ad_group


class UploadBatch(api_common.BaseApiView):
    def post(self, request):
        resource = json.loads(request.body)
        form = forms.AdGroupAdsUploadBaseForm(resource)
        if not form.is_valid():
            raise utils.exc.ValidationError(errors=form.errors)

        account, ad_group = _get_account_ad_group(request.user, form)

        batch = models.UploadBatch.objects.create(
            request.user, account, form.cleaned_data["batch_name"], ad_group=ad_group
        )

        candidates = []
        if not request.GET.get("withoutCandidates"):
            candidates = [upload.add_candidate(batch)]
        return self.create_api_response(
            {
                "batch_id": batch.id,
                "batch_name": batch.name,
                "candidates": [candidate.to_dict() for candidate in candidates],
            }
        )


class UploadCsv(api_common.BaseApiView):
    def post(self, request):
        form = forms.AdGroupAdsUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise utils.exc.ValidationError(errors=form.errors)

        account, ad_group = _get_account_ad_group(request.user, form)

        batch_name = form.cleaned_data["batch_name"]
        candidates_data = form.cleaned_data["candidates"]
        filename = request.FILES["candidates"].name

        batch, candidates = upload.insert_candidates(
            request.user, account, candidates_data, ad_group, batch_name, filename
        )

        candidates_result = upload.get_candidates_with_errors(candidates)
        return self.create_api_response(
            {"batch_id": batch.id, "batch_name": batch.name, "candidates": candidates_result}
        )


class UploadStatus(api_common.BaseApiView):
    def get(self, request, batch_id):
        batch = helpers.get_upload_batch(request.user, batch_id)

        candidates = batch.contentadcandidate_set.all()
        candidate_ids = request.GET.get("candidates")

        if candidate_ids:
            candidate_ids = candidate_ids.strip().split(",")
            candidates = candidates.filter(id__in=candidate_ids)

        candidates_result = {candidate["id"]: candidate for candidate in upload.get_candidates_with_errors(candidates)}
        return self.create_api_response({"candidates": candidates_result})


class UploadSave(api_common.BaseApiView):
    def _execute_save(self, request, batch):
        resource = {"batch_name": batch.name}
        resource.update(json.loads(request.body))
        form = forms.AdGroupAdsUploadBaseForm(resource)
        if not form.is_valid():
            raise utils.exc.ValidationError(errors=form.errors)

        with transaction.atomic():
            batch.name = form.cleaned_data["batch_name"]
            batch.save()

            try:
                content_ads = upload.persist_batch(batch)
            except (exc.InvalidBatchStatus, exc.CandidateErrorsRemaining) as e:
                raise utils.exc.ValidationError(message=str(e))

        return content_ads

    def _execute_update(self, request, batch):
        try:
            return upload.persist_edit_batch(request, batch)
        except (exc.InvalidBatchStatus, exc.CandidateErrorsRemaining) as e:
            raise utils.exc.ValidationError(message=str(e))

    def post(self, request, batch_id):
        batch = helpers.get_upload_batch(request.user, batch_id)

        if batch.type != constants.UploadBatchType.EDIT:
            content_ads = self._execute_save(request, batch)
        elif request.user.has_perm("zemauth.can_edit_content_ads"):
            content_ads = self._execute_update(request, batch)
        else:
            raise Http404("Permission denied")

        return self.create_api_response({"num_successful": len(content_ads)})


class UploadCancel(api_common.BaseApiView):
    def post(self, request, batch_id):
        batch = helpers.get_upload_batch(request.user, batch_id)

        try:
            upload.cancel_upload(batch)
        except exc.InvalidBatchStatus:
            raise utils.exc.ValidationError(errors={"cancel": "Cancel action unsupported at this stage"})

        return self.create_api_response({})


class CandidatesDownload(api_common.BaseApiView):
    def get(self, request, batch_id):
        batch = helpers.get_upload_batch(request.user, batch_id)

        batch_name = batch.name
        if "batch_name" in request.GET:
            batch_name = request.GET["batch_name"]

        content = upload.get_candidates_csv(batch)
        return self.create_csv_response(batch_name, content=content)


class CandidateUpdate(api_common.BaseApiView):
    def post(self, request, batch_id, candidate_id):
        batch = helpers.get_upload_batch(request.user, batch_id)
        resource = json.loads(request.POST["data"])

        try:
            updated_fields, errors = upload.update_candidate(
                resource["candidate"], resource["defaults"], batch, request.FILES
            )
        except models.ContentAdCandidate.DoesNotExist:
            raise utils.exc.MissingDataError("Candidate does not exist")

        return self.create_api_response({"updated_fields": updated_fields, "errors": errors})


class Candidate(api_common.BaseApiView):
    def get(self, request, batch_id, candidate_id=None):
        if candidate_id:
            raise utils.exc.ValidationError("Not supported")

        try:
            batch = helpers.get_upload_batch(request.user, batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError("Batch does not exist")

        return self.create_api_response(
            {"candidates": upload.get_candidates_with_errors(batch.contentadcandidate_set.all())}
        )

    def post(self, request, batch_id, candidate_id=None):
        if candidate_id:
            raise utils.exc.ValidationError("Not supported")
        batch = helpers.get_upload_batch(request.user, batch_id)
        candidate = upload.add_candidate(batch)

        return self.create_api_response({"candidate": candidate.to_dict()})  # don't add errors for new candidate

    def delete(self, request, batch_id, candidate_id):
        batch = helpers.get_upload_batch(request.user, batch_id)
        try:
            candidate = batch.contentadcandidate_set.get(id=candidate_id)
        except models.ContentAdCandidate.DoesNotExist:
            raise utils.exc.MissingDataError("Candidate does not exist")

        upload.delete_candidate(candidate)
        return self.create_api_response({})
