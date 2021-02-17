import concurrent.futures
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import pluralize

import core.features.videoassets
import dash.features.contentupload
from dash import constants
from dash import forms
from dash import image_helper
from dash import models
from server import celery
from utils import csv_utils
from utils import k1_helper
from utils import lambda_helper
from utils import sspd_client
from utils import zlogging

from . import exc
from . import upload_dev

logger = zlogging.getLogger(__name__)

DISPLAY_AD_TYPES = [constants.AdType.IMAGE, constants.AdType.AD_TAG]
VALID_DEFAULTS_FIELDS = set(["image_crop", "description", "display_url", "brand_name", "call_to_action", "ad_tag"])
VALID_UPDATE_FIELDS = set(
    [
        "url",
        "brand_name",
        "display_url",
        "description",
        "image_crop",
        "label",
        "primary_tracker_url",
        "secondary_tracker_url",
        "call_to_action",
        "ad_tag",
        "trackers",
    ]
)
MAX_TRACKERS = 3
MAX_TRACKERS_EXTRA = 6


def insert_candidates(
    user,
    account,
    candidates_data,
    ad_group,
    batch_name,
    filename,
    auto_save=False,
    batch_type=constants.UploadBatchType.INSERT,
    state_override=None,
    do_invoke_external_validation=True,
):
    with transaction.atomic():
        batch = models.UploadBatch.objects.create_for_file(
            user,
            account,
            batch_name,
            ad_group,
            filename,
            auto_save,
            batch_type=batch_type,
            state_override=state_override,
        )
        candidates = _create_candidates(candidates_data, ad_group, batch)

    if do_invoke_external_validation:
        for candidate in candidates:
            invoke_external_validation(candidate, batch)

    return batch, candidates


def insert_edit_candidates(user, content_ads, ad_group):
    content_ads_data = []
    for content_ad in content_ads:
        content_ad_dict = content_ad.to_candidate_dict()
        content_ad_dict["original_content_ad"] = content_ad
        content_ads_data.append(content_ad_dict)

    return insert_candidates(
        user, ad_group.campaign.account, content_ads_data, ad_group, "", "", batch_type=constants.UploadBatchType.EDIT
    )


def insert_clone_edit_candidates(user, content_ads, ad_group, batch_name, state_override):
    content_ads_data = []
    for content_ad in content_ads:
        content_ad_dict = content_ad.to_cloned_candidate_dict()
        content_ad_dict["image_url"] = content_ad.get_base_image_url()
        content_ad_dict["icon_url"] = content_ad.get_base_icon_url()
        content_ad_dict["original_content_ad"] = content_ad
        content_ads_data.append(content_ad_dict)

    return insert_candidates(
        user,
        ad_group.campaign.account,
        content_ads_data,
        ad_group,
        batch_name,
        "",
        batch_type=constants.UploadBatchType.CLONE,
        state_override=state_override,
    )


def _reset_candidate_async_status(candidate):
    if candidate.url:
        candidate.url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    if candidate.primary_tracker_url:
        candidate.primary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    if candidate.secondary_tracker_url:
        candidate.secondary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    if candidate.trackers:
        trackers_status = {}
        for tracker in candidate.trackers:
            tracker_status_key = dash.features.contentupload.get_tracker_status_key(
                tracker.get("url"), tracker.get("method")
            )
            trackers_status[tracker_status_key] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
            if tracker.get("fallback_url"):
                fallback_tracker_status_key = dash.features.contentupload.get_tracker_status_key(
                    tracker.get("fallback_url"), constants.TrackerMethod.IMG
                )
                trackers_status[fallback_tracker_status_key] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidate.trackers_status = trackers_status
    if candidate.type != constants.AdType.AD_TAG and candidate.image_url:
        candidate.image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidate.image_id = None
        candidate.image_hash = None
        candidate.image_width = None
        candidate.image_height = None
        candidate.image_file_size = None
    if candidate.type not in DISPLAY_AD_TYPES and candidate.icon_url:
        candidate.icon_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidate.icon_id = None
        candidate.icon_hash = None
        candidate.icon_width = None
        candidate.icon_height = None
        candidate.icon_file_size = None

    candidate.save()


