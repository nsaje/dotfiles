import time
import uuid
from dataclasses import dataclass

import celery.result
import celery.states
import django.core.exceptions
from django.core.cache import caches
from django.db import transaction

import core.models
import zemauth.models
from dash import constants
from dash.features import contentupload
from server import celery as z1_celery
from utils import exc
from utils import zlogging

logger = zlogging.getLogger(__name__)
cache = caches["cluster_level_cache"]
CACHE_TIMEOUT = 60 * 60 * 24 * 7
ALIVE_TIMEOUT = 60 * 2


@dataclass
class UploadResult:
    status: str


@dataclass
class Request:
    user: zemauth.models.User


def upload_adgroups(user, ad_groups_dicts):
    task_id = uuid.uuid4()
    _cache_set(task_id, "exists", True)
    _cache_set(task_id, "ad_groups_dicts", ad_groups_dicts)
    logger.info("Triggering async", task_id=task_id, ad_groups_dicts=ad_groups_dicts)
    return upload_adgroups_async.apply_async((user,), task_id=task_id)


@z1_celery.app.task(bind=True, acks_late=True, name="bulkupload_adgroups")
def upload_adgroups_async(self, user):
    """
    Uploads ad groups in bulk.

    First uploads adgroups in a transaction, then batches in a transaction.
    Is idempotently retriable and can pick up where it left off due to saving intermediate data in cache.
    """

    task_id = self.request.id or ""

    if self.backend.get_state(task_id) in celery.states.READY_STATES:
        raise celery.exceptions.Ignore("Already finished")

    already_alive = _cache_get(task_id, "alive")
    if already_alive:
        raise celery.exceptions.Reject("Still being processed by another worker", requeue=False)

    ad_groups_dicts = _cache_get(task_id, "ad_groups_dicts")
    if not ad_groups_dicts:
        logger.error("No data in cache!", task_id=task_id)
        raise Exception("No data in cache")
    request = Request(user)

    logger.info("Processing bulk upload task", task_id=task_id)

    exception = _cache_get(task_id, "exception")
    if exception:
        logger.info("Raising cached exception", task_id=task_id)
        raise exception

    ad_group_ids = _cache_get(task_id, "adgroupids") or []
    if not ad_group_ids:
        with transaction.atomic():
            logger.info("Creating ad groups", task_id=task_id)
            ad_group_ids = _upload_adgroups(task_id, request, ad_groups_dicts)
            logger.info("Ad groups created", task_id=task_id, ad_group_ids=ad_group_ids)
            _cache_set(task_id, "adgroupids", ad_group_ids)

    ad_groups_by_id = {ag.id: ag for ag in core.models.AdGroup.objects.filter(pk__in=ad_group_ids)}
    ad_groups = [ad_groups_by_id[id_] for id_ in ad_group_ids]

    batch_ids = _cache_get(task_id, "batchids") or []
    if not batch_ids:
        with transaction.atomic():
            logger.info("Creating batches", task_id=task_id)
            batch_ids = _upload_batches(task_id, request, ad_groups, ad_groups_dicts)
            logger.info("Batches created", task_id=task_id, batch_ids=batch_ids)
            _cache_set(task_id, "batchids", batch_ids)

    validation_triggered = _cache_get(task_id, "validation_triggered") or False
    if not validation_triggered:
        _invoke_external_validation(task_id, batch_ids)
        _cache_set(task_id, "validation_triggered", True)
    logger.info("External validation triggered", task_id=task_id)

    _wait_for_batch_validation(task_id, batch_ids)
    logger.info("External validation complete", task_id=task_id)

    batches_by_id = {b.id: b for b in core.models.UploadBatch.objects.filter(pk__in=batch_ids)}
    batches = [batches_by_id[id_] for id_ in batch_ids]

    _ensure_batches_valid(task_id, request, batches)

    logger.info("Task finished", task_id=task_id)
    return ad_groups, batches


