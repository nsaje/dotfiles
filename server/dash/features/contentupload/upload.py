import logging

from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import pluralize

from dash import constants
from dash import forms
from dash import image_helper
from dash import models
from server import celery
from utils import k1_helper
from utils import lambda_helper
from utils import redirector_helper
from utils import csv_utils

import exc
import upload_dev

logger = logging.getLogger(__name__)

VALID_DEFAULTS_FIELDS = set(['image_crop', 'description', 'display_url', 'brand_name', 'call_to_action'])
VALID_UPDATE_FIELDS = set(['url', 'brand_name', 'display_url', 'description', 'image_crop', 'label',
                           'primary_tracker_url', 'secondary_tracker_url', 'call_to_action'])


def insert_candidates(user, account, candidates_data, ad_group, batch_name, filename, auto_save=False, is_edit=False):
    with transaction.atomic():
        batch = models.UploadBatch.objects.create_for_file(
            user, account, batch_name, ad_group, filename, auto_save, is_edit)
        candidates = _create_candidates(candidates_data, ad_group, batch)

    for candidate in candidates:
        _invoke_external_validation(candidate, batch)

    return batch, candidates


def insert_edit_candidates(user, content_ads, ad_group):
    content_ads_data = []
    for content_ad in content_ads:
        content_ad_dict = content_ad.to_candidate_dict()
        content_ad_dict['original_content_ad'] = content_ad
        content_ads_data.append(content_ad_dict)

    return insert_candidates(user, ad_group.campaign.account, content_ads_data, ad_group, '', '', is_edit=True)


def _reset_candidate_async_status(candidate):
    if candidate.url:
        candidate.url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE

    if candidate.image_url:
        candidate.image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidate.image_id = None
        candidate.image_hash = None
        candidate.image_width = None
        candidate.image_height = None

    candidate.save()


@transaction.atomic
def _invoke_external_validation(candidate, batch):
    _reset_candidate_async_status(candidate)

    if settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME == 'mock':
        upload_dev.MockAsyncValidation(candidate, _handle_auto_save).start()
        return

    cleaned_urls = _get_cleaned_urls(candidate)
    skip_url_validation = has_skip_validation_magic_word(batch.original_filename)
    if batch.ad_group and batch.ad_group.campaign.account_id == 305:  # OEN
        skip_url_validation = True
    data = {
        'namespace': settings.LAMBDA_CONTENT_UPLOAD_NAMESPACE,
        'candidateID': candidate.pk,
        'pageUrl': cleaned_urls['url'],
        'adGroupID': candidate.ad_group_id,
        'batchID': candidate.batch.pk,
        'imageUrl': cleaned_urls['image_url'],
        'callbackUrl': settings.LAMBDA_CONTENT_UPLOAD_CALLBACK_URL,
        'skipUrlValidation': skip_url_validation,
    }
    if settings.USE_CELERY_FOR_UPLOAD_LAMBDAS:
        _invoke_lambda_celery.delay(data)
    else:
        _invoke_lambda_async(data)


def _invoke_lambda_async(data):
    lambda_helper.invoke_lambda(
        settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME,
        data,
        async=True,
    )


@celery.app.task(
    acks_late=True,
    name='upload_lambda_execute',
    time_limit=300,
    max_retries=5,
    default_retry_delay=20)
def _invoke_lambda_celery(data):
    data['raiseException'] = True
    lambda_helper.invoke_lambda(
        settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME,
        data,
        async=False,
    )


def has_skip_validation_magic_word(filename):
    return 'no-verify' in (filename or '')


def persist_batch(batch):
    if not batch.ad_group_id:
        raise exc.ChangeForbidden('Batch has no ad group specified')

    cleaned_candidates = clean_candidates(batch)

    with transaction.atomic():
        content_ads = models.ContentAd.objects.bulk_create_from_candidates(cleaned_candidates, batch)

        batch.mark_save_done()
        batch.contentadcandidate_set.all().delete()

        _save_history(batch, content_ads)

    k1_helper.update_content_ads(
        batch.ad_group_id, [ad.pk for ad in batch.contentad_set.all()],
        msg='upload.process_async.insert'
    )
    return content_ads


