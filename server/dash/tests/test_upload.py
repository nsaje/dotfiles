#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock
import httplib
import urllib2

from django.http import HttpRequest
from django.test import TestCase

from dash import models
from dash import upload
from dash import image_helper
from dash import constants

from actionlog.models import ActionLog

from zemauth.models import User


class ErrorReportTest(TestCase):
    def _fake_upload_error_report_to_s3(self, content, filename):
        self.error_report = content
        return None

    def test_error_report(self):
        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        errors = 'Error message'

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas,
            'errors': errors
        }]
        filename = 'testname.csv'

        upload._upload_error_report_to_s3 = self._fake_upload_error_report_to_s3
        upload._save_error_report(content_ads, filename)
        self.assertEqual(
            '''url,title,image_url,crop_areas,errors
http://example.com,test title,http://example.com/image,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))",Error message\n'''.replace("\n", '\r\n'),
            self.error_report)

    def test_error_report_no_crop_areas(self):
        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = ''

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }]
        filename = 'testname.csv'

        upload._upload_error_report_to_s3 = self._fake_upload_error_report_to_s3
        upload._save_error_report(content_ads, filename)
        self.assertEqual(
            '''url,title,image_url,errors
http://example.com,test title,http://example.com/image,\n'''.replace("\n", '\r\n'),
            self.error_report)


@patch('dash.upload.urllib2.urlopen')
@patch('dash.upload.image_helper.process_image')
class CleanRowTest(TestCase):
    fixtures = ['test_api.yaml']

    def _run_clean_row(self, url, title, image_url, crop_areas):
        row = {
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }

        batch_name = 'Test batch name'
        batch = models.UploadBatch.objects.create(name=batch_name)
        ad_group = models.AdGroup.objects.get(pk=1)

        result_row, data, errors = upload._clean_row(batch, ad_group, row)

        self.assertEqual(row, result_row)

        return data, errors

    def test_clean_row(self, mock_process_image, mock_urlopen):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"
        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_urlopen.return_value = Mock(code=httplib.OK)

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'image': {
                'id': image_id,
                'width': image_width,
                'height': image_height,
                'hash': image_hash
            },
            'title': title,
            'url': url
        })
        self.assertEqual(errors, [])

    def test_invalid_title(self, mock_process_image, mock_urlopen):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"
        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_urlopen.return_value = Mock(code=httplib.OK)

        url = 'http://example.com'
        title = ''
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'image': {
                'id': image_id,
                'width': image_width,
                'height': image_height,
                'hash': image_hash
            },
            'url': url
        })
        self.assertEqual(errors, ['Missing title'])

    def test_url_without_protocol(self, mock_process_image, mock_urlopen):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"
        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_urlopen.return_value = Mock(code=httplib.OK)

        url = 'example.com'
        title = 'test_title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'image': {
                'id': image_id,
                'width': image_width,
                'height': image_height,
                'hash': image_hash
            },
            'url': 'http://{}'.format(url),
            'title': title
        })
        self.assertEqual(errors, [])

    def test_invalid_url(self, mock_process_image, mock_urlopen):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"
        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_urlopen.return_value = Mock(code=httplib.OK)

        url = 'example'
        title = 'test_title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'image': {
                'id': image_id,
                'width': image_width,
                'height': image_height,
                'hash': image_hash
            },
            'title': title,
        })
        self.assertEqual(errors, ['Invalid URL'])

    def test_invalid_image_url(self, mock_process_image, mock_urlopen):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"
        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_urlopen.return_value = Mock(code=httplib.OK)

        url = 'http://example.com'
        title = 'test title'
        image_url = 'example/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'title': title,
            'url': url
        })
        self.assertEqual(errors, ['Invalid Image URL'])

    def test_invalid_crop_areas(self, mock_process_image, mock_urlopen):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"
        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_urlopen.return_value = Mock(code=httplib.OK)

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '((((177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'title': title,
            'url': url
        })
        self.assertEqual(errors, ['Invalid crop areas'])

    def test_image_not_downloaded(self, mock_process_image, mock_urlopen):
        mock_process_image.side_effect = image_helper.ImageProcessingException
        mock_urlopen.return_value = Mock(code=httplib.OK)

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'title': title,
            'url': url
        })
        self.assertEqual(errors, ['Image could not be processed'])

    def test_content_unreachable(self, mock_process_image, mock_urlopen):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"
        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_urlopen.side_effect = urllib2.URLError('Error')

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        data, errors = self._run_clean_row(url, title, image_url, crop_areas)

        self.assertEqual(data, {
            'image': {
                'id': image_id,
                'width': image_width,
                'height': image_height,
                'hash': image_hash
            },
            'title': title,
        })
        self.assertEqual(errors, ['Content unreachable'])


