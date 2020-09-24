import json

from django.db import transaction

import core.models.content_ad.exceptions
import core.models.content_ad_candidate.exceptions
import utils.exc
import zemauth.access
from dash import constants
from dash import forms
from dash import models
from dash.common.views_base import DASHAPIBaseView
from zemauth.features.entity_permission import Permission

from . import exc
from . import upload


def _get_account_ad_group(user, form):
    account = zemauth.access.get_account(user, Permission.WRITE, form.cleaned_data["account_id"])
    ad_group = None
    if form.cleaned_data["ad_group_id"]:
        ad_group = zemauth.access.get_ad_group(user, Permission.WRITE, form.cleaned_data["ad_group_id"])
    return account, ad_group


class UploadBatch(DASHAPIBaseView):
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

        can_use_icon = ad_group.campaign.type != constants.CampaignType.DISPLAY
        return self.create_api_response(
            {
                "batch_id": batch.id,
                "batch_name": batch.name,
                "candidates": [candidate.to_dict(can_use_icon) for candidate in candidates],
            }
        )


class UploadCsv(DASHAPIBaseView):
    def post(self, request):
        form = forms.AdGroupAdsUploadForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            raise utils.exc.ValidationError(errors=form.errors)

        account, ad_group = _get_account_ad_group(request.user, form)

        batch_name = form.cleaned_data["batch_name"]
        candidates_data = form.cleaned_data["candidates"]
        filename = request.FILES["candidates"].name

        try:
            batch, candidates = upload.insert_candidates(
                request.user, account, candidates_data, ad_group, batch_name, filename
            )
        except core.models.content_ad_candidate.exceptions.AdGroupIsArchived as err:
            raise utils.exc.ValidationError(message=str(err))
        candidates_result = upload.get_candidates_with_errors(request, candidates)
        return self.create_api_response(
            {"batch_id": batch.id, "batch_name": batch.name, "candidates": candidates_result}
        )


class UploadStatus(DASHAPIBaseView):
    def get(self, request, batch_id):
        batch = zemauth.access.get_upload_batch(request.user, Permission.READ, batch_id)

        candidates = batch.contentadcandidate_set.all()
        candidate_ids = request.GET.get("candidates")

        if candidate_ids:
            candidate_ids = candidate_ids.strip().split(",")
            candidates = candidates.filter(id__in=candidate_ids)

        candidates_result = {
            candidate["id"]: candidate for candidate in upload.get_candidates_with_errors(request, candidates)
        }
        return self.create_api_response({"candidates": candidates_result})


class UploadSave(DASHAPIBaseView):
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
            except (
                exc.InvalidBatchStatus,
                exc.CandidateErrorsRemaining,
                core.models.content_ad.exceptions.CampaignAdTypeMismatch,
                core.models.content_ad.exceptions.AdGroupIsArchived,
            ) as err:
                raise utils.exc.ValidationError(message=str(err))

        return content_ads

    def _execute_update(self, request, batch):
        try:
            return upload.persist_edit_batch(request, batch)
        except (
            exc.InvalidBatchStatus,
            exc.CandidateErrorsRemaining,
            core.models.content_ad.exceptions.CampaignAdTypeMismatch,
        ) as e:
            raise utils.exc.ValidationError(message=str(e))

    def post(self, request, batch_id):
        batch = zemauth.access.get_upload_batch(request.user, Permission.WRITE, batch_id)

        if batch.type != constants.UploadBatchType.EDIT:
            content_ads = self._execute_save(request, batch)
        else:
            content_ads = self._execute_update(request, batch)

        return self.create_api_response({"num_successful": len(content_ads)})


class UploadCancel(DASHAPIBaseView):
    def post(self, request, batch_id):
        batch = zemauth.access.get_upload_batch(request.user, Permission.WRITE, batch_id)

        try:
            upload.cancel_upload(batch)
        except exc.InvalidBatchStatus:
            raise utils.exc.ValidationError(errors={"cancel": "Cancel action unsupported at this stage"})

        return self.create_api_response({})


class CandidatesDownload(DASHAPIBaseView):
    def get(self, request, batch_id):
        batch = zemauth.access.get_upload_batch(request.user, Permission.READ, batch_id)

        batch_name = batch.name
        if "batch_name" in request.GET:
            batch_name = request.GET["batch_name"]

        content = upload.get_candidates_csv(request, batch)
        return self.create_csv_response(batch_name, content=content)


class CandidateUpdate(DASHAPIBaseView):
    def post(self, request, batch_id, candidate_id):
        batch = zemauth.access.get_upload_batch(request.user, Permission.WRITE, batch_id)
        resource = json.loads(request.POST["data"])

        try:
            updated_fields, errors = upload.update_candidate(
                resource["candidate"], resource["defaults"], batch, request.FILES
            )
        except models.ContentAdCandidate.DoesNotExist:
            raise utils.exc.MissingDataError("Candidate does not exist")

        return self.create_api_response({"updated_fields": updated_fields, "errors": errors})


class Candidate(DASHAPIBaseView):
    def get(self, request, batch_id, candidate_id=None):
        if candidate_id:
            raise utils.exc.ValidationError("Not supported")

        try:
            batch = zemauth.access.get_upload_batch(request.user, Permission.READ, batch_id)
        except models.UploadBatch.DoesNotExist:
            raise utils.exc.MissingDataError("Batch does not exist")

        return self.create_api_response(
            {"candidates": upload.get_candidates_with_errors(request, batch.contentadcandidate_set.all())}
        )

    def post(self, request, batch_id, candidate_id=None):
        if candidate_id:
            raise utils.exc.ValidationError("Not supported")
        batch = zemauth.access.get_upload_batch(request.user, Permission.WRITE, batch_id)
        candidate = upload.add_candidate(batch)

        return self.create_api_response({"candidate": candidate.to_dict()})  # don't add errors for new candidate

    def delete(self, request, batch_id, candidate_id):
        batch = zemauth.access.get_upload_batch(request.user, Permission.WRITE, batch_id)
        try:
            candidate = batch.contentadcandidate_set.get(id=candidate_id)
        except models.ContentAdCandidate.DoesNotExist:
            raise utils.exc.MissingDataError("Candidate does not exist")

        upload.delete_candidate(candidate)
        return self.create_api_response({})