@transaction.atomic
def invoke_external_validation(candidate, batch):
    _reset_candidate_async_status(candidate)

    if settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME == "mock":
        upload_dev.MockAsyncValidation(candidate, _handle_auto_save).start()
        return

    cleaned_urls = _get_cleaned_urls(candidate)
    skip_url_validation = has_skip_validation_magic_word(batch.original_filename)
    if batch.ad_group and batch.ad_group.campaign.account_id == settings.HARDCODED_ACCOUNT_ID_OEN:
        skip_url_validation = True
    data = {
        "namespace": settings.LAMBDA_CONTENT_UPLOAD_NAMESPACE,
        "candidateID": candidate.pk,
        "pageUrl": cleaned_urls["url"],
        "adGroupID": candidate.ad_group_id,
        "imageUrls": [],
        "callbackUrl": settings.LAMBDA_CONTENT_UPLOAD_CALLBACK_URL,
        "skipUrlValidation": skip_url_validation,
        "normalize": candidate.type not in DISPLAY_AD_TYPES,
        "impressionTrackers": [it for it in [candidate.primary_tracker_url, candidate.secondary_tracker_url] if it],
        "trackers": candidate.trackers or [],
    }

    if cleaned_urls["image_url"]:
        data["imageUrls"].append(cleaned_urls["image_url"])

    if cleaned_urls["icon_url"]:
        data["imageUrls"].append(cleaned_urls["icon_url"])

    if settings.USE_CELERY_FOR_UPLOAD_LAMBDAS:
        _invoke_lambda_celery.delay(data)
    else:
        _invoke_lambda_async(data)


def _invoke_lambda_async(data):
    lambda_helper.invoke_lambda(settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME, data, do_async=True)


@celery.app.task(
    acks_late=True,
    name="upload_lambda_execute",
    time_limit=300,
    max_retries=5,
    default_retry_delay=20,
    ignore_result=True,
)
def _invoke_lambda_celery(data):
    data["raiseException"] = True
    lambda_helper.invoke_lambda(settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME, data, do_async=False)


def has_skip_validation_magic_word(filename):
    return "no-verify" in (filename or "")


def persist_batch(batch):
    if not batch.ad_group_id:
        raise exc.ChangeForbidden("Batch has no ad group specified")

    cleaned_candidates = clean_candidates(batch)

    with transaction.atomic():
        content_ads = models.ContentAd.objects.bulk_create_from_candidates(cleaned_candidates, batch)

        batch.mark_save_done()
        batch.contentadcandidate_set.all().delete()

        _save_history(batch, content_ads)

    sspd_client.sync_batch(batch)

    msg = "upload.process_async.insert"
    if batch.type == constants.UploadBatchType.CLONE:
        msg += ", clonecontent.clone_edit"

    k1_helper.update_content_ads(batch.contentad_set.all().select_related("ad_group__campaign"), msg=msg)
    return content_ads


