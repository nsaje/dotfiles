import json
import logging
import unicodecsv
import StringIO
import urllib2
import httplib
from functools import partial
from multiprocessing.pool import ThreadPool

from django.db import transaction
from django.forms import ValidationError
from django.core import validators
from django.conf import settings
from django.db.models import F

import actionlog.zwei_actions

from utils import redirector_helper
from utils import s3helpers
from utils import url_helper
from utils import email_helper

from dash import models
from dash import api
from dash import constants
from dash import image_helper

logger = logging.getLogger(__name__)

NUM_THREADS = 20
MAX_CSV_TITLE_LENGTH = 256
URL_VALIDATOR_NUM_RETRIES = 3
S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT = 'contentads/errors/{filename}'


class UploadFailedException(Exception):
    pass


def process_async(content_ads_data, filename, batch, ad_group, request):
    ad_group_sources = [s for s in models.AdGroupSource.objects.filter(ad_group_id=ad_group.id)
                        if s.can_manage_content_ads and s.source.can_manage_content_ads()]

    pool = ThreadPool(processes=NUM_THREADS)
    pool.map_async(
        partial(_clean_row, batch, ad_group),
        content_ads_data,
        callback=partial(_process_callback, batch, ad_group.id, ad_group_sources, filename, request),
    )


def _process_callback(batch, ad_group_id, ad_group_sources, filename, request, results):
    try:
        # ensure content ads are only commited to DB
        # if all of them are successfully processed
        with transaction.atomic():
            rows = []
            all_content_ad_sources = []
            num_errors = 0

            for row, cleaned_data, errors in results:
                if not errors:
                    content_ad, content_ad_sources = _create_objects(
                        cleaned_data, batch, ad_group_id, ad_group_sources)

                    errors = _create_redirect_id(content_ad)

                    if not errors:
                        all_content_ad_sources.extend(content_ad_sources)

                if errors:
                    row['errors'] = ', '.join(errors)
                    num_errors += len(errors)

                rows.append(row)

            if num_errors > 0:
                # raise exception to rollback transaction
                raise UploadFailedException()

            actions = api.submit_content_ads(all_content_ad_sources, request)

            batch.status = constants.UploadBatchStatus.DONE
            batch.save()

            _add_to_history(request, batch, ad_group_sources)
            
    except UploadFailedException:
        batch.error_report_key = _save_error_report(rows, filename)
        batch.status = constants.UploadBatchStatus.FAILED
        batch.num_errors = num_errors
        batch.save()
        return
    except Exception:
        logger.exception('Exception in ProcessUploadThread')
        batch.status = constants.UploadBatchStatus.FAILED
        batch.save()
        return

    actionlog.zwei_actions.send(actions)


def _save_error_report(rows, filename):
    string = StringIO.StringIO()

    fields = ['url', 'title', 'image_url']

    if any(row.get('crop_areas') for row in rows):
        fields.append('crop_areas')

    if any(row.get('tracker_urls') for row in rows):
        fields.append('tracker_urls')

    fields.append('errors')
    writer = unicodecsv.DictWriter(string, fields)

    writer.writeheader()
    for row in rows:
        if 'crop_areas' not in fields and 'crop_areas' in row:
            del row['crop_areas']

        if 'tracker_urls' not in fields and 'tracker_urls' in row:
            del row['tracker_urls']

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


def _clean_row(batch, ad_group, row):
    try:
        title = row.get('title')
        url = row.get('url')
        image_url = row.get('image_url')
        crop_areas = row.get('crop_areas')
        tracker_urls_string = row.get('tracker_urls')

        cleaners = {
            'title': partial(_clean_title, title),
            'url': partial(_clean_url, url, ad_group),
            'image': partial(_clean_image, image_url, crop_areas),
            'tracker_urls': partial(_clean_tracker_urls, tracker_urls_string)
        }

        errors = []
        data = {}
        for key, cleaner in cleaners.items():
            try:
                data[key] = cleaner()
            except ValidationError as e:
                errors.extend(e.messages)

        # atomically update counter
        batch.processed_content_ads = F('processed_content_ads') + 1
        batch.save()

        return row, data, errors
    except Exception as e:
        logger.exception('Exception in upload._clean_row')
        raise


def _clean_url(url, ad_group):
    try:
        # URL is considered invalid if it contains any unicode chars
        url = url.encode('ascii')
        url = _validate_url(url)
    except (ValidationError, UnicodeEncodeError):
        raise ValidationError('Invalid URL')

    tracking_codes = ad_group.get_test_tracking_params()
    url_with_tracking_codes = url_helper.add_tracking_codes_to_url(url, tracking_codes)

    if not _is_content_reachable(url_with_tracking_codes):
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


def _is_content_reachable(url):
    request = urllib2.Request(url)
    request.add_header('User-Agent', settings.URL_VALIDATOR_USER_AGENT)

    for _ in range(URL_VALIDATOR_NUM_RETRIES):
        try:
            response = urllib2.urlopen(request)
        except (urllib2.HTTPError, urllib2.URLError):
            continue

        if response.code != httplib.OK:
            continue

        return True

    return False


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

def _add_to_history(request, batch, ad_group_sources):
    if not ad_group_sources:
        return
    
    ad_group = ad_group_sources[0].ad_group
    changes_text = '{} set with {} creatives was uploaded to: {}.'.format(
        batch.name,
        batch.batch_size,
        ', '.join(s.source.name for s in ad_group_sources)
    )
    settings = ad_group.get_current_settings().copy_settings()
    settings.changes_text = changes_text
    settings.save(request)
    email_helper.send_ad_group_settings_change_mail_if_necessary(ad_group, request.user, request)

