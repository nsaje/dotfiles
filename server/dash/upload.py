import logging
import StringIO

from django.db import transaction
from django.conf import settings
import unicodecsv

from dash import constants
from dash import forms
from dash import models
from utils import lambda_helper, k1_helper, redirector_helper

logger = logging.getLogger(__name__)

VALID_DEFAULTS_FIELDS = set(['image_crop', 'description', 'display_url', 'brand_name', 'call_to_action'])


class InvalidBatchStatus(Exception):
    pass


class CandidateErrorsRemaining(Exception):
    pass


@transaction.atomic
def insert_candidates(candidates_data, ad_group, batch_name, filename):
    batch = create_empty_batch(ad_group.id, batch_name, original_filename=filename)
    candidates = _create_candidates(candidates_data, ad_group, batch)
    return batch, candidates


def create_empty_batch(ad_group_id, batch_name, original_filename=None):
    return models.UploadBatch.objects.create(
        name=batch_name,
        ad_group_id=ad_group_id,
        original_filename=original_filename,
    )


def _reset_candidate_async_status(candidate):
    candidate.url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    candidate.image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
    candidate.image_id = None
    candidate.image_hash = None
    candidate.image_width = None
    candidate.image_height = None
    candidate.save()


@transaction.atomic
def invoke_external_validation(candidate, batch):
    _reset_candidate_async_status(candidate)

    cleaned_urls = _get_cleaned_urls(candidate)
    skip_url_validation = has_skip_validation_magic_word(batch.original_filename)
    lambda_helper.invoke_lambda(
        settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME,
        {
            'namespace': settings.LAMBDA_CONTENT_UPLOAD_NAMESPACE,
            'candidateID': candidate.pk,
            'pageUrl': cleaned_urls['url'],
            'adGroupID': candidate.ad_group.pk,
            'batchID': candidate.batch.pk,
            'imageUrl': cleaned_urls['image_url'],
            'callbackUrl': settings.LAMBDA_CONTENT_UPLOAD_CALLBACK_URL,
            'skipUrlValidation': skip_url_validation,
        },
        async=True,
    )


def has_skip_validation_magic_word(filename):
    return 'no-verify' in (filename or '')


def persist_candidates(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise InvalidBatchStatus('Invalid batch status')

    candidates = models.ContentAdCandidate.objects.filter(batch=batch)
    cleaned_candidates, errors = _clean_candidates(candidates)
    if errors:
        raise CandidateErrorsRemaining('Save not permitted - candidate errors exist')

    with transaction.atomic():
        content_ads = _persist_content_ads(batch, cleaned_candidates)
        batch.status = constants.UploadBatchStatus.DONE
        batch.save()
        candidates.delete()

    k1_helper.update_content_ads(
        batch.ad_group_id, [ad.pk for ad in batch.contentad_set.all()],
        msg='upload.process_async'
    )
    return content_ads


def create_redirect_ids(content_ads):
    redirector_batch = redirector_helper.insert_redirects_batch(content_ads)
    for content_ad in content_ads:
        content_ad.url = redirector_batch[str(content_ad.id)]["redirect"]["url"]
        content_ad.redirect_id = redirector_batch[str(content_ad.id)]["redirectid"]
        content_ad.save()


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


def _get_csv(fields, rows):
    string = StringIO.StringIO()
    writer = unicodecsv.DictWriter(string, [_transform_field(field) for field in fields])
    writer.writeheader()
    for row in rows:
        writer.writerow({_transform_field(k): v for k, v in row.items() if k in fields})
    return string.getvalue()


def _get_candidates_csv(candidates):
    fields = list(forms.ALL_CSV_FIELDS)
    rows = []
    for candidate in sorted(candidates, key=lambda x: x.id):
        rows.append({k: v for k, v in candidate.to_dict().items() if k in fields})
    return _get_csv(fields, rows)


def _transform_field(field):
    if field in forms.CSV_EXPORT_COLUMN_NAMES_DICT:
        return forms.CSV_EXPORT_COLUMN_NAMES_DICT[field]
    return field.replace('_', ' ').capitalize()


@transaction.atomic
def cancel_upload(batch):
    if batch.status != constants.UploadBatchStatus.IN_PROGRESS:
        raise InvalidBatchStatus('Invalid batch status')

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


def _update_candidate(data, batch):
    candidate = batch.contentadcandidate_set.get(id=data['id'])
    form = forms.ContentAdCandidateForm(data)
    form.is_valid()  # used only to clean data of any possible unsupported fields

    errors = {}
    for field in data:
        if field not in form.cleaned_data:
            continue

        if field in form.errors:
            errors[field] = form.errors[field]
        setattr(candidate, field, form.cleaned_data[field])

    if candidate.has_changed('url') or candidate.has_changed('image_url'):
        invoke_external_validation(candidate, batch)

    candidate.save()
    return errors


def _get_partial_errors(data):
    form = forms.ContentAdForm(data)
    if form.is_valid():
        return {}

    errors = {}
    for field in data.keys():
        if field not in form.errors:
            continue
        errors[field] = form.errors[field]
    return errors


@transaction.atomic
def update_candidate(data, defaults, batch):
    _update_defaults(data, defaults, batch)
    _update_candidate(data, batch)
    return _get_partial_errors(data)


@transaction.atomic
def add_candidate(batch):
    return batch.contentadcandidate_set.create(ad_group_id=batch.ad_group_id)


def _get_cleaned_urls(candidate):
    form = forms.ContentAdForm(candidate.to_dict())
    form.is_valid()  # it doesn't matter if the form as a whole is valid or not
    return {
        'url': form.cleaned_data.get('url'),
        'image_url': form.cleaned_data.get('image_url'),
    }


@transaction.atomic
def process_callback(callback_data):
    try:
        candidate_id = callback_data.get('id')
        candidate = models.ContentAdCandidate.objects.get(pk=candidate_id)
    except models.ContentAdCandidate.DoesNotExist:
        logger.exception('No candidate with id %s', callback_data['id'])
        return

    cleaned_urls = _get_cleaned_urls(candidate)
    if 'originUrl' in callback_data['image'] and callback_data['image']['originUrl'] != cleaned_urls['image_url'] or\
       'originUrl' in callback_data['url'] and callback_data['url']['originUrl'] != cleaned_urls['url']:
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
        form = forms.ContentAdCandidateForm(content_ad)
        form.is_valid()  # used only to clean data of any possible unsupported fields
        candidates_added.append(
            models.ContentAdCandidate.objects.create(
                ad_group=ad_group,
                batch=batch,
                **form.cleaned_data
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

    _create_content_ad_sources(content_ad, ad_group_sources)
    return content_ad


def _create_content_ad_sources(content_ad, ad_group_sources):
    for ad_group_source in ad_group_sources:
            models.ContentAdSource.objects.create(
                source=ad_group_source.source,
                content_ad=content_ad,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.ACTIVE
            )