def _upload_adgroups(task_id, request, ad_groups_dicts):
    ad_group_ids = []
    errors = [{}] * len(ad_groups_dicts)
    has_errors = False
    for i, ad_group_dict in enumerate(ad_groups_dicts):
        _mark_alive(task_id)
        try:
            campaign = core.models.Campaign.objects.get(pk=ad_group_dict["ad_group"]["campaign_id"])
            ad_group_obj = core.models.AdGroup.objects.create(
                request,
                campaign=campaign,
                name=ad_group_dict.get("ad_group_name", None),
                bidding_type=ad_group_dict.get("ad_group", {}).get("bidding_type"),
                is_restapi=True,
                initial_settings=ad_group_dict,
                sources=ad_group_dict.get("sources"),
            )
            ad_group_ids.append(ad_group_obj.id)
        except exc.ValidationError as e:
            errors[i] = str(e)
            has_errors = True
        if has_errors:
            e = exc.ValidationError("Error uploading one or more ad groups", errors=errors)
            _cache_set(task_id, "exception", e)
            logger.info("Raising validation exception", task_id=task_id)
            raise e
    return ad_group_ids


def _upload_batches(task_id, request, ad_groups, ad_groups_dicts):
    batch_ids = []
    errors = [{}] * len(ad_groups_dicts)
    has_errors = False
    for i, (ad_group, ad_group_dict) in enumerate(zip(ad_groups, ad_groups_dicts)):
        _mark_alive(task_id)
        candidates_data = ad_group_dict["ads"]

        try:
            batch, _ = contentupload.upload.insert_candidates(
                request.user if request else None,
                ad_group.campaign.account,
                candidates_data,
                ad_group,
                "Bulk Upload",
                None,
                auto_save=True,
                do_invoke_external_validation=False,
            )
            batch_ids.append(batch.id)
        except exc.ValidationError as e:
            errors[i] = {"ads": str(e)}
            has_errors = True

        if has_errors:
            e = exc.ValidationError("Error uploading one or more ad batches", errors=errors)
            _cache_set(task_id, "exception", e)
            logger.info("Raising ad validation exception", task_id=task_id)
            raise e
    return batch_ids


def _invoke_external_validation(task_id, batch_ids):
    candidates = core.models.ContentAdCandidate.objects.filter(batch_id__in=batch_ids).select_related("batch")
    for candidate in candidates:
        _mark_alive(task_id)
        contentupload.upload.invoke_external_validation(candidate, candidate.batch)


def _wait_for_batch_validation(task_id, batch_ids):
    batches_qs = core.models.UploadBatch.objects.filter(pk__in=batch_ids)
    while any(batch.status == constants.UploadBatchStatus.IN_PROGRESS for batch in batches_qs.all()):
        _mark_alive(task_id)
        time.sleep(5.0)


def _ensure_batches_valid(task_id, request, batches):
    errors = [{}] * len(batches)
    has_errors = False
    for i, batch in enumerate(batches):
        if batch.status != constants.UploadBatchStatus.DONE:
            errors[i] = {
                "ads": [
                    candidate["errors"]
                    for candidate in contentupload.upload.get_candidates_with_errors(
                        request, batch.contentadcandidate_set.all()
                    )
                ]
            }
            has_errors = True

    if has_errors:
        e = exc.ValidationError("Error uploading one or more ad batches", errors=errors)
        _cache_set(task_id, "exception", e)
        logger.info("Raising ad batch validation exception", task_id=task_id)
        raise e


def _mark_alive(task_id):
    logger.info("Task alive", task_id=task_id)
    _cache_set(task_id, "alive", True, timeout=ALIVE_TIMEOUT)


def _cache_get(task_id, kind):
    return cache.get(_get_cache_key(task_id, kind))


def _cache_set(task_id, kind, value, timeout=None):
    return cache.set(_get_cache_key(task_id, kind), value, timeout=(timeout or CACHE_TIMEOUT))


def _get_cache_key(task_id, kind):
    return f"{task_id}_{kind}"


def get_upload_promise(task_id):
    exists = _cache_get(task_id, "exists")
    if not exists:
        raise django.core.exceptions.ObjectDoesNotExist()
    return celery.result.AsyncResult(id=task_id)
