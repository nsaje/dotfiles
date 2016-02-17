#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock
import httplib
import urllib2

from django.http import HttpRequest
from django.test import TestCase, override_settings

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

    def test_error_report_all_fields(self):
        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        display_url = 'abc.com'
        brand_name = 'Brand Inc.'
        description = 'Very nice!'
        call_to_action = 'Now!'
        errors = 'Error message'

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas,
            'display_url': display_url,
            'brand_name': brand_name,
            'description': description,
            'call_to_action': call_to_action,
            'errors': errors,
        }]
        filename = 'testname.csv'

        upload._upload_error_report_to_s3 = self._fake_upload_error_report_to_s3
        upload._save_error_report(content_ads, filename)
        self.assertEqual(
            '''url,title,image_url,crop_areas,display_url,brand_name,description,call_to_action,errors
http://example.com,test title,http://example.com/image,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))",abc.com,Brand Inc.,Very nice!,Now!,Error message\n'''.replace("\n", '\r\n'),
            self.error_report)

    def test_error_report_no_optional_fields(self):
        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        errors = 'Error message'

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'errors': errors,
        }]
        filename = 'testname.csv'

        upload._upload_error_report_to_s3 = self._fake_upload_error_report_to_s3
        upload._save_error_report(content_ads, filename)
        self.assertEqual(
            '''url,title,image_url,errors
http://example.com,test title,http://example.com/image,Error message\n'''.replace("\n", '\r\n'),
            self.error_report)


class CleanRowTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        # default test data
        self.url = u'http://example.com'
        self.title = 'test title'
        self.image_url = 'http://example.com/image'
        self.crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        self.tracker_urls = 'https://example.com/p.gif'

        self.display_url = ''
        self.brand_name = ''
        self.description = ''
        self.call_to_action = ''

        self.upload_form_display_url = 'abc.com'
        self.upload_form_brand_name = 'ABC inc.'
        self.upload_form_description = "Oh my desc!"
        self.upload_form_call_to_action = "Act!"

        self.image_id = 'test_image_id'
        self.image_width = 100
        self.image_height = 200
        self.image_hash = "123"

        self.process_image_patcher = patch('dash.upload.image_helper.process_image')
        self.mock_process_image = self.process_image_patcher.start()
        self.mock_process_image.return_value = (
            self.image_id, self.image_width, self.image_height, self.image_hash)

        self.validate_url_patcher = patch('dash.upload.redirector_helper.validate_url')
        self.mock_validate_url = self.validate_url_patcher.start()
        self.mock_validate_url.return_value = True

        self.default_expected_data = {
            'image': {
                'id': self.image_id,
                'width': self.image_width,
                'height': self.image_height,
                'hash': self.image_hash,
                'crop_areas': self.crop_areas
            },
            'title': self.title,
            'tracker_urls': self.tracker_urls.split(' '),
            'url': self.url,
            'display_url': self.upload_form_display_url,
            'brand_name': self.upload_form_brand_name,
            'description': self.upload_form_description,
            'call_to_action': self.upload_form_call_to_action,
        }

    def tearDown(self):
        self.process_image_patcher.stop()
        self.validate_url_patcher.stop()

    def _run_clean_row(self):
        row = {
            'url': self.url,
            'title': self.title,
            'image_url': self.image_url,
            'crop_areas': self.crop_areas,
            'tracker_urls': self.tracker_urls,
            'display_url': self.display_url,
            'brand_name': self.brand_name,
            'description': self.description,
            'call_to_action': self.call_to_action,
        }

        batch_name = 'Test batch name'
        batch = models.UploadBatch.objects.create(name=batch_name)
        upload_form_cleaned_fields = {'display_url': self.upload_form_display_url,
                                      'brand_name': self.upload_form_brand_name,
                                      'description': self.upload_form_description,
                                      'call_to_action': self.upload_form_call_to_action}

        ad_group = models.AdGroup.objects.get(pk=1)

        result_row, data, errors = upload._clean_row(batch, upload_form_cleaned_fields, ad_group, row)

        self.assertEqual(row, result_row)

        return data, errors

    def test_clean_row(self):
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, [])

    def test_invalid_title(self):
        self.title = ''
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('title')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Missing title'])

    def test_url_without_protocol(self):
        self.url = u'example.com'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, [])

    def test_invalid_url(self):
        self.url = u'example'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('url')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid URL'])

    def test_url_strip(self):
        self.url = u' http://example.com '
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, [])

    def test_unicode_url(self):
        self.url = u'http://exampleś.com'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('url')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid URL'])

    def test_invalid_image_url(self):
        self.image_url = 'example/image'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('image')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid Image URL'])

    def test_image_url_strip(self):
        self.image_url = u' http://example.com/image '
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, [])

    def test_invalid_crop_areas(self):
        self.crop_areas = '((((177, 122)))'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('image')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid crop areas'])

    def test_image_not_downloaded(self):
        self.mock_process_image.side_effect = image_helper.ImageProcessingException

        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('image')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Image could not be processed'])

    def test_content_unreachable(self):
        self.mock_validate_url.return_value = False

        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('url')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Content unreachable'])

    def test_invalid_tracker_urls(self):
        self.tracker_urls = 'invalid_url'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('tracker_urls')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid tracker URLs'])

    def test_unicode_tracker_urls(self):
        self.tracker_urls = u'http://exampleś.com'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('tracker_urls')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid tracker URLs'])

    def test_invalid_tracker_urls_not_https(self):
        self.tracker_urls = 'http://example.com/p.gif'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('tracker_urls')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid tracker URLs'])

    def test_multiple_tracker_urls(self):
        self.tracker_urls = 'https://example.com/p1.gif https://example.com/p2.gif'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data['tracker_urls'] = self.tracker_urls.split(' ')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, [])

    def test_invalid_multiple_tracker_urls(self):
        self.tracker_urls = 'https://example.com/p1.gif invalid_url'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('tracker_urls')
        self.assertEqual(data, expected_data)
        self.assertEqual(errors, ['Invalid tracker URLs'])

    def test_no_upload_form_fields(self):
        self.upload_form_display_url = ''
        self.upload_form_brand_name = ''
        self.upload_form_description = ''
        self.upload_form_call_to_action = ''
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('display_url')
        expected_data.pop('brand_name')
        expected_data.pop('description')
        expected_data.pop('call_to_action')
        self.assertEqual(data, expected_data)
        self.assertItemsEqual(errors, 
            [u'Display URL has to be present in CSV or default value should be submitted in the upload form.',
            u'Brand name has to be present in CSV or default value should be submitted in the upload form.',
            u'Description has to be present in CSV or default value should be submitted in the upload form.',
            u'Call to action has to be present in CSV or default value should be submitted in the upload form.'])

    def test_csv_override(self):
        self.display_url = 'def.com'
        self.brand_name = 'NewBrand inc.'
        self.description = 'Better description'
        self.call_to_action = 'Act Now!'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data['display_url'] = self.display_url
        expected_data['brand_name'] = self.brand_name
        expected_data['description'] = self.description
        expected_data['call_to_action'] = self.call_to_action
        self.assertItemsEqual(errors, [])
        self.assertEqual(data, expected_data)

    def test_csv_override_max_lengths(self):
        self.display_url = 'a' * 300 + ".com"
        self.brand_name = 'b' * 300
        self.description = 'c' * 300
        self.call_to_action = 'd' * 300
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('display_url')
        expected_data.pop('brand_name')
        expected_data.pop('description')
        expected_data.pop('call_to_action')
        self.assertItemsEqual(errors, [u'Display URL is too long (304/25).',
                                       u'Brand name is too long (300/25).',
                                       u'Description is too long (300/140).',
                                       u'Call to action is too long (300/25).'])
        self.assertEqual(data, expected_data)

    def test_csv_override_invalid_display_url(self):
        self.display_url = 'aaaa'
        data, errors = self._run_clean_row()
        expected_data = dict(self.default_expected_data)
        expected_data.pop('display_url')
        self.assertItemsEqual(errors, [u'Display URL is invalid.'])
        self.assertEqual(data, expected_data)