@patch('dash.upload.redirector_helper.insert_redirect')
class ProcessCallbackTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.save_error_report_patcher = patch('dash.upload._save_error_report')
        self.mock_save_error_report = self.save_error_report_patcher.start()
        self.mock_save_error_report.return_value = 'mock_key'

        self.send_multiple_patcher = patch('dash.upload.actionlog.zwei_actions.send_multiple')
        self.mock_send_multiple = self.send_multiple_patcher.start()

    def tearDown(self):
        self.save_error_report_patcher.stop()
        self.send_multiple_patcher.stop()

    def test_process_callback(self, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

        redirect_id = "u123456"

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        row = {
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }

        filename = 'testname.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        cleaned_data = {
            'image': {
                'id': image_id,
                'width': image_width,
                'height': image_height,
                'hash': image_hash
            },
            'title': title,
            'url': url
        }

        errors = []

        batch = models.UploadBatch.objects.create(name=batch_name)
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        request = HttpRequest()
        user = User.objects.create_user('user@test.com')
        request.user = user

        mock_redirect_insert.return_value = redirect_id

        results = [(row, cleaned_data, errors)]
        upload._process_callback(batch, ad_group_id, [ad_group_source], filename, request, results)

        content_ad = models.ContentAd.objects.latest()
        self.assertEqual(content_ad.title, title)
        self.assertEqual(content_ad.url, url)
        self.assertEqual(content_ad.ad_group_id, ad_group_id)

        self.assertEqual(content_ad.redirect_id, redirect_id)
        self.assertEqual(content_ad.image_id, image_id)
        self.assertEqual(content_ad.image_width, image_width)
        self.assertEqual(content_ad.image_height, image_height)
        self.assertEqual(content_ad.image_hash, image_hash)
        self.assertEqual(content_ad.batch.name, batch_name)
        self.assertEqual(content_ad.state, constants.ContentAdSourceState.ACTIVE)

        content_ad_source = models.ContentAdSource.objects.get(content_ad_id=content_ad.id)
        self.assertEqual(content_ad_source.source_id, ad_group_source.source_id)
        self.assertEqual(
            content_ad_source.submission_status,
            constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        )
        self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.ACTIVE)

        self.assertEqual(batch.status, constants.UploadBatchStatus.DONE)

        mock_redirect_insert.assert_called_with(content_ad.url, content_ad.id, content_ad.ad_group_id)

        action = ActionLog.objects.get(content_ad_source_id=content_ad_source.id)
        self.assertEqual(action.ad_group_source_id, ad_group_source.id)

        self.mock_send_multiple.assert_called_with([action])

    def test_process_callback_errors(self, mock_redirect_insert):
        redirect_id = "u123456"

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        row = {
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }

        filename = 'testname.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        cleaned_data = None
        errors = ['Some random error']

        batch = models.UploadBatch.objects.create(name=batch_name)
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        request = HttpRequest()
        user = User.objects.create_user('user@test.com')
        request.user = user

        mock_redirect_insert.return_value = redirect_id

        prev_content_ad_count = models.ContentAd.objects.all().count()
        prev_action_count = ActionLog.objects.all().count()

        results = [(row, cleaned_data, errors)]
        upload._process_callback(batch, ad_group_id, [ad_group_source], filename, request, results)

        new_content_ad_count = models.ContentAd.objects.all().count()
        new_action_count = ActionLog.objects.all().count()

        self.assertEqual(prev_content_ad_count, new_content_ad_count)
        self.assertEqual(prev_action_count, new_action_count)

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)

        self.assertFalse(mock_redirect_insert.called)
        self.assertFalse(self.mock_send_multiple.called)

        self.mock_save_error_report.assert_called_with([row], filename)

    def test_process_callback_redirector_error(self, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        row = {
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }

        filename = 'testname.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        cleaned_data = {
            'image': {
                'id': image_id,
                'width': image_width,
                'height': image_height,
                'hash': image_hash
            },
            'title': title,
            'url': url
        }

        errors = []

        batch = models.UploadBatch.objects.create(name=batch_name)
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        request = HttpRequest()
        user = User.objects.create_user('user@test.com')
        request.user = user

        mock_redirect_insert.side_effect = Exception

        prev_content_ad_count = models.ContentAd.objects.all().count()
        prev_action_count = ActionLog.objects.all().count()

        results = [(row, cleaned_data, errors)]
        upload._process_callback(batch, ad_group_id, [ad_group_source], filename, request, results)

        new_content_ad_count = models.ContentAd.objects.all().count()
        new_action_count = ActionLog.objects.all().count()

        self.assertEqual(prev_content_ad_count, new_content_ad_count)
        self.assertEqual(prev_action_count, new_action_count)

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)

        self.assertFalse(self.mock_send_multiple.called)

    @patch('dash.upload._create_redirect_id')
    def test_process_callback_exception(self, mock_redirect_insert, mock_create_redirect_id):
        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        row = {
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }

        filename = 'testname.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        cleaned_data = None
        errors = ['Some random error']

        batch = models.UploadBatch.objects.create(name=batch_name)
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        request = HttpRequest()
        user = User.objects.create_user('user@test.com')
        request.user = user

        mock_create_redirect_id.side_effect = Exception

        prev_content_ad_count = models.ContentAd.objects.all().count()
        prev_action_count = ActionLog.objects.all().count()

        results = [(row, cleaned_data, errors)]
        upload._process_callback(batch, ad_group_id, [ad_group_source], filename, request, results)

        new_content_ad_count = models.ContentAd.objects.all().count()
        new_action_count = ActionLog.objects.all().count()

        self.assertEqual(prev_content_ad_count, new_content_ad_count)
        self.assertEqual(prev_action_count, new_action_count)

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        self.assertFalse(self.mock_send_multiple.called)
        self.mock_save_error_report.assert_called_with([row], filename)
