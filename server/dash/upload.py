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

from dash import models
from dash import api
from dash import constants
from dash import image_helper

logger = logging.getLogger(__name__)

NUM_THREADS = 20
MAX_CSV_TITLE_LENGTH = 256
S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT = 'contentads/errors/{filename}'


class UploadFailedException():
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

    actionlog.zwei_actions.send_multiple(actions)


def _save_error_report(rows, filename):
    string = StringIO.StringIO()

    has_crop_areas_data = False
    for idx, row in enumerate(rows):
        if row.get('crop_areas') is not None and row['crop_areas'] != '':
            has_crop_areas_data = True
            break

    if has_crop_areas_data:
        writer = unicodecsv.DictWriter(string, ['url', 'title', 'image_url', 'crop_areas', 'errors'])
    else:
        writer = unicodecsv.DictWriter(string, ['url', 'title', 'image_url', 'errors'])

    writer.writeheader()
    for row in rows:
        if not has_crop_areas_data:
            del row['crop_areas']
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


def _create_redirect_id(content_ad):
    try:
        content_ad.redirect_id = redirector_helper.insert_redirect(
            content_ad.url,
            content_ad.pk,
            content_ad.ad_group_id,
        )
        content_ad.save()
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

        cleaners = {
            'title': partial(_clean_title, title),
            'url': partial(_clean_url, url, ad_group),
            'image': partial(_clean_image, image_url, crop_areas)
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
        url = _validate_url(url)
    except ValidationError:
        raise ValidationError('Invalid URL')

    tracking_codes = url_helper.combine_tracking_codes(
        ad_group.get_current_settings().get_tracking_codes(),
        url_helper.get_tracking_id_params(ad_group.id, 'z1')
    )
    url_with_tracking_codes = url_helper.add_tracking_codes_to_url(url, tracking_codes)

    if _is_content_unreachable(url_with_tracking_codes):
        raise ValidationError('Content unreachable')

    return url


def _is_content_unreachable(url):
    request = urllib2.Request(url)
    request.add_header('User-Agent', settings.URL_VALIDATOR_USER_AGENT)

    try:
        response = urllib2.urlopen(request)
    except (urllib2.HTTPError, urllib2.URLError):
        return True

    if response.code != httplib.OK:
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