@patch('dash.upload.redirector_helper.insert_redirect')
class ProcessCallbackTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.save_error_report_patcher = patch('dash.upload._save_error_report')
        self.mock_save_error_report = self.save_error_report_patcher.start()
        self.mock_save_error_report.return_value = 'mock_key'

        self.actionlog_send_patcher = patch('dash.upload.actionlog.zwei_actions.send')
        self.mock_actionlog_send = self.actionlog_send_patcher.start()

        self.mock_upload_update_progress = patch('dash.threads.UpdateUploadBatchThread')

    def tearDown(self):
        self.save_error_report_patcher.stop()
        self.actionlog_send_patcher.stop()

    @override_settings(
        SEND_AD_GROUP_SETTINGS_CHANGE_MAIL=False
    )
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
        tracker_url_list = ['https://example.com/p.gif']

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
                'hash': image_hash,
                'crop_areas': crop_areas,
            },
            'tracker_urls': tracker_url_list,
            'title': title,
            'url': url,
            'display_url': 'brand.com',
            'brand_name': 'Brand inc.',
            'description': 'This content is a must read',
            'call_to_action': 'Act!',
        }

        errors = []

        batch = models.UploadBatch.objects.create(name=batch_name)
        batch.batch_size = 10
        batch.save()
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        user = User.objects.create_user('user@test.com')
        request.user = user

        mock_redirect_insert.return_value = redirect_id

        results = [(row, cleaned_data, errors)]
        upload._process_callback(batch, models.AdGroup.objects.get(pk=ad_group_id), [ad_group_source], filename, request, results)

        # check for errors first, before proceeding to the rest
        self.assertEqual(batch.status, constants.UploadBatchStatus.DONE)
        self.assertIn(batch.num_errors, [0, None])

        content_ad = models.ContentAd.objects.latest()
        self.assertEqual(content_ad.title, title)
        self.assertEqual(content_ad.url, url)
        self.assertEqual(content_ad.ad_group_id, ad_group_id)
        self.assertEqual(content_ad.display_url, cleaned_data['display_url'])
        self.assertEqual(content_ad.brand_name, cleaned_data['brand_name'])
        self.assertEqual(content_ad.description, cleaned_data['description'])
        self.assertEqual(content_ad.call_to_action, cleaned_data['call_to_action'])

        self.assertEqual(content_ad.redirect_id, redirect_id)
        self.assertEqual(content_ad.image_id, image_id)
        self.assertEqual(content_ad.image_width, image_width)
        self.assertEqual(content_ad.image_height, image_height)
        self.assertEqual(content_ad.image_hash, image_hash)
        self.assertEqual(content_ad.batch.name, batch_name)
        self.assertEqual(content_ad.state, constants.ContentAdSourceState.ACTIVE)
        self.assertEqual(content_ad.crop_areas, crop_areas)

        content_ad_source = models.ContentAdSource.objects.get(content_ad_id=content_ad.id)
        self.assertEqual(content_ad_source.source_id, ad_group_source.source_id)
        self.assertEqual(
            content_ad_source.submission_status,
            constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        )
        self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.ACTIVE)

        mock_redirect_insert.assert_called_with(content_ad.url, content_ad.id, content_ad.ad_group_id)

        action = ActionLog.objects.get(content_ad_source_id=content_ad_source.id)
        self.assertEqual(action.ad_group_source_id, ad_group_source.id)

        self.mock_actionlog_send.assert_called_with([action])

        settings = ad_group_source.ad_group.get_current_settings()
        self.assertEqual(settings.changes_text,
                         u'Imported batch "Test batch name" with 10 content ads.')

    @override_settings(
        SEND_AD_GROUP_SETTINGS_CHANGE_MAIL=False
    )
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
        upload._process_callback(batch, models.AdGroup.objects.get(pk=ad_group_id), [ad_group_source], filename, request, results)
        self.assertEqual(batch.num_errors, 1) 
        
        new_content_ad_count = models.ContentAd.objects.all().count()
        new_action_count = ActionLog.objects.all().count()

        self.assertEqual(prev_content_ad_count, new_content_ad_count)
        self.assertEqual(prev_action_count, new_action_count)

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)

        self.assertFalse(mock_redirect_insert.called)
        self.assertFalse(self.mock_actionlog_send.called)

        self.mock_save_error_report.assert_called_with([row], filename)

    @override_settings(
        SEND_AD_GROUP_SETTINGS_CHANGE_MAIL=False
    )
    def test_process_callback_redirector_error(self, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        tracker_url_list = ['https://example.com/p.gif']

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
                'hash': image_hash,
                'crop_areas': crop_areas
            },
            'tracker_urls': tracker_url_list,
            'title': title,
            'url': url,
            'display_url': 'brand.com',
            'brand_name': 'Brand inc.',
            'description': 'This content is a must read',
            'call_to_action': 'Act!',
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
        upload._process_callback(batch, models.AdGroup.objects.get(pk=ad_group_id), [ad_group_source], filename, request, results)
        
        # first test if there really were errors we're expecting (there could be other exceptions)
        # ideally we should check if specific exception we were expecting happened, 
        self.assertEqual(batch.num_errors, 1)

        new_content_ad_count = models.ContentAd.objects.all().count()
        new_action_count = ActionLog.objects.all().count()

        self.assertEqual(prev_content_ad_count, new_content_ad_count)
        self.assertEqual(prev_action_count, new_action_count)

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)

        self.assertFalse(self.mock_actionlog_send.called)

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
        self.assertFalse(self.mock_actionlog_send.called)
        self.mock_save_error_report.assert_called_with([row], filename)
