import json
import logging
import unicodecsv
import StringIO

from functools import partial
from multiprocessing.pool import ThreadPool

from django.db import transaction
from django.forms import ValidationError
from django.core import validators
from django.db.models import F

import actionlog.zwei_actions

from utils import redirector_helper
from utils import s3helpers
from utils import email_helper

from dash import models
from dash import api
from dash import constants
from dash import image_helper
from dash import threads
from dash.forms import AdGroupAdsPlusUploadForm, MANDATORY_CSV_FIELDS, OPTIONAL_CSV_FIELDS  # to get fields & validators

logger = logging.getLogger(__name__)

NUM_THREADS = 20
MAX_CSV_TITLE_LENGTH = 256
URL_VALIDATOR_NUM_RETRIES = 3
S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT = 'contentads/errors/{filename}'


class UploadFailedException(Exception):
    pass


def process_async(content_ads_data, filename, batch, upload_form_cleaned_fields, ad_group, request):
    ad_group_sources = [s for s in models.AdGroupSource.objects.filter(ad_group_id=ad_group.id)
                        if s.can_manage_content_ads and s.source.can_manage_content_ads()]

    pool = ThreadPool(processes=NUM_THREADS)
    pool.map_async(
        partial(_clean_row, batch, upload_form_cleaned_fields, ad_group),
        content_ads_data,
        callback=partial(_process_callback, batch, ad_group, ad_group_sources, filename, request),
    )


def _process_callback(batch, ad_group, ad_group_sources, filename, request, results):
    try:
        # ensure content ads are only commited to DB
        # if all of them are successfully processed
        count_inserted = 0
        with transaction.atomic():
            rows = []
            all_content_ad_sources = []
            num_errors = 0

            logger.info('Inserting uploaded content ads for batch %s %s', batch.pk, batch.name)
            for row, cleaned_data, errors in results:
                if not errors:
                    content_ad, content_ad_sources = _create_objects(
                        cleaned_data, batch, ad_group.id, ad_group_sources)

                    errors = _create_redirect_id(content_ad)

                    if not errors:
                        all_content_ad_sources.extend(content_ad_sources)

                if errors:
                    row['errors'] = ', '.join(errors)
                    num_errors += len(errors)

                rows.append(row)

                # update progress in another thread to escape transaction
                count_inserted += 1
                t = threads.UpdateUploadBatchThread(batch.id, count_inserted)
                t.start_and_join()

            if num_errors > 0:
                # raise exception to rollback transaction
                raise UploadFailedException()

            logger.info('Submitting uploaded content ads for batch %s %s', batch.pk, batch.name)
            actions = api.submit_content_ads(all_content_ad_sources, request)

            batch.status = constants.UploadBatchStatus.DONE
            batch.save()

            _add_to_history(request, batch, ad_group)

    except UploadFailedException:
        batch.error_report_key = _save_error_report(rows, filename)
        batch.status = constants.UploadBatchStatus.FAILED
        batch.num_errors = num_errors
        batch.save()
        return
    except Exception as e:
        logger.exception('Exception in ProcessUploadThread: {0}'.format(e))
        batch.status = constants.UploadBatchStatus.FAILED
        batch.save()
        return

    logger.info('Sending uploaded content ads for batch %s %s', batch.pk, batch.name)
    actionlog.zwei_actions.send(actions)


def _save_error_report(rows, filename):
    string = StringIO.StringIO()

    fields = list(MANDATORY_CSV_FIELDS)

    for field_name in OPTIONAL_CSV_FIELDS:
        if any(row.get(field_name) for row in rows):
            fields.append(field_name)

    fields.append('errors')
    writer = unicodecsv.DictWriter(string, fields)

    writer.writeheader()
    for row in rows:
        for field_name in OPTIONAL_CSV_FIELDS:
            if field_name not in fields and field_name in row:
                del row[field_name]

        writer.writerow(row)

    content = string.getvalue()
    return _upload_error_report_to_s3(content, filename)


def _upload_error_report_to_s3(content, filename):
    key = S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT.format(
        filename=s3helpers.generate_safe_filename(filename, content)
    )
    try:
        s3helpers.S3Helper().put(key, content)
        return key
    except Exception:
        logger.exception('Error while saving upload error report')

    return None


def _create_redirect_id(content_ad):
    try:
        content_ad.redirect_id = redirector_helper.insert_redirect(
            content_ad.url,
            content_ad.pk,
            content_ad.ad_group_id,
        )
        content_ad.save()
        return []
    except Exception:
        logger.exception('Exception in create_redirect_id')
        return ['Internal server error while processing request']


