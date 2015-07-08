from threading import Thread
import logging
import json
import unicodecsv
import StringIO

from django.conf import settings
from django.db import transaction
from django.forms import ValidationError
from django.core import validators

import actionlog.zwei_actions
from utils import s3helpers
from utils import redirector_helper

from dash import api
from dash import image_helper
from dash import models
from dash import constants


logger = logging.getLogger(__name__)

MAX_CSV_TITLE_LENGTH = 256
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

        count_processed = 0
        try:
            # ensure content ads are only commited to DB
            # if all of them are successfully processed
            with transaction.atomic():
                num_errors = 0

                all_content_ad_sources = []
                for row in self.content_ads_data:
                    data, errors = self._clean_row(row)
                    count_processed += 1

                    # update upload batch in another thread to avoid
                    # transaction
                    t = UpdateUploadBatchThread(
                        self.batch.id,
                        count_processed
                    )
                    t.start_and_join()

                    if not errors:
                        content_ad, content_ad_sources = self._create_objects(data, ad_group_sources)
                        errors = self._create_redirect_id(content_ad)

                        if not errors:
                            all_content_ad_sources.extend(content_ad_sources)

                    if errors:
                        row['errors'] = ', '.join(errors)
                        num_errors += len(errors)
                        continue

                if num_errors > 0:
                    # raise exception to rollback transaction
                    raise UploadFailedException()

                actions = api.submit_content_ads(all_content_ad_sources, self.request)

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

    def _create_redirect_id(self, content_ad):
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

    def _save_error_report(self):
        string = StringIO.StringIO()

        fields = ['url', 'title', 'image_url']

        if any(row.get('crop_areas') for row in self.content_ads_data):
            fields.append('crop_areas')

        if any(row.get('tracker_urls') for row in self.content_ads_data):
            fields.append('tracker_urls')

        fields.append('errors')
        writer = unicodecsv.DictWriter(string, fields)

        writer.writeheader()
        for row in self.content_ads_data:
            if 'crop_areas' not in fields and 'crop_areas' in row:
                del row['crop_areas']

            if 'tracker_urls' not in fields and 'tracker_urls' in row:
                del row['tracker_urls']

            writer.writerow(row)

        content = string.getvalue()
        return self._upload_error_report_to_s3(content)

    def _upload_error_report_to_s3(self, content):
        key = S3_CONTENT_ADS_ERROR_REPORT_KEY_FORMAT.format(
            filename=s3helpers.generate_safe_filename(self.filename, content)
        )
        try:
            s3helpers.S3Helper().put(key, content)
            return key
        except Exception:
            logger.exception('Error while saving upload error report')

        return None

    def _validate_url(self, url):
        validate_url = validators.URLValidator(schemes=['http', 'https'])

        url_err = False
        try:
            validate_url(url)
        except ValidationError:
            url_err = True

        # allow urls without protocol prefix(ie. www.)
        if url_err:
            url = 'http://{url}'.format(url=url)
            try:
                validate_url(url)
            except ValidationError:
                raise ValidationError('Invalid URL')

        return url

    def _clean_tracker_urls(self, tracker_urls_string):
        if tracker_urls_string is None:
            return None

        tracker_urls = tracker_urls_string.strip().split(' ')

        result = []
        for url in tracker_urls:
            result.append(self._validate_url(url))

        return result

    def _clean_row(self, row):
        errors = []
        process_image = True

        url = row.get('url')
        title = row.get('title')
        image_url = row.get('image_url')
        crop_areas = row.get('crop_areas')
        tracker_urls_string = row.get('tracker_urls')

        try:
            tracker_urls = self._clean_tracker_urls(tracker_urls_string)
        except ValidationError:
            tracker_urls = None
            errors.append('Invalid tracker URLs')

        try:
            url = self._validate_url(url)
        except ValidationError:
            errors.append('Invalid URL')

        try:
            image_url = self._validate_url(image_url)
        except ValidationError:
            errors.append('Invalid image URL')

        if title is None or not len(title):
            errors.append('Missing title')
        elif len(title) > MAX_CSV_TITLE_LENGTH:
            errors.append('Title too long (max %d characters)' % MAX_CSV_TITLE_LENGTH)

        try:
            crop_areas = self._parse_crop_areas(crop_areas)
        except ValidationError:
            crop_areas = None
            process_image = False
            errors.append('Invalid crop areas')

        error_status = None
        try:
            if process_image:
                image_id, width, height, image_hash = image_helper.process_image(image_url, crop_areas)
        except image_helper.ImageProcessingException as e:
            error_status = e.status() or 'error'

        if error_status == 'image-size-error':
            errors.append('Image too big.')
        elif error_status == 'download-error':
            errors.append(('Image could not be downloaded.'))
        elif error_status is not None:
            errors.append('Image could not be processed.')

        if errors:
            return None, errors

        data = {
            'title': title,
            'url': url,
            'image_id': image_id,
            'image_width': width,
            'image_height': height,
            'image_hash': image_hash,
            'tracker_urls': tracker_urls
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


class UpdateUploadBatchThread(Thread):
    def __init__(self, batch_id, processed_content_ads, *args, **kwargs):
        self.batch_id = batch_id
        self.processed_content_ads = processed_content_ads
        super(UpdateUploadBatchThread, self).__init__(*args, **kwargs)

    def start_and_join(self):
        # hack around the fact that all db tests are ran in transaction
        # not calling parent constructor causes run to be called as a normal
        # function
        if settings.TESTING:
            self.run()
            return
        self.start()
        self.join()

    def run(self):
        batch = models.UploadBatch.objects.get(pk=self.batch_id)
        batch.processed_content_ads = self.processed_content_ads
        batch.save()


class SendActionLogsThread(Thread):
    '''
    This is a hack used to escape transaction that wraps every django admin method.
    It's not intended to be used elsewhere.
    '''
    def __init__(self, action_logs, *args, **kwargs):
        self.action_logs = action_logs
        super(SendActionLogsThread, self).__init__(*args, **kwargs)

    def run(self):
        actionlog.zwei_actions.send_multiple(self.action_logs)
