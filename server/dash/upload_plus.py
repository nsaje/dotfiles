import logging
import StringIO

from django.db import transaction
from django.conf import settings
import unicodecsv

from dash import constants
from dash import forms
from dash import models
from utils import s3helpers, lambda_helper, k1_helper

logger = logging.getLogger(__name__)

S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT = 'contentads/errors/{batch_id}/{filename}'

MAPPED_ERROR_CSV_FIELD = {
    'tracker_urls': 'impression_trackers',
}


class InvalidBatchStatus(Exception):
    pass


@transaction.atomic
def insert_candidates(content_ads_data, ad_group, batch_name, filename):
    batch = models.UploadBatch.objects.create(
        name=batch_name,
        ad_group=ad_group,
        batch_size=len(content_ads_data),
        original_filename=filename,
    )
    candidates = _create_candidates(content_ads_data, ad_group, batch)
    return batch, candidates


@transaction.atomic
def invoke_external_validation(candidate, skip_url_validation=False):
    lambda_helper.invoke_lambda(
        settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME,
        {
            'namespace': settings.LAMBDA_CONTENT_UPLOAD_NAMESPACE,
            'candidateID': candidate.pk,
            'pageUrl': candidate.url,
            'adGroupID': candidate.ad_group.pk,
            'batchID': candidate.batch.pk,
            'imageUrl': candidate.image_url,
            'callbackUrl': settings.LAMBDA_CONTENT_UPLOAD_CALLBACK_URL,
            'skipUrlValidation': skip_url_validation,
        },
        async=True,
    )
    candidate.image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    candidate.url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    candidate.save()


def has_skip_validation_magic_word(filename):
    return 'no-verify' in (filename or '')


