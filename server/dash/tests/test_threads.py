#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock

from django.test import TestCase

from dash import threads
from dash import image_helper
from dash import constants
from dash import models

import actionlog.models


class ProcessUploadThreadTest(TestCase):

    def _fake_upload_error_report_to_s3(self, content):
        self.error_report = content
        return None

    @patch('dash.threads.redirector_helper.insert_redirect')
    @patch('dash.threads.image_helper.process_image')
    def test_no_crop_areas_report(self, mock_process_image, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

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
        ad_group_id = 1

        mock_process_image.return_value = image_id, image_width, image_height, image_hash

        batch_name = 'Test batch name I'
        batch = models.UploadBatch.objects.create(name=batch_name)

        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        thread._upload_error_report_to_s3 = self._fake_upload_error_report_to_s3
        thread._save_error_report()
        self.assertEqual(
            '''url,title,image_url,errors
http://example.com,test title,http://example.com/image,\n'''.replace("\n",'\r\n') ,
            self.error_report)


    @patch('dash.threads.redirector_helper.insert_redirect')
    @patch('dash.threads.image_helper.process_image')
    def test_run(self, mock_process_image, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

        redirect_id = "u123456"

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        crop_areas_list = [[[44, 22], [144, 122]], [[33, 22], [177, 122]]]

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }]
        filename = 'testname.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_redirect_insert.return_value = redirect_id

        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        prev_actionlog_count = actionlog.models.ActionLog.objects.all().count()
        thread.run()

        mock_process_image.assert_called_with(image_url, crop_areas_list)

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

        self.assertEqual(prev_actionlog_count, actionlog.models.ActionLog.objects.all().count())
        self.assertEqual(batch.status, constants.UploadBatchStatus.DONE)

    @patch('dash.threads.redirector_helper.insert_redirect')
    @patch('dash.threads.image_helper.process_image')
    @patch('dash.views.views.actionlog.api_contentads.init_insert_content_ad_action')
    def test_exception(self, mock_insert_action, mock_process_image, mock_redirect_insert):
        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        redirect_id = "u123456"

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }]
        filename = 'testfile.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        mock_redirect_insert.return_value = redirect_id

        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        thread._clean_row = Mock(side_effect=Exception)

        thread.run()

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        self.assertFalse(mock_insert_action.called)

    @patch('dash.threads.redirector_helper.insert_redirect')
    @patch('dash.threads.image_helper.process_image')
    @patch('dash.views.views.actionlog.api_contentads.init_insert_content_ad_action')
    def test_redirector_exception(self, mock_insert_action, mock_process_image, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }]
        filename = 'testname.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        mock_process_image.return_value = image_id, image_width, image_height, image_hash
        mock_insert_action.side_effect = Exception

        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)

        thread.run()

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        self.assertTrue(mock_redirect_insert.called)
        self.assertEqual(thread.content_ads_data[0]['errors'], 'Internal server error while processing request')

    @patch('dash.threads.redirector_helper.insert_redirect')
    @patch('dash.threads.s3helpers.S3Helper')
    @patch('dash.threads.s3helpers.generate_safe_filename')
    @patch('dash.threads.image_helper.process_image')
    @patch('dash.views.views.actionlog.api_contentads.init_insert_content_ad_action')
    def test_run_validation_errors(self, mock_insert_action, mock_process_image, mock_generate_safe_filename, MockS3Helper, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

        redirect_id = "u123456"

        # two content ads
        content_ads = [{
            'url': 'invalidurl',
            'title': '',
            'image_url': '',
            'crop_areas': '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        }, {
            'url': 'http://example.com',
            'title': 'very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long test title',
            'image_url': 'http://example.com/image',
            'crop_areas': '(23, 21(()))'
        }]
        filename = 'filename.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        # raise ImageProcessingException for the second ad
        mock_process_image.side_effect = [
            (image_id, image_width, image_height, image_hash),
            image_helper.ImageProcessingException
        ]

        mock_instance = Mock()
        MockS3Helper.return_value = mock_instance

        mock_redirect_insert.return_value = redirect_id

        mock_generate_safe_filename.return_value = 'safefilename.csv'

        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        thread.run()

        mock_instance.put.assert_called_with(
            'contentads/errors/safefilename.csv',
            'url,title,image_url,crop_areas,errors\r\ninvalidurl,,,"(((44, 22), (144, 122)), ((33, 22), (177, 122)))","Invalid URL, Invalid image URL, Missing title"\r\nhttp://example.com,very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long test title,http://example.com/image,"(23, 21(()))","Title too long (max 256 characters), Invalid crop areas"\r\n'
        )
        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        self.assertFalse(mock_insert_action.called)

    @patch('dash.threads.redirector_helper.insert_redirect')
    @patch('dash.threads.s3helpers.S3Helper')
    @patch('dash.threads.s3helpers.generate_safe_filename')
    @patch('dash.threads.image_helper.process_image')
    @patch('dash.views.views.actionlog.api_contentads.init_insert_content_ad_action')
    def test_www_prefix(self, mock_insert_action, mock_process_image, mock_generate_safe_filename, MockS3Helper, mock_redirect_insert):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200
        image_hash = "123"

        redirect_id = "u123456"

        # two content ads
        content_ads = [{
            'url': 'noprefix.com',
            'title': 'Test title',
            'image_url': 'example.com/image',
            'crop_areas': '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        }, {
            'url': 'http://prefix.com',
            'title': 'Test title',
            'image_url': 'www.example.com/image',
            'crop_areas': '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        }]
        filename = 'filename.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        # raise ImageProcessingException for the second ad
        mock_process_image.side_effect = [
            (image_id, image_width, image_height, image_hash),
            (image_id, image_width, image_height, image_hash),
        ]

        mock_instance = Mock()
        MockS3Helper.return_value = mock_instance

        mock_redirect_insert.return_value = redirect_id

        mock_generate_safe_filename.return_value = 'safefilename.csv'

        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        thread.run()

        self.assertEqual(batch.status, constants.UploadBatchStatus.DONE)

        mock_process_image.assert_called_with('http://www.example.com/image',[[[44, 22], [144, 122]], [[33, 22], [177, 122]]])

        content_ads = models.ContentAd.objects.all().order_by('-created_dt')
        self.assertEqual('http://prefix.com', content_ads[0].url)
        self.assertEqual('http://noprefix.com', content_ads[1].url)

    @patch('dash.threads.image_helper.process_image')
    def test_clean_row_z3_image_too_large(self, mock_process_image):
        filename = 'filename.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        content_ads = [{
            'url': 'http://example.com',
            'title': 'ordinar ad',
            'image_url': 'http://example.com/image',
            'crop_areas': '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        }]

        mock_process_image.side_effect = [
            image_helper.ImageProcessingException(status='image-size-error')
        ]

        batch = models.UploadBatch.objects.create(name=batch_name)
        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        res, err = thread._clean_row(content_ads[0])

        self.assertIsNone(res)
        self.assertTrue("too big" in err[0])

    @patch('dash.threads.image_helper.process_image')
    def test_clean_row_z3_dload_error(self, mock_process_image):
        filename = 'filename.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        content_ads = [{
            'url': 'http://example.com',
            'title': 'ordinar ad',
            'image_url': 'http://example.com/image',
            'crop_areas': '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        }]

        mock_process_image.side_effect = [
            image_helper.ImageProcessingException(status='download-error')
        ]

        batch = models.UploadBatch.objects.create(name=batch_name)
        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        res, err = thread._clean_row(content_ads[0])

        self.assertIsNone(res)
        self.assertTrue("could not be downloaded" in err[0])

    @patch('dash.threads.image_helper.process_image')
    def test_clean_row_z3_generic_error(self, mock_process_image):
        filename = 'filename.csv'
        batch_name = 'Test batch name'
        ad_group_id = 1

        content_ads = [{
            'url': 'http://example.com',
            'title': 'ordinar ad',
            'image_url': 'http://example.com/image',
            'crop_areas': '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        }]

        mock_process_image.side_effect = [
            image_helper.ImageProcessingException(status='error')
        ]

        batch = models.UploadBatch.objects.create(name=batch_name)
        thread = threads.ProcessUploadThread(content_ads, filename, batch, ad_group_id, None)
        res, err = thread._clean_row(content_ads[0])

        self.assertIsNone(res)
        self.assertTrue("could not be processed" in err[0])