def clean_candidates(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise exc.InvalidBatchStatus("Invalid batch status")

    if batch.type == constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden("Batch in edit mode")

    candidates = batch.contentadcandidate_set.all().order_by("pk")

    cleaned_candidates, errors = get_clean_candidates_and_errors(candidates)
    if errors:
        raise exc.CandidateErrorsRemaining("Save not permitted - candidate errors exist")

    return cleaned_candidates


def persist_edit_batch(request, batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise exc.InvalidBatchStatus("Invalid batch status")

    if batch.type != constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden("Batch not in edit mode")

    candidates = models.ContentAdCandidate.objects.filter(batch=batch)
    with transaction.atomic():
        content_ads = _update_content_ads(request, candidates)

        candidates.delete()
        batch.delete()

        _save_history(batch, content_ads)

    sspd_client.sync_batch(batch)

    k1_helper.update_content_ads(content_ads, msg="upload.process_async.edit")
    return content_ads


def _save_history(batch, content_ads):
    if batch.type == constants.UploadBatchType.EDIT:
        changes_text = "Edited {} content ad{}.".format(len(content_ads), pluralize(len(content_ads)))
        action_type = constants.HistoryActionType.CONTENT_AD_EDIT
    elif batch.type == constants.UploadBatchType.CLONE:
        changes_text = 'Imported batch "{}" with {} cloned and edited content ad{}.'.format(
            batch.name, len(content_ads), pluralize(len(content_ads))
        )
        action_type = constants.HistoryActionType.CONTENT_AD_CREATE
    else:
        changes_text = 'Imported batch "{}" with {} content ad{}.'.format(
            batch.name, len(content_ads), pluralize(len(content_ads))
        )
        action_type = constants.HistoryActionType.CONTENT_AD_CREATE
    batch.ad_group.write_history(changes_text, user=batch.created_by, action_type=action_type)


def get_candidates_with_errors(request, candidates):
    _, errors = get_clean_candidates_and_errors(candidates)

    result = []
    for candidate in candidates:
        can_use_icon = candidate.type not in DISPLAY_AD_TYPES
        candidate_dict = candidate.to_dict(can_use_icon)

        candidate_dict["errors"] = {}
        if candidate.id in errors:
            candidate_dict["errors"] = errors[candidate.id]

        result.append(candidate_dict)
    return result


def get_candidates_csv(request, batch):
    candidates = batch.contentadcandidate_set.all()
    return _get_candidates_csv(request, batch.ad_group, candidates)


def _update_content_ads(request, update_candidates):
    updated_content_ads = []
    for candidate in update_candidates:
        updated_content_ads.append(_apply_content_ad_edit(request, candidate))

    return updated_content_ads


def _get_candidates_csv(request, ad_group, candidates):
    fields = [_transform_field(field) for field in forms.ALL_CSV_FIELDS]
    rows = _get_candidates_csv_rows(candidates)
    fields, rows = _remove_ad_type_specific_fields_and_rows(ad_group, fields, rows)
    fields, rows = _remove_permissioned_fields_and_rows(request, fields, rows)
    return csv_utils.dictlist_to_csv(fields, rows)


def _remove_ad_type_specific_fields_and_rows(ad_group, fields, rows):
    if ad_group.campaign.type != constants.CampaignType.DISPLAY:
        fields, rows = _remove_specific_fields_and_rows(forms.DISPLAY_SPECIFIC_FIELDS, fields, rows)
    else:
        fields, rows = _remove_specific_fields_and_rows(forms.NATIVE_SPECIFIC_FIELDS, fields, rows)
    return fields, rows


def _remove_specific_fields_and_rows(specific_fields, fields, rows):
    for field in specific_fields:
        fields, rows = _remove_fields_and_rows(field, fields, rows)
    return fields, rows


def _remove_permissioned_fields_and_rows(request, fields, rows):
    if not request or not request.user:
        return fields, rows

    for field, permissions in forms.FIELD_PERMISSION_MAPPING.items():
        if not all(request.user.has_perm(p) for p in permissions):
            field_name = _transform_field(field)
            fields.remove(field_name)
            for row in rows:
                row.pop(field_name, None)

    return fields, rows


def _remove_fields_and_rows(original_field, fields, rows):
    field = _transform_field(original_field)
    field in fields and fields.remove(field)
    for row in rows:
        row.pop(field, None)
    return fields, rows


def _get_candidates_csv_rows(candidates):
    rows = []
    for candidate in sorted(candidates, key=lambda x: x.id):
        row = {_transform_field(k): v for k, v in list(candidate.to_dict().items()) if k in forms.ALL_CSV_FIELDS}
        row = _remap_separate_to_joint_fields(candidate, row)
        row = _map_trackers(candidate, row)
        rows.append(row)
    return rows


def _remap_separate_to_joint_fields(candidate, row):
    for joint_field, joint_params in forms.JOINT_CSV_FIELDS.items():
        attr1 = getattr(candidate, joint_params[1], None)
        attr2 = getattr(candidate, joint_params[2], None)
        if attr1 and attr2:
            row[_transform_field(joint_field)] = joint_params[0].join((str(attr1), str(attr2)))
    return row


def _transform_field(field):
    if field in forms.CSV_EXPORT_COLUMN_NAMES_DICT:
        return forms.CSV_EXPORT_COLUMN_NAMES_DICT[field]
    return field.replace("_", " ").capitalize()


def _map_trackers(candidate, row):
    if candidate.trackers:
        csv_trackers = dash.features.contentupload.map_trackers_to_csv(candidate.trackers)
        for field, value in csv_trackers.items():
            row[_transform_field(field)] = value

    return row


@transaction.atomic
def cancel_upload(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise exc.InvalidBatchStatus("Invalid batch status")

    batch.status = constants.UploadBatchStatus.CANCELLED
    batch.save()

    batch.contentadcandidate_set.all().delete()


def get_clean_candidates_and_errors(candidates):
    cleaned_candidates = []
    errors = defaultdict(dict)
    campaign = candidates[0].ad_group.campaign if (candidates and candidates[0].ad_group) else None

    for candidate in candidates:
        form = _get_candidate_form(candidate)
        f = form(campaign, candidate.to_dict(), original_content_ad=candidate.original_content_ad)
        if not f.is_valid():
            errors[candidate.id] = f.errors

        if f.cleaned_data.get("video_asset_id"):
            try:
                core.features.videoassets.service.update_asset_for_vast_upload(
                    candidate.ad_group.campaign.account, f.cleaned_data["video_asset_id"]
                )
            except core.features.videoassets.service.ParseVastError as err:
                errors[candidate.id]["video_asset_id"] = [str(err)]

        cleaned_candidates.append(f.cleaned_data)
    return cleaned_candidates, errors


def _get_candidate_form(candidate):
    if candidate.type == constants.AdType.IMAGE:
        return forms.ImageAdForm
    if candidate.type == constants.AdType.AD_TAG:
        return forms.AdTagForm

    return forms.ContentAdForm


def _update_defaults(data, defaults, batch):
    defaults = set(defaults) & VALID_DEFAULTS_FIELDS
    if not defaults:
        return

    batch.contentadcandidate_set.all().update(**{field: data[field] for field in defaults})

    for field in defaults:
        setattr(batch, "default_" + field, data[field])
    batch.save()


def _update_candidate(data, batch, files):
    candidate = batch.contentadcandidate_set.get(id=data.pop("id"))
    campaign = candidate.ad_group.campaign if candidate.ad_group else None

    if "primary_tracker_url" in data and "secondary_tracker_url" not in data:
        data["secondary_tracker_url"] = candidate.secondary_tracker_url
    elif "secondary_tracker_url" in data and "primary_tracker_url" not in data:
        data["primary_tracker_url"] = candidate.primary_tracker_url

    form = forms.ContentAdCandidateForm(campaign, data, files)
    form.is_valid()  # used only to clean data of any possible unsupported fields

    updated_fields = {}
    for field in data:
        if batch.type == constants.UploadBatchType.EDIT and field not in VALID_UPDATE_FIELDS:
            raise exc.ChangeForbidden("Update not permitted - field is not editable")

        if field in ["image", "icon"] or field not in form.cleaned_data:
            continue

        updated_fields[field] = form.cleaned_data[field]
        setattr(candidate, field, form.cleaned_data[field])

    if "primary_tracker_url" in data or "secondary_tracker_url" in data:
        setattr(candidate, "trackers", form.cleaned_data["trackers"])

    if form.cleaned_data.get("image"):
        image_url = image_helper.upload_image_to_s3(form.cleaned_data["image"], batch.id)
        candidate.image_url = image_url
        updated_fields["image_url"] = image_url
    elif form.errors.get("image"):
        candidate.image_url = None
        updated_fields["image_url"] = None

    if form.cleaned_data.get("icon"):
        icon_url = image_helper.upload_image_to_s3(form.cleaned_data["icon"], batch.id)
        candidate.icon_url = icon_url
        updated_fields["icon_url"] = icon_url
    elif form.errors.get("icon"):
        candidate.icon_url = None
        updated_fields["icon_url"] = None

    if (
        candidate.has_changed("url")
        or candidate.has_changed("image_url")
        or candidate.has_changed("icon_url")
        or candidate.has_changed("primary_tracker_url")
        or candidate.has_changed("secondary_tracker_url")
        or candidate.has_changed("trackers")
    ):
        invoke_external_validation(candidate, batch)

    candidate.save()
    return updated_fields, candidate


def _get_field_errors(candidate, data, files):
    errors = {}
    campaign = candidate.ad_group.campaign if candidate.ad_group else None
    form = _get_candidate_form(candidate)
    f = form(campaign, data, files=files)
    if f.is_valid():
        return errors

    fields = set(data.keys())
    if files:
        fields |= set(files.keys())

    for field in fields:
        if field not in f.errors:
            continue
        errors[field] = f.errors[field]
    return errors


@transaction.atomic
def update_candidate(data, defaults, batch, files=None):
    _update_defaults(data, defaults, batch)
    updated_fields, candidate = _update_candidate(data, batch, files)
    errors = _get_field_errors(candidate, data, files)
    return updated_fields, errors


@transaction.atomic
def add_candidate(batch):
    if batch.type == constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden("Cannot add candidate - batch in edit mode")

    campaign_type = batch.ad_group.campaign.type if batch.ad_group else None

    return batch.contentadcandidate_set.create(
        ad_group=batch.ad_group,
        image_crop=batch.default_image_crop,
        display_url=batch.default_display_url,
        brand_name=batch.default_brand_name,
        description=batch.default_description,
        call_to_action=batch.default_call_to_action,
        type={
            constants.CampaignType.VIDEO: constants.AdType.VIDEO,
            constants.CampaignType.DISPLAY: constants.AdType.IMAGE,
        }.get(campaign_type, constants.AdType.CONTENT),
    )


def delete_candidate(candidate):
    if candidate.batch.type == constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden("Cannot delete candidate - batch in edit mode")

    candidate.delete()


def _get_cleaned_urls(candidate):
    campaign = candidate.ad_group.campaign if candidate.ad_group else None
    form = _get_candidate_form(candidate)
    f = form(campaign, candidate.to_dict())
    f.is_valid()  # it doesn't matter if the form as a whole is valid or not
    return {
        "url": f.cleaned_data.get("url"),
        "image_url": f.cleaned_data.get("image_url"),
        "icon_url": f.cleaned_data.get("icon_url"),
        "primary_tracker_url": f.cleaned_data.get("primary_tracker_url"),
        "secondary_tracker_url": f.cleaned_data.get("secondary_tracker_url"),
    }


def _process_image_url_update(candidate, image_url, callback_data):
    if candidate.type == constants.AdType.AD_TAG or image_url not in callback_data.get("images", {}):
        return

    if candidate.image_status == constants.AsyncUploadJobStatus.PENDING_START:
        # image url hasn't been set yet
        return

    candidate.image_status = constants.AsyncUploadJobStatus.FAILED
    image_data = callback_data["images"][image_url]
    try:
        if candidate.type != constants.AdType.AD_TAG and image_data["valid"]:
            candidate.image_id = image_data["id"]
            candidate.image_width = image_data["width"]
            candidate.image_height = image_data["height"]
            candidate.image_hash = image_data["hash"]
            candidate.image_file_size = image_data["file_size"]
            candidate.image_status = constants.AsyncUploadJobStatus.OK
    except KeyError:
        logger.exception("Failed to parse callback data", data=str(callback_data))


def _process_icon_url_update(candidate, icon_url, callback_data):
    if candidate.type in DISPLAY_AD_TYPES or icon_url not in callback_data.get("images", {}):
        return

    if candidate.icon_status == constants.AsyncUploadJobStatus.PENDING_START:
        # icon url hasn't been set yet
        return

    candidate.icon_status = constants.AsyncUploadJobStatus.FAILED
    icon_data = callback_data["images"][icon_url]
    try:
        if candidate.type not in DISPLAY_AD_TYPES and icon_data["valid"]:
            candidate.icon_id = icon_data["id"]
            candidate.icon_width = icon_data["width"]
            candidate.icon_height = icon_data["height"]
            candidate.icon_hash = icon_data["hash"]
            candidate.icon_file_size = icon_data["file_size"]
            candidate.icon_status = constants.AsyncUploadJobStatus.OK
    except KeyError:
        logger.exception("Failed to parse callback data", data=str(callback_data))


def _process_url_update(candidate, url, callback_data):
    if "originUrl" not in callback_data["url"] or callback_data["url"]["originUrl"] != url:
        # prevent issues with concurrent jobs
        return
    if candidate.url_status == constants.AsyncUploadJobStatus.PENDING_START:
        # url hasn't been set yet
        return

    candidate.url_status = (
        constants.AsyncUploadJobStatus.OK if callback_data["url"]["valid"] else constants.AsyncUploadJobStatus.FAILED
    )


def _process_trackers_url(candidate, tracker_attr, tracker_data):
    tracker_url_attr = getattr(candidate, tracker_attr)
    if not tracker_url_attr:
        return
    status_attr = tracker_attr + "_status"
    if getattr(candidate, status_attr) == constants.AsyncUploadJobStatus.PENDING_START:
        # Url hasn't been set yet
        return
    new_status = constants.AsyncUploadJobStatus.OK if tracker_data["valid"] else constants.AsyncUploadJobStatus.FAILED
    setattr(candidate, status_attr, new_status)


def _process_impression_trackers_legacy(candidate, cleaned_urls, callback_data):

    if not callback_data["impressionTrackers"]:
        return

    for imp_tracker in callback_data["impressionTrackers"]:
        if imp_tracker["originUrl"] == cleaned_urls["primary_tracker_url"]:
            _process_trackers_url(candidate, "primary_tracker_url", imp_tracker)
        if imp_tracker["originUrl"] == cleaned_urls["secondary_tracker_url"]:
            _process_trackers_url(candidate, "secondary_tracker_url", imp_tracker)


def _process_trackers(candidate, callback_data):
    if not callback_data["trackers"]:
        return

    trackers_status = candidate.trackers_status
    if trackers_status:
        for tracker_data_callback in callback_data["trackers"]:
            tracker_status_key = dash.features.contentupload.get_tracker_status_key(
                tracker_data_callback.get("originUrl"), tracker_data_callback.get("method")
            )
            status = trackers_status.get(tracker_status_key)
            if status and status != constants.AsyncUploadJobStatus.PENDING_START:
                trackers_status[tracker_status_key] = (
                    constants.AsyncUploadJobStatus.OK
                    if tracker_data_callback["valid"]
                    else constants.AsyncUploadJobStatus.FAILED
                )

        candidate.trackers_status = trackers_status


def _handle_auto_save(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        return
    elif not batch.auto_save:
        return

    should_fail = False
    _, errors = get_clean_candidates_and_errors(batch.contentadcandidate_set.all())
    for error_dict in list(errors.values()):
        keys = set(error_dict.keys())
        keys.discard("__all__")
        if len(keys) > 0:
            should_fail = True
            break

    if should_fail:
        batch.status = constants.UploadBatchStatus.FAILED
        batch.save()
        return

    try:
        persist_batch(batch)
    except Exception:
        if all(
            candidate.image_status == constants.AsyncUploadJobStatus.OK
            and candidate.icon_status == constants.AsyncUploadJobStatus.OK
            and candidate.url_status == constants.AsyncUploadJobStatus.OK
            for candidate in batch.contentadcandidate_set.all()
        ):
            logger.exception("Couldn't auto save batch for unknown reason")


def process_callback(callback_data):
    with transaction.atomic():
        try:
            candidate_id = callback_data.get("id")
            candidate = models.ContentAdCandidate.objects.filter(pk=candidate_id).select_related("batch").get()
        except models.ContentAdCandidate.DoesNotExist:
            logger.info("No candidate with id", candidate_id=callback_data["id"])
            raise exc.CandidateDoesNotExist()

        logger.info("Processing callback for candidate", candidate_id=candidate.id, ad_group_id=candidate.ad_group_id)
        cleaned_urls = _get_cleaned_urls(candidate)
        _process_url_update(candidate, cleaned_urls["url"], callback_data)
        _process_image_url_update(candidate, cleaned_urls["image_url"], callback_data)
        _process_icon_url_update(candidate, cleaned_urls["icon_url"], callback_data)
        _process_impression_trackers_legacy(candidate, cleaned_urls, callback_data)
        _process_trackers(candidate, callback_data)
        candidate.save()

    # HACK(nsaje): mark all ads with same image as having image present, if not already
    _mark_ads_images_present(callback_data, cleaned_urls["image_url"])


def _mark_ads_images_present(callback_data, image_url):
    image_id = callback_data.get("images", {}).get(image_url, {}).get("id")
    if not image_id:
        return
    updated = models.ContentAd.objects.filter(image_present=False, image_id=image_id).update(image_present=True)
    if updated:
        logger.warning("Marked additional ads as having an image present after lambda upload!", updated=updated)


def handle_auto_save_batches(batches_qs):
    batches_qs = (
        batches_qs.filter(status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=True)
        .select_related("ad_group__campaign")
        .order_by("-pk")[:1000]
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(_handle_auto_save, batches_qs)


def clean_up_old_in_progress_batches(created_before):
    batches = models.UploadBatch.objects.filter(
        status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=True, created_dt__lte=created_before
    )

    return batches.update(status=constants.UploadBatchStatus.FAILED)


def _create_candidates(content_ads_data, ad_group, batch):
    candidates_added = []
    for content_ad in content_ads_data:
        form = forms.ContentAdCandidateForm(ad_group.campaign, content_ad)
        form.is_valid()  # used only to clean data of any possible unsupported fields

        fields = {k: v for k, v in list(form.cleaned_data.items()) if k not in ["image", "icon"]}
        if "original_content_ad" in content_ad:
            fields["original_content_ad"] = content_ad["original_content_ad"]

        candidates_added.append(models.ContentAdCandidate.objects.create(ad_group=ad_group, batch=batch, **fields))
    return candidates_added


def _apply_content_ad_edit(request, candidate):
    content_ad = candidate.original_content_ad
    if not content_ad:
        raise exc.ChangeForbidden("Update not permitted - original content ad not set")

    campaign = candidate.ad_group.campaign if candidate.ad_group else None
    form = _get_candidate_form(candidate)
    f = form(campaign, candidate.to_dict())
    if not f.is_valid():
        raise exc.CandidateErrorsRemaining("Save not permitted - candidate errors exist")

    tracker_urls = []
    primary_tracker_url = f.cleaned_data["primary_tracker_url"]
    if primary_tracker_url:
        tracker_urls.append(primary_tracker_url)
    secondary_tracker_url = f.cleaned_data["secondary_tracker_url"]
    if secondary_tracker_url:
        tracker_urls.append(secondary_tracker_url)

    updates = {k: v for k, v in list(f.cleaned_data.items()) if k in VALID_UPDATE_FIELDS}
    if tracker_urls != content_ad.tracker_urls:
        updates["tracker_urls"] = tracker_urls

    content_ad.update(request, write_history=False, **updates)

    return content_ad