def clean_candidates(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise exc.InvalidBatchStatus('Invalid batch status')

    if batch.type == constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden('Batch in edit mode')

    candidates = batch.contentadcandidate_set.all().order_by('pk')
    if any(candidate.original_content_ad_id for candidate in candidates):
        raise exc.ChangeForbidden('Some candidates are linked to content ads')

    cleaned_candidates, errors = _clean_candidates(candidates)
    if errors:
        raise exc.CandidateErrorsRemaining('Save not permitted - candidate errors exist')

    return cleaned_candidates


def persist_edit_batch(request, batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise exc.InvalidBatchStatus('Invalid batch status')

    if batch.type != constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden('Batch not in edit mode')

    candidates = models.ContentAdCandidate.objects.filter(batch=batch)
    with transaction.atomic():
        content_ads = _update_content_ads(candidates)
        redirector_helper.update_redirects(content_ads)

        candidates.delete()
        batch.delete()

        _save_history(batch, content_ads)

    k1_helper.update_content_ads(
        batch.ad_group_id, [ad.pk for ad in content_ads],
        msg='upload.process_async.edit'
    )
    return content_ads


def _save_history(batch, content_ads):
    if batch.type == constants.UploadBatchType.EDIT:
        changes_text = 'Edited {} content ad{}.'.format(
            len(content_ads),
            pluralize(len(content_ads)),
        )
        action_type = constants.HistoryActionType.CONTENT_AD_EDIT
    else:
        changes_text = 'Imported batch "{}" with {} content ad{}.'.format(
            batch.name,
            len(content_ads),
            pluralize(len(content_ads)),
        )
        action_type = constants.HistoryActionType.CONTENT_AD_CREATE
    batch.ad_group.write_history(
        changes_text,
        user=batch.created_by,
        action_type=action_type)


def get_candidates_with_errors(candidates):
    _, errors = _clean_candidates(candidates)
    result = []
    for candidate in candidates:
        candidate_dict = candidate.to_dict()
        candidate_dict['errors'] = {}
        if candidate.id in errors:
            candidate_dict['errors'] = errors[candidate.id]
        result.append(candidate_dict)
    return result


def get_candidates_csv(batch):
    candidates = batch.contentadcandidate_set.all()
    return _get_candidates_csv(candidates)


def _update_content_ads(update_candidates):
    updated_content_ads = []
    for candidate in update_candidates:
        updated_content_ads.append(_apply_content_ad_edit(candidate))

    return updated_content_ads


def _get_candidates_csv(candidates):
    fields = [_transform_field(field) for field in forms.ALL_CSV_FIELDS]
    rows = _get_candidates_csv_rows(candidates)
    return csv_utils.dictlist_to_csv(
        fields,
        rows,
    )


def _get_candidates_csv_rows(candidates):
    rows = []
    for candidate in sorted(candidates, key=lambda x: x.id):
        rows.append({
            _transform_field(k): v for k, v in candidate.to_dict().items()
            if k in forms.ALL_CSV_FIELDS
        })
    return rows


def _transform_field(field):
    if field in forms.CSV_EXPORT_COLUMN_NAMES_DICT:
        return forms.CSV_EXPORT_COLUMN_NAMES_DICT[field]
    return field.replace('_', ' ').capitalize()


@transaction.atomic
def cancel_upload(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise exc.InvalidBatchStatus('Invalid batch status')

    batch.status = constants.UploadBatchStatus.CANCELLED
    batch.save()

    batch.contentadcandidate_set.all().delete()


def _clean_candidates(candidates):
    cleaned_candidates = []
    errors = {}
    for candidate in candidates:
        f = forms.ContentAdForm(candidate.to_dict())
        if not f.is_valid():
            errors[candidate.id] = f.errors
        cleaned_candidates.append(f.cleaned_data)
    return cleaned_candidates, errors


def _update_defaults(data, defaults, batch):
    defaults = set(defaults) & VALID_DEFAULTS_FIELDS
    if not defaults:
        return

    batch.contentadcandidate_set.all().update(**{
        field: data[field] for field in defaults
    })

    for field in defaults:
        setattr(batch, 'default_' + field, data[field])
    batch.save()


def _update_candidate(data, batch, files):
    candidate = batch.contentadcandidate_set.get(id=data.pop('id'))

    form = forms.ContentAdCandidateForm(data, files)
    form.is_valid()  # used only to clean data of any possible unsupported fields

    updated_fields = {}
    for field in data:
        if batch.type == constants.UploadBatchType.EDIT and field not in VALID_UPDATE_FIELDS:
            raise exc.ChangeForbidden('Update not permitted - field is not editable')

        if field == 'image' or field not in form.cleaned_data:
            continue

        updated_fields[field] = form.cleaned_data[field]
        setattr(candidate, field, form.cleaned_data[field])

    if form.cleaned_data.get('image'):
        image_url = image_helper.upload_image_to_s3(form.cleaned_data['image'], batch.id)
        candidate.image_url = image_url
        updated_fields['image_url'] = image_url
    elif form.errors.get('image'):
        candidate.image_url = None
        updated_fields['image_url'] = None

    if candidate.has_changed('url') or candidate.has_changed('image_url'):
        _invoke_external_validation(candidate, batch)

    candidate.save()
    return updated_fields


def _get_field_errors(data, files):
    errors = {}
    form = forms.ContentAdForm(data, files=files)
    if form.is_valid():
        return errors

    fields = set(data.keys())
    if files:
        fields |= set(files.keys())

    for field in fields:
        if field not in form.errors:
            continue
        errors[field] = form.errors[field]
    return errors


@transaction.atomic
def update_candidate(data, defaults, batch, files=None):
    _update_defaults(data, defaults, batch)
    updated_fields = _update_candidate(data, batch, files)
    errors = _get_field_errors(data, files)
    return updated_fields, errors


@transaction.atomic
def add_candidate(batch):
    if batch.type == constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden('Cannot add candidate - batch in edit mode')

    return batch.contentadcandidate_set.create(
        ad_group_id=batch.ad_group_id,
        image_crop=batch.default_image_crop,
        display_url=batch.default_display_url,
        brand_name=batch.default_brand_name,
        description=batch.default_description,
        call_to_action=batch.default_call_to_action,
    )


def delete_candidate(candidate):
    if candidate.batch.type == constants.UploadBatchType.EDIT:
        raise exc.ChangeForbidden('Cannot delete candidate - batch in edit mode')

    candidate.delete()


def _get_cleaned_urls(candidate):
    form = forms.ContentAdForm(candidate.to_dict())
    form.is_valid()  # it doesn't matter if the form as a whole is valid or not
    return {
        'url': form.cleaned_data.get('url'),
        'image_url': form.cleaned_data.get('image_url'),
    }


def _process_image_url_update(candidate, image_url, callback_data):
    if 'originUrl' not in callback_data['image'] or callback_data['image']['originUrl'] != image_url:
        # prevent issues with concurrent jobs
        return

    if candidate.image_status == constants.AsyncUploadJobStatus.PENDING_START:
        # image url hasn't been set yet
        return

    candidate.image_status = constants.AsyncUploadJobStatus.FAILED
    try:
        if callback_data['image']['valid']:
            candidate.image_id = callback_data['image']['id']
            candidate.image_width = callback_data['image']['width']
            candidate.image_height = callback_data['image']['height']
            candidate.image_hash = callback_data['image']['hash']
            candidate.image_status = constants.AsyncUploadJobStatus.OK
    except KeyError:
        logger.exception('Failed to parse callback data %s', str(callback_data))


def _process_url_update(candidate, url, callback_data):
    if 'originUrl' not in callback_data['url'] or callback_data['url']['originUrl'] != url:
        # prevent issues with concurrent jobs
        return

    if candidate.url_status == constants.AsyncUploadJobStatus.PENDING_START:
        # url hasn't been set yet
        return

    candidate.url_status = constants.AsyncUploadJobStatus.FAILED
    try:
        if callback_data['url']['valid']:
            candidate.url_status = constants.AsyncUploadJobStatus.OK
    except KeyError:
        logger.exception('Failed to parse callback data %s', str(callback_data))


def _handle_auto_save(batch):
    if not batch.auto_save:
        return

    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        return

    should_fail = False
    _, errors = _clean_candidates(batch.contentadcandidate_set.all())
    for error_dict in errors.values():
        keys = set(error_dict.keys())
        keys.discard('__all__')
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
        if all(candidate.image_status == constants.AsyncUploadJobStatus.OK and
               candidate.url_status == constants.AsyncUploadJobStatus.OK
               for candidate in batch.contentadcandidate_set.all()):
            logger.exception('Couldn\'t auto save batch for unknown reason')


def process_callback(callback_data):
    with transaction.atomic():
        try:
            candidate_id = callback_data.get('id')
            candidate = models.ContentAdCandidate.objects.filter(pk=candidate_id).select_related('batch').get()
        except models.ContentAdCandidate.DoesNotExist:
            logger.info('No candidate with id %s', callback_data['id'])
            return

        cleaned_urls = _get_cleaned_urls(candidate)
        _process_url_update(candidate, cleaned_urls['url'], callback_data)
        _process_image_url_update(candidate, cleaned_urls['image_url'], callback_data)

        candidate.save()


def handle_auto_save_batches(created_after):
    batches = models.UploadBatch.objects.filter(
        status=constants.UploadBatchStatus.IN_PROGRESS,
        created_dt__gte=created_after,
    )

    for batch in batches:
        _handle_auto_save(batch)


def _create_candidates(content_ads_data, ad_group, batch):
    candidates_added = []
    for content_ad in content_ads_data:
        form = forms.ContentAdCandidateForm(content_ad)
        form.is_valid()  # used only to clean data of any possible unsupported fields

        fields = {k: v for k, v in form.cleaned_data.items() if k != 'image'}
        if 'original_content_ad' in content_ad:
            fields['original_content_ad'] = content_ad['original_content_ad']

        candidates_added.append(
            models.ContentAdCandidate.objects.create(
                ad_group=ad_group,
                batch=batch,
                **fields
            )
        )
    return candidates_added


def _apply_content_ad_edit(candidate):
    content_ad = candidate.original_content_ad
    if not content_ad:
        raise exc.ChangeForbidden('Update not permitted - original content ad not set')

    f = forms.ContentAdForm(candidate.to_dict())
    if not f.is_valid():
        raise exc.CandidateErrorsRemaining('Save not permitted - candidate errors exist')

    for field in VALID_UPDATE_FIELDS:
        setattr(content_ad, field, f.cleaned_data[field])

    content_ad.tracker_urls = []

    primary_tracker_url = f.cleaned_data['primary_tracker_url']
    if primary_tracker_url:
        content_ad.tracker_urls.append(primary_tracker_url)

    secondary_tracker_url = f.cleaned_data['secondary_tracker_url']
    if secondary_tracker_url:
        content_ad.tracker_urls.append(secondary_tracker_url)

    content_ad.save()
    return content_ad