def _create_objects(data, batch, ad_group_id, ad_group_sources):
    content_ad = models.ContentAd.objects.create(
        image_id=data['image']['id'],
        image_width=data['image']['width'],
        image_height=data['image']['height'],
        image_hash=data['image']['hash'],
        url=data['url'],
        title=data['title'],
        batch=batch,
        display_url=data['display_url'],
        brand_name=data['brand_name'],
        description=data['description'],
        call_to_action=data['call_to_action'],
        ad_group_id=ad_group_id,
        tracker_urls=data['tracker_urls']
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

    return content_ad, content_ad_sources


def _clean_row(batch, upload_form_cleaned_fields, ad_group, row):
    try:
        errors = []
        data = {}
        for key in ['title', 'url', 'image', 'tracker_urls', 'display_url', 'brand_name', 'description', 'call_to_action']:
            try:
                if key == 'title': 
                    data[key] = _clean_title(row.get('title'))
                elif key == 'url':
                    data[key] = _clean_url(row.get('url'), ad_group)
                elif key == 'image': 
                    data[key] = _clean_image(row.get('image_url'), row.get('crop_areas'))
                elif key == 'tracker_urls': 
                    data[key] = _clean_tracker_urls(row.get('tracker_urls'))
                elif key in ['description', 'display_url', 'brand_name', 'call_to_action']:
                    data[key] = _clean_inherited_csv_field(key, row.get(key), upload_form_cleaned_fields[key])
                else:
                    raise Exception("Unknown key: {0}".format(key))	# should never happen, guards against coding errors
            except ValidationError as e:
                errors.extend(e.messages)

        # atomically update counter
        batch.processed_content_ads = F('processed_content_ads') + 1
        batch.save()

        return row, data, errors
    except Exception as e:
        logger.exception('Exception in upload._clean_row')
        raise

# This function cleans the fields that are, when column is not present or the value is empty, inherited from form submission
def _clean_inherited_csv_field(field_name, value_from_csv, cleaned_value_from_form):
    field = AdGroupAdsPlusUploadForm.base_fields[field_name]

    if value_from_csv:
        return field.clean(value_from_csv)

    if cleaned_value_from_form:
        return cleaned_value_from_form

    # this currently can never happen as the form values are still mandatory
    raise ValidationError("{0} has to be present in CSV or default value should be submitted in the upload form.".format(field.label))


def _clean_url(url, ad_group):
    try:
        # URL is considered invalid if it contains any unicode chars
        url = url.encode('ascii')
        url = _validate_url(url)
    except (ValidationError, UnicodeEncodeError):
        raise ValidationError('Invalid URL')

    if not redirector_helper.validate_url(url, ad_group.id):
        raise ValidationError('Content unreachable')
    return url


def _clean_tracker_urls(tracker_urls_string):
    if tracker_urls_string is None:
        return None

    tracker_urls = tracker_urls_string.strip().split(' ')

    result = []
    validate_url = validators.URLValidator(schemes=['https'])

    for url in tracker_urls:
        try:
            # URL is considered invalid if it contains any unicode chars
            url = url.encode('ascii')
            validate_url(url)
        except (ValidationError, UnicodeEncodeError):
            raise ValidationError('Invalid tracker URLs')

        result.append(url)

    return result


def _clean_image(image_url, crop_areas):
    errors = []

    try:
        image_url = _validate_url(image_url)
    except ValidationError as e:
        errors.append('Invalid Image URL')

    try:
        crop_areas = _clean_crop_areas(crop_areas)
    except ValidationError as e:
        errors.append(e.message)

    if errors:
        raise ValidationError(errors)

    try:
        image_id, width, height, image_hash = image_helper.process_image(image_url, crop_areas)
    except image_helper.ImageProcessingException as e:
        error_status = e.status()

        if error_status == 'image-size-error':
            message = 'Image too big'
        elif error_status == 'download-error':
            message = 'Image could not be downloaded'
        else:
            message = 'Image could not be processed'

        raise ValidationError(message)

    return {
        'id': image_id,
        'width': width,
        'height': height,
        'hash': image_hash
    }


def _clean_title(title):
    if title is None or not len(title):
        raise ValidationError('Missing title')
    elif len(title) > MAX_CSV_TITLE_LENGTH:
        raise ValidationError('Title too long (max %d characters)' % MAX_CSV_TITLE_LENGTH)

    return title


def _clean_crop_areas(crop_string):
    if not crop_string:
        # crop areas are optional, so return None
        # if they are not provided
        return None

    crop_string = crop_string.replace('(', '[').replace(')', ']')

    try:
        crop_list = json.loads(crop_string)
        _validate_crops(crop_list)
    except (ValueError, IndexError):
        raise ValidationError('Invalid crop areas')

    return crop_list


def _validate_url(url):
    validate_url = validators.URLValidator(schemes=['http', 'https'])

    try:
        validate_url(url)
        return url
    except ValidationError:
        pass

    url = 'http://{url}'.format(url=url)
    validate_url(url)

    return url


def _validate_crops(crop_list):
    for i in range(2):
        for j in range(2):
            for k in range(2):
                if not isinstance(crop_list[i][j][k], (int, long)):
                    raise ValueError('Coordinate is not an integer')


def _add_to_history(request, batch, ad_group):
    changes_text = 'Imported batch "{}" with {} content ads.'.format(
        batch.name,
        batch.batch_size
    )
    settings = ad_group.get_current_settings().copy_settings()
    settings.changes_text = changes_text
    settings.save(request)
    email_helper.send_ad_group_notification_email(ad_group, request)