def persist_candidates(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise InvalidBatchStatus('Invalid batch status')

    with transaction.atomic():
        new_content_ads, errors = _prepare_candidates(batch)
        content_ads = _persist_content_ads(batch, new_content_ads)
        _update_batch_status(batch, errors)

    k1_helper.update_content_ads(
        batch.ad_group_id, [ad.pk for ad in batch.contentad_set.all()],
        msg='upload.process_async'
    )
    return content_ads


def _prepare_candidates(batch):
    candidates = models.ContentAdCandidate.objects.filter(
        batch=batch,
    )

    new_content_ads = []
    errors = []
    for candidate in candidates:
        f = forms.ContentAdForm(candidate.to_dict())
        if not f.is_valid():
            # f.errors is a dict of lists of messages
            errors.append({
                'candidate': candidate,
                'errors': ', '.join([', '.join(inner) for inner in f.errors.values()])
            })
            continue
        new_content_ads.append(f.cleaned_data)

    candidates.delete()
    return new_content_ads, errors


def _persist_content_ads(batch, new_content_ads):
    ad_group_sources = []
    for ags in models.AdGroupSource.objects.filter(
            ad_group=batch.ad_group,
    ).select_related('source__source_type'):
        if ags.can_manage_content_ads and ags.source.can_manage_content_ads():
            ad_group_sources.append(ags)

    saved_content_ads = []
    for content_ad in new_content_ads:
        saved_content_ads.append(_create_content_ad(content_ad, batch.ad_group_id, batch.id, ad_group_sources))

    return saved_content_ads


def _update_batch_status(batch, errors):
    if errors:
        batch.error_report_key = _save_error_report(batch.id, batch.original_filename, errors)

    batch.status = constants.UploadBatchStatus.DONE
    batch.num_errors = len(errors)
    batch.save()


def _save_error_report(batch_id, filename, errors):
    string = StringIO.StringIO()

    fields = [field for field in forms.MANDATORY_CSV_FIELDS]
    fields += [field for field in forms.OPTIONAL_CSV_FIELDS]
    fields.remove('crop_areas')  # a hack to ease transition

    fields.append('errors')
    writer = unicodecsv.DictWriter(string, [_transform_field(field) for field in fields])

    writer.writeheader()
    for error_dict in errors:
        row = {_transform_field(k): v for k, v in error_dict['candidate'].to_dict().items() if k in fields}
        row['Errors'] = error_dict['errors']
        writer.writerow(row)

    content = string.getvalue()
    return _upload_error_report_to_s3(batch_id, content, filename)


def _transform_field(field):
    field = _get_mapped_field(field)
    return field.replace('_', ' ').title()


def _get_mapped_field(field):
    if field not in MAPPED_ERROR_CSV_FIELD:
        return field
    return MAPPED_ERROR_CSV_FIELD[field]


def _upload_error_report_to_s3(batch_id, content, filename):
    key = S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT.format(
        batch_id=batch_id,
        filename=s3helpers.generate_safe_filename(filename, content),
    )
    try:
        s3helpers.S3Helper().put(key, content)
        return key
    except Exception:
        logger.exception('Error while saving upload error report')

    return None


@transaction.atomic
def cancel_upload(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise InvalidBatchStatus('Invalid batch status')

    batch.status = constants.UploadBatchStatus.CANCELLED
    batch.save()

    batch.contentadcandidate_set.all().delete()


def validate_candidates(candidates):
    errors = {}
    for candidate in candidates:
        f = forms.ContentAdForm(candidate.to_dict())
        if not f.is_valid():
            errors[candidate.id] = f.errors
    return errors


@transaction.atomic
def process_callback(callback_data):
    try:
        candidate_id = callback_data.get('id')
        candidate = models.ContentAdCandidate.objects.get(pk=candidate_id)
    except models.ContentAdCandidate.DoesNotExist:
        logger.exception('No candidate with id %s', callback_data['id'])
        return

    candidate.image_status = constants.AsyncUploadJobStatus.FAILED
    candidate.url_status = constants.AsyncUploadJobStatus.FAILED
    try:
        if callback_data['image']['valid']:
            candidate.image_id = callback_data['image']['id']
            candidate.image_width = callback_data['image']['width']
            candidate.image_height = callback_data['image']['height']
            candidate.image_hash = callback_data['image']['hash']
            candidate.image_status = constants.AsyncUploadJobStatus.OK
        if callback_data['url']['valid']:
            candidate.url_status = constants.AsyncUploadJobStatus.OK
    except KeyError:
        logger.exception('Failed to parse callback data %s', str(callback_data))

    candidate.save()


def _create_candidates(content_ads_data, ad_group, batch):
    candidates_added = []
    for content_ad in content_ads_data:
        candidates_added.append(
            models.ContentAdCandidate.objects.create(
                ad_group=ad_group,
                batch=batch,
                label=content_ad.get('label', ''),
                url=content_ad.get('url', ''),
                title=content_ad.get('title', ''),
                image_url=content_ad.get('image_url', ''),
                image_crop=content_ad.get('image_crop', constants.ImageCrop.CENTER),
                display_url=content_ad.get('display_url', ''),
                brand_name=content_ad.get('brand_name', ''),
                description=content_ad.get('description', ''),
                call_to_action=content_ad.get('call_to_action', ''),
                tracker_urls=content_ad.get('tracker_urls', ''),
                primary_tracker_url=content_ad.get('primary_tracker_url', ''),
                secondary_tracker_url=content_ad.get('secondary_tracker_url', ''),
            )
        )
    return candidates_added


def _create_content_ad(candidate, ad_group_id, batch_id, ad_group_sources):
    content_ad = models.ContentAd.objects.create(
        ad_group_id=ad_group_id,
        batch_id=batch_id,
        image_id=candidate['image_id'],
        image_width=candidate['image_width'],
        image_height=candidate['image_height'],
        image_hash=candidate['image_hash'],
        image_crop=candidate['image_crop'],
        label=candidate['label'],
        url=candidate['url'],
        title=candidate['title'],
        display_url=candidate['display_url'],
        brand_name=candidate['brand_name'],
        description=candidate['description'],
        call_to_action=candidate['call_to_action'],
        tracker_urls=candidate['tracker_urls'],
    )

    content_ad_sources = []
    for ad_group_source in ad_group_sources:
        content_ad_sources.append(
            models.ContentAdSource.objects.create(
                source=ad_group_source.source,
                content_ad=content_ad,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.ACTIVE
            )
        )

    return content_ad
