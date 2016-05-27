import logging
import StringIO

from django.db import transaction
from django.forms.models import model_to_dict
from django.conf import settings
import unicodecsv

from dash import constants
from dash import forms
from dash import models
from utils import s3helpers, lambda_helper

logger = logging.getLogger(__name__)

S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT = 'contentads/errors/{batch_id}/{filename}'


@transaction.atomic
def insert_candidates(content_ads_data, ad_group, batch_name, filename):
    batch = models.UploadBatch.objects.create(
        name=batch_name,
        account=ad_group.campaign.account,
        batch_size=len(content_ads_data),
        original_filename=filename,
    )
    candidates = _create_candidates(content_ads_data, ad_group, batch)
    return batch, candidates


@transaction.atomic
def invoke_external_validation(candidate):
    lambda_helper.invoke_lambda(
        settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME,
        {
            'namespace': settings.LAMBDA_CONTENT_UPLOAD_NAMESPACE,
            'candidateID': candidate.pk,
            'pageUrl': candidate.url,
            'adGroupID': candidate.ad_group.pk,
            'batchID': candidate.batch.pk,
            'imageUrl': candidate.image_url,
        }
    )
    candidate.image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    candidate.url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    candidate.save()


@transaction.atomic
def persist_candidates(ad_group, batch):
    candidates = models.ContentAdCandidate.objects.filter(
        batch_id=batch,
    )
    ad_group_sources = []
    for s in models.AdGroupSource.objects.filter(
            ad_group_id=ad_group.id,
    ).select_related('source__source_type'):
        if s.can_manage_content_ads and s.source.can_manage_content_ads():
            ad_group_sources.append(s)

    errors = {}
    for candidate in candidates:
        f = forms.ContentAdForm(model_to_dict(candidate))
        if f.is_valid():
            _create_content_ad(f.cleaned_data, ad_group.id, batch.id, ad_group_sources)
            continue

        # f.errors is a dict of lists
        errors[candidate] = ', '.join([', '.join(inner) for inner in f.errors.values()])

    error_report_key = None
    if errors:
        error_report_key = _save_error_report(batch.id, batch.original_filename, errors)
        batch.error_report_key = error_report_key

    batch.status = constants.UploadBatchStatus.DONE
    batch.num_errors = len(errors)
    batch.save()

    candidates.delete()
    return batch.error_report_key, batch.num_errors


@transaction.atomic
def cancel_upload(ad_group, batch):
    batch.status = constants.UploadBatchStatus.CANCELLED
    batch.save()

    batch.contentadcandidate_set.all().delete()


def validate_candidates(candidates):
    errors = {}
    for candidate in candidates:
        f = forms.ContentAdCandidateForm(model_to_dict(candidate))
        if not f.is_valid():
            errors[candidate.id] = f.errors
    return errors


def _save_error_report(batch_id, filename, error_dict):
    string = StringIO.StringIO()

    fields = list(forms.MANDATORY_CSV_FIELDS) + list(forms.OPTIONAL_CSV_FIELDS)
    fields.remove('crop_areas')  # a hack to ease transition

    fields.append('errors')
    writer = unicodecsv.DictWriter(string, fields)

    writer.writeheader()
    for candidate, errors in error_dict.iteritems():
        row = {k: v for k, v in model_to_dict(candidate).items() if k in fields}
        row['errors'] = errors
        writer.writerow(row)

    content = string.getvalue()
    return _upload_error_report_to_s3(batch_id, content, filename)


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
                image_crop=content_ad.get('image_crop', 'faces'),
                display_url=content_ad.get('display_url', ''),
                brand_name=content_ad.get('brand_name', ''),
                description=content_ad.get('description', ''),
                call_to_action=content_ad.get('call_to_action', ''),
                tracker_urls=content_ad.get('trakcer_urls', ''),
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
        if callback_data['image']['id']:
            candidate.image_status = constants.AsyncUploadJobStatus.OK
        if callback_data['url']['valid']:
            candidate.url_status = constants.AsyncUploadJobStatus.OK
        candidate.image_id = callback_data['image']['id']
        candidate.image_width = callback_data['image']['width']
        candidate.image_height = callback_data['image']['height']
        candidate.image_hash = callback_data['image']['hash']
    except:
        logger.exception('Failed to parse callback data %s', str(callback_data))

    candidate.save()
