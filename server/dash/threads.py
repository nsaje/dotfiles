from threading import Thread
import logging
import json
import unicodecsv
import StringIO

from django.db import transaction
from django.forms import ValidationError
from django.core import validators

from dash import api
from dash import image_helper
from dash import models
from dash import constants

import actionlog.zwei_actions

from utils import s3helpers

logger = logging.getLogger(__name__)

S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT = 'contentads/errors/{filename}'


class UploadFailedException():
    pass


class ProcessUploadThread(Thread):
    def __init__(self, content_ads_data, filename, batch, ad_group_id, request, *args, **kwargs):
        self.content_ads_data = content_ads_data
        self.filename = filename
        self.batch = batch
        self.ad_group_id = ad_group_id
        self.request = request
        super(ProcessUploadThread, self).__init__(*args, **kwargs)

    def run(self):
        ad_group_sources = [s for s in models.AdGroupSource.objects.filter(ad_group_id=self.ad_group_id)
                            if s.can_manage_content_ads and s.source.can_manage_content_ads()]

        try:
            # ensure content ads are only commited to DB
            # if all of them are successfully processed
            with transaction.atomic():
                num_errors = 0

                content_ad_sources = []
                for row in self.content_ads_data:
                    data, errors = self._clean_row(row)

                    if errors:
                        row['errors'] = ', '.join(errors)
                        num_errors += len(errors)
                        continue

                    content_ad_sources.extend(self._create_objects(data, ad_group_sources))

                if num_errors > 0:
                    # raise exception to rollback transaction
                    raise UploadFailedException()

                actions = api.submit_content_ads(content_ad_sources, self.request)

                self.batch.status = constants.UploadBatchStatus.DONE
                self.batch.save()
        except UploadFailedException:
            self.batch.error_report_key = self._save_error_report()
            self.batch.status = constants.UploadBatchStatus.FAILED
            self.batch.num_errors = num_errors
            self.batch.save()
            return
        except Exception:
            logger.exception('Exception in ProcessUploadThread')
            self.batch.status = constants.UploadBatchStatus.FAILED
            self.batch.save()
            return

        actionlog.zwei_actions.send_multiple(actions)

    def _create_objects(self, data, ad_group_sources):
        content_ad = models.ContentAd.objects.create(
            image_id=data['image_id'],
            image_width=data['image_width'],
            image_height=data['image_height'],
            image_hash=data['image_hash'],
            url=data['url'],
            title=data['title'],
            batch=self.batch,
            ad_group_id=self.ad_group_id,
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

        return content_ad_sources

    def _save_error_report(self):
        string = StringIO.StringIO()

        writer = unicodecsv.DictWriter(string, ['url', 'title', 'image_url', 'crop_areas', 'errors'])
        writer.writeheader()
        for row in self.content_ads_data:
            writer.writerow(row)

        content = string.getvalue()

        key = S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT.format(
            filename=s3helpers.generate_safe_filename(self.filename, content)
        )

        try:
            s3helpers.S3Helper().put(key, content)
            return key
        except Exception:
            logger.exception('Error while saving upload error report')

        return None

    def _clean_row(self, row):
        errors = []
        process_image = True

        url = row.get('url')
        title = row.get('title')
        image_url = row.get('image_url')
        crop_areas = row.get('crop_areas')

        validate_url = validators.URLValidator(schemes=['http', 'https'])

        try:
            validate_url(url)
        except ValidationError:
            errors.append('Invalid URL')

        try:
            validate_url(image_url)
        except ValidationError:
            process_image = False
            errors.append('Invalid image URL')

        if title is None or not len(title):
            errors.append('Invalid title')

        try:
            crop_areas = self._parse_crop_areas(crop_areas)
        except ValidationError:
            crop_areas = None
            process_image = False
            errors.append('Invalid crop areas')

        try:
            if process_image:
                image_id, width, height, image_hash = image_helper.process_image(
                    image_url, crop_areas)
        except image_helper.ImageProcessingException:
            errors.append('Image could not be processed.')

        if errors:
            return None, errors

        data = {
            'title': title,
            'url': url,
            'image_id': image_id,
            'image_width': width,
            'image_height': height,
            'image_hash': image_hash
        }

        return data, None

    def _validate_crops(self, crop_list):
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    if not isinstance(crop_list[i][j][k], (int, long)):
                        raise ValueError('Coordinate is not an integer')

    def _parse_crop_areas(self, crop_string):
        if not crop_string:
            # crop areas are optional, so return None
            # if they are not provided
            return None

        crop_string = crop_string.replace('(', '[').replace(')', ']')

        try:
            crop_list = json.loads(crop_string)
            self._validate_crops(crop_list)
        except (ValueError, IndexError):
            raise ValidationError('Invalid crop areas')

        return crop_list


class SendActionLogsThread(Thread):
    '''
    This is a hack to escape transaction that wraps every django admin mehtod.
    It should not be used elsewhere.
    '''
    def __init__(self, action_logs, *args, **kwargs):
        self.action_logs = action_logs
        super(SendActionLogsThread, self).__init__(*args, **kwargs)

    def run(self):
        actionlog.zwei_actions.send_multiple(self.action_logs)
