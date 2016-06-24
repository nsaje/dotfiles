# -*- coding: utf-8 -*-
import json

import boto.exception
from mock import patch, Mock, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from dash import constants
from dash import models
from zemauth.models import User
import utils.s3helpers


def _get_client(superuser=True):
    password = 'secret'

    user_id = 1 if superuser else 2
    user = User.objects.get(pk=user_id)
    username = user.email

    client = Client()
    client.login(username=username, password=password)

    return client


class UploadCsvTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    def test_get(self):
        ad_group_id = 1
        response = _get_client().get(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'defaults': {
                    'display_url': 'example.com',
                    'brand_name': 'Example',
                    'description': 'Example description',
                    'call_to_action': 'Click here!',
                }
            }
        }, json.loads(response.content))

    def test_get_permission(self):
        ad_group_id = 1
        response = _get_client(superuser=False).get(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')

    @patch('utils.lambda_helper.invoke_lambda')
    def test_post_with_common_fields(self, mock_invoke_lambda):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Tracker URLs\n'
            'http://zemanta.com/test-content-ad,test content ad,http://zemanta.com/test-image.jpg,test,entropy,'
            'https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png'
        )
        response = _get_client().post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            {
                'content_ads': mock_file,
                'batch_name': 'batch 1',
                'display_url': 'zemanta.com/default',
                'brand_name': 'Zemanta Default',
                'description': 'Default description',
                'call_to_action': 'default',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        (_, lambda_data1), _ = mock_invoke_lambda.call_args_list[0]
        self.assertFalse(lambda_data1['skipUrlValidation'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'candidates': [candidate.id],
                'errors': {
                    str(candidate.id): {
                        '__all__': ['Content ad still processing'],
                    }
                },
            }
        }, json.loads(response.content))

        self.assertEqual('batch 1', batch.name)
        self.assertEqual('test_upload.csv', batch.original_filename)
        self.assertEqual(1, batch.batch_size)

        self.assertEqual('test', candidate.label)
        self.assertEqual('http://zemanta.com/test-content-ad', candidate.url)
        self.assertEqual('test content ad', candidate.title)
        self.assertEqual('http://zemanta.com/test-image.jpg', candidate.image_url)
        self.assertEqual('entropy', candidate.image_crop)
        self.assertEqual('https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png', candidate.tracker_urls)
        self.assertEqual('zemanta.com/default', candidate.display_url)
        self.assertEqual('Zemanta Default', candidate.brand_name)
        self.assertEqual('Default description', candidate.description)
        self.assertEqual('default', candidate.call_to_action)

    @patch('utils.lambda_helper.invoke_lambda')
    def test_post_with_noverify(self, mock_invoke_lambda):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload_no-verify.csv',
            'URL,Title,Image URL,Label,Image Crop,Tracker URLs\n'
            'http://zemanta.com/test-content-ad,test content ad,http://zemanta.com/test-image.jpg,test,entropy,'
            'https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png'
        )
        response = _get_client().post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            {
                'content_ads': mock_file,
                'batch_name': 'batch 1',
                'display_url': 'zemanta.com/default',
                'brand_name': 'Zemanta Default',
                'description': 'Default description',
                'call_to_action': 'default',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        (_, lambda_data1), _ = mock_invoke_lambda.call_args_list[0]
        self.assertTrue(lambda_data1['skipUrlValidation'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'candidates': [candidate.id],
                'errors': {
                    str(candidate.id): {
                        '__all__': ['Content ad still processing'],
                    }
                },
            }
        }, json.loads(response.content))

        self.assertEqual('batch 1', batch.name)
        self.assertEqual('test_upload_no-verify.csv', batch.original_filename)
        self.assertEqual(1, batch.batch_size)

        self.assertEqual('test', candidate.label)
        self.assertEqual('http://zemanta.com/test-content-ad', candidate.url)
        self.assertEqual('test content ad', candidate.title)
        self.assertEqual('http://zemanta.com/test-image.jpg', candidate.image_url)
        self.assertEqual('entropy', candidate.image_crop)
        self.assertEqual('https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png', candidate.tracker_urls)
        self.assertEqual('zemanta.com/default', candidate.display_url)
        self.assertEqual('Zemanta Default', candidate.brand_name)
        self.assertEqual('Default description', candidate.description)
        self.assertEqual('default', candidate.call_to_action)

    @patch('utils.lambda_helper.invoke_lambda', MagicMock())
    def test_post_without_common_fields(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Tracker URLs,Display URL,Brand Name,Description,Call To Action\n'
            'http://zemanta.com/test-content-ad,test content ad,http://zemanta.com/test-image.jpg,test,entropy,'
            'https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png,zemanta.com/custom,Zemanta Custom,Custom '
            'description,custom'
        )
        response = _get_client().post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            {
                'content_ads': mock_file,
                'batch_name': 'batch 1',
                'display_url': 'zemanta.com/default',
                'brand_name': 'Zemanta Default',
                'description': 'Default description',
                'call_to_action': 'default',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'candidates': [candidate.id],
                'errors': {
                    str(candidate.id): {
                        '__all__': ['Content ad still processing'],
                    }
                },
            }
        }, json.loads(response.content))

        self.assertEqual('batch 1', batch.name)
        self.assertEqual('test_upload.csv', batch.original_filename)
        self.assertEqual(1, batch.batch_size)

        self.assertEqual('test', candidate.label)
        self.assertEqual('http://zemanta.com/test-content-ad', candidate.url)
        self.assertEqual('test content ad', candidate.title)
        self.assertEqual('http://zemanta.com/test-image.jpg', candidate.image_url)
        self.assertEqual('entropy', candidate.image_crop)
        self.assertEqual('https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png', candidate.tracker_urls)
        self.assertEqual('zemanta.com/custom', candidate.display_url)
        self.assertEqual('Zemanta Custom', candidate.brand_name)
        self.assertEqual('Custom description', candidate.description)
        self.assertEqual('custom', candidate.call_to_action)

    @patch('utils.lambda_helper.invoke_lambda', MagicMock())
    def test_post_errors(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Tracker URLs\n'
            'ahttp://zemanta.com/test-content-ad,test content ad,ahttp://zemanta.com/test-image.jpg,'
            'testtoolonglabelforthecontentadcandidatelabelfield,entropy,'
            'http://t.zemanta.com/px1.png https://t.zemanta.com/px2.png'
        )
        response = _get_client().post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            {
                'content_ads': mock_file,
                'batch_name': 'batch 1',
                'display_url': 'zemanta.com/default',
                'brand_name': 'Zemanta Default',
                'description': 'Default description',
                'call_to_action': 'default',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'candidates': [candidate.id],
                'errors': {
                    str(candidate.id): {
                        '__all__': ['Content ad still processing'],
                        'tracker_urls': ['Impression tracker URLs have to be HTTPS'],
                        'image_url': ['Invalid image URL'],
                        'url': ['Invalid URL'],
                    }
                },
            }
        }, json.loads(response.content))

    def test_post_permission(self):
        ad_group_id = 1
        response = _get_client(superuser=False).post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class UploadMultipleTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    @patch('utils.lambda_helper.invoke_lambda', MagicMock())
    def test_post(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Tracker URLs,Brand name,Display URL,Call to Action,Description\n'
            'http://zemanta.com/test-content-ad,test content ad,http://zemanta.com/test-image.jpg,test,entropy,'
            'https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png,Zemanta,zemanta.com,Click for more,description'
        )
        response = _get_client().post(
            reverse('upload_multiple', kwargs={'ad_group_id': ad_group_id}),
            {
                'content_ads': mock_file,
                'batch_name': 'batch 1',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate['errors'] = {
            '__all__': ['Content ad still processing'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'candidates': [expected_candidate],
            }
        }, json.loads(response.content))

        self.assertEqual('batch 1', batch.name)
        self.assertEqual('test_upload.csv', batch.original_filename)
        self.assertEqual(1, batch.batch_size)

        self.assertEqual('test', candidate.label)
        self.assertEqual('http://zemanta.com/test-content-ad', candidate.url)
        self.assertEqual('test content ad', candidate.title)
        self.assertEqual('http://zemanta.com/test-image.jpg', candidate.image_url)
        self.assertEqual('entropy', candidate.image_crop)
        self.assertEqual('https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png', candidate.tracker_urls)
        self.assertEqual('zemanta.com', candidate.display_url)
        self.assertEqual('Zemanta', candidate.brand_name)
        self.assertEqual('description', candidate.description)
        self.assertEqual('Click for more', candidate.call_to_action)

    @patch('utils.lambda_helper.invoke_lambda', MagicMock())
    def test_post_defaults(self):
        ad_group_id = 1
        ad_group_settings = models.AdGroup.objects.get(id=ad_group_id).get_current_settings().copy_settings()
        ad_group_settings.brand_name = 'Default brand name'
        ad_group_settings.save(None)

        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Tracker URLs,Description\n'
            'http://example.com/test-content-ad,test content ad,http://zemanta.com/test-image.jpg,test,entropy,'
            'https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png,description'
        )
        response = _get_client().post(
            reverse('upload_multiple', kwargs={'ad_group_id': ad_group_id}),
            {
                'content_ads': mock_file,
                'batch_name': 'batch 1',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate['errors'] = {
            '__all__': ['Content ad still processing'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'candidates': [expected_candidate],
            }
        }, json.loads(response.content))

        self.assertEqual('batch 1', batch.name)
        self.assertEqual('test_upload.csv', batch.original_filename)
        self.assertEqual(1, batch.batch_size)

        self.assertEqual('test', candidate.label)
        self.assertEqual('http://example.com/test-content-ad', candidate.url)
        self.assertEqual('test content ad', candidate.title)
        self.assertEqual('http://zemanta.com/test-image.jpg', candidate.image_url)
        self.assertEqual('entropy', candidate.image_crop)
        self.assertEqual('https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png', candidate.tracker_urls)
        self.assertEqual('example.com', candidate.display_url)
        self.assertEqual('Default brand name', candidate.brand_name)
        self.assertEqual('description', candidate.description)
        self.assertEqual('Read more', candidate.call_to_action)

    @patch('utils.lambda_helper.invoke_lambda', MagicMock())
    def test_post_errors(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Tracker URLs\n'
            'ahttp://zemanta.com/test-content-ad,test content ad,ahttp://zemanta.com/test-image.jpg,'
            'testtoolonglabelforthecontentadcandidatelabelfield,entropy,'
            'http://t.zemanta.com/px1.png https://t.zemanta.com/px2.png'
        )
        response = _get_client().post(
            reverse('upload_multiple', kwargs={'ad_group_id': ad_group_id}),
            {
                'content_ads': mock_file,
                'batch_name': 'batch 1',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate['errors'] = {
            '__all__': ['Content ad still processing'],
            'tracker_urls': ['Impression tracker URLs have to be HTTPS'],
            'image_url': ['Invalid image URL'],
            'url': ['Invalid URL'],
            'description': ['Missing description'],
        }

        self.maxDiff = None
        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'candidates': [expected_candidate],
            }
        }, json.loads(response.content))

    def test_post_permission(self):
        ad_group_id = 1
        response = _get_client(superuser=False).post(
            reverse('upload_multiple', kwargs={'ad_group_id': ad_group_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class UploadStatusTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    def test_pending(self):
        batch_id = 1
        ad_group_id = 2

        candidate = models.ContentAdCandidate.objects.get(ad_group_id=ad_group_id)
        expected_candidate = candidate.to_dict()
        expected_candidate['errors'] = {
            '__all__': ['Content ad still processing'],
        }

        response = _get_client().get(
            reverse('upload_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'candidates': {
                    str(candidate.id): expected_candidate,
                }
            }
        }, json.loads(response.content))

    def test_ok(self):
        batch_id = 2
        ad_group_id = 3

        candidate = models.ContentAdCandidate.objects.get(ad_group_id=ad_group_id)
        expected_candidate = candidate.to_dict()
        expected_candidate['errors'] = {}

        response = _get_client().get(
            reverse('upload_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'candidates': {
                    str(candidate.id): expected_candidate,
                }
            }
        }, json.loads(response.content))

    def test_failed(self):
        batch_id = 3
        ad_group_id = 4

        candidate = models.ContentAdCandidate.objects.get(ad_group_id=ad_group_id, batch_id=batch_id)
        expected_candidate = candidate.to_dict()
        expected_candidate['errors'] = {
            'image_url': ['Image could not be processed'],
            'url': ['Content unreachable'],
        }

        response = _get_client().get(
            reverse('upload_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'candidates': {
                    str(candidate.id): expected_candidate,
                }
            }
        }, json.loads(response.content))

    def test_permission(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client(superuser=False).get(
            reverse('upload_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class UploadSaveTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    @staticmethod
    def _mock_insert_redirects_batch(content_ads):
        return {
            str(content_ad.id): {
                'redirect': {
                    'url': 'http://example.com',
                },
                'redirectid': 'abc123',
            } for content_ad in content_ads
        }

    @patch.object(utils.s3helpers.S3Helper, '__init__', Mock(return_value=None))
    @patch.object(utils.s3helpers.S3Helper, 'put')
    @patch('utils.redirector_helper.insert_redirects_batch')
    def test_ok(self, mock_insert_batch, mock_s3_put):
        mock_insert_batch.side_effect = self._mock_insert_redirects_batch
        batch_id = 2
        ad_group_id = 3

        response = _get_client().post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'num_successful': 1,
                'num_errors': 0,
                'error_report': None,
            }
        }, json.loads(response.content))
        self.assertEqual(
            models.History.objects.filter(
                ad_group=ad_group_id,
                level=constants.HistoryLevel.AD_GROUP,
            ).latest('created_dt').changes_text,
            'Imported batch "batch 2" with 1 content ad.',
        )

    @patch.object(utils.s3helpers.S3Helper, '__init__', Mock(return_value=None))
    @patch.object(utils.s3helpers.S3Helper, 'put')
    @patch('utils.redirector_helper.insert_redirects_batch')
    def test_change_batch_name(self, mock_insert_batch, mock_s3_put):
        mock_insert_batch.side_effect = self._mock_insert_redirects_batch

        batch_id = 2
        ad_group_id = 3

        response = _get_client().post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({
                'batch_name': 'new batch name'
            }),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'num_successful': 1,
                'num_errors': 0,
                'error_report': None,
            }
        }, json.loads(response.content))

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(batch.name, 'new batch name')

    def test_invalid_batch_name(self):
        batch_id = 2
        ad_group_id = 3

        response = _get_client().post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({
                'batch_name': 'new batch name' * 50
            }),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'data': None,
                'error_code': 'ValidationError',
                'errors': {
                    'batch_name': ['Batch name is too long (700/255).'],
                },
                'message': None,
            },
        }, json.loads(response.content))

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(batch.name, 'batch 2')

    @patch.object(utils.s3helpers.S3Helper, '__init__', Mock(return_value=None))
    @patch.object(utils.s3helpers.S3Helper, 'put')
    @patch('utils.redirector_helper.insert_redirects_batch')
    def test_errors(self, mock_insert_batch, mock_s3_put):
        mock_insert_batch.side_effect = self._mock_insert_redirects_batch

        batch_id = 3
        ad_group_id = 4

        response = _get_client().post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'num_successful': 0,
                'num_errors': 1,
                'error_report': reverse('upload_error_report',
                                        kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id})
            }
        }, json.loads(response.content))
        self.assertEqual(
            models.History.objects.filter(
                ad_group=ad_group_id,
            ).latest('created_dt').changes_text,
            'Imported batch "batch 3" with 0 content ads.',
        )

    @patch.object(utils.s3helpers.S3Helper, 'put')
    @patch('utils.redirector_helper.insert_redirects_batch')
    def test_redirector_error(self, mock_insert_batch, mock_s3_put):
        mock_insert_batch.side_effect = Exception()

        batch_id = 2
        ad_group_id = 3

        response = _get_client().post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(500, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'ServerError',
                'message': 'An error occurred.'
            },
        }, json.loads(response.content))
        self.assertEqual(0, models.ContentAd.objects.count())

    def test_invalid_batch_status(self):
        batch_id = 4
        ad_group_id = 5

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

        response = _get_client().post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'data': None,
                'error_code': 'ValidationError',
                'errors': None,
                'message': 'Invalid batch status'
            }
        }, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

    def test_invalid_batch_id(self):
        batch_id = 1
        ad_group_id = 1

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Upload batch does not exist',
            }
        }, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

    def test_permission(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client(superuser=False).post(
            reverse('upload_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            json.dumps({}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class CandidatesDownloadTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    def test_valid(self):
        batch_id = 1
        ad_group_id = 2

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().get(
            reverse('upload_candidates_download', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual('Url,Title,Image url,Display url,Brand name,Description,Call to action,'
                         'Label,Image crop,Primary tracker url,Secondary tracker url\r\nhttp://zemanta.com/blog,'
                         'Zemanta blog čšž,http://zemanta.com/img.jpg,zemanta.com,Zemanta,Zemanta blog,Read more,'
                         'content ad 1,entropy,,\r\n', response.content)
        self.assertEqual('attachment; filename="batch 1.csv"', response.get('Content-Disposition'))

    def test_custom_batch_name(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client().get(
            reverse('upload_candidates_download', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            {'batch_name': 'Another batch'},
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual('attachment; filename="Another batch.csv"', response.get('Content-Disposition'))

    def test_wrong_batch_id(self):
        batch_id = 1
        ad_group_id = 1

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().get(
            reverse('upload_candidates_download', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Upload batch does not exist',
            }
        }, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

    def test_permission(self):
        batch_id = 1
        ad_group_id = 2

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client(superuser=False).get(
            reverse('upload_candidates_download', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)


class UploadCancelTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    def test_valid(self):
        batch_id = 1
        ad_group_id = 2

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().post(
            reverse('upload_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
        }, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.CANCELLED, batch.status)

    def test_invalid(self):
        batch_id = 1
        ad_group_id = 2

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        batch.status = constants.UploadBatchStatus.DONE
        batch.save()

        response = _get_client().post(
            reverse('upload_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'data': None,
                'error_code': 'ValidationError',
                'errors': {
                    'cancel': 'Cancel action unsupported at this stage',
                },
                'message': None,
            }
        }, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

    def test_wrong_batch_id(self):
        batch_id = 1
        ad_group_id = 1

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().post(
            reverse('upload_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Upload batch does not exist',
            }
        }, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

    def test_permission(self):
        batch_id = 1
        ad_group_id = 2

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client(superuser=False).post(
            reverse('upload_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)


class UploadErrorReport(TestCase):

    fixtures = ['test_upload.yaml']

    @patch.object(utils.s3helpers.S3Helper, '__init__', Mock(return_value=None))
    @patch.object(utils.s3helpers.S3Helper, 'get')
    def test_existing(self, mock_s3_get):
        mock_s3_get.return_value = 'url,title,image_url,tracker_urls,display_url,brand_name,description,'\
                                   'call_to_action,label,image_crop,errors\r\nhttp://zemanta.com/blog,Zemanta blog,'\
                                   'http://zemanta.com/img.jpg,,zemanta.com,Zemanta,Zemanta blog,Read more,'\
                                   'content ad 1,entropy,"Content unreachable., Image could not be processed."\r\n'
        batch_id = 4
        ad_group_id = 5

        response = _get_client().get(
            reverse('upload_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(mock_s3_get.return_value, response.content)

    @patch.object(utils.s3helpers.S3Helper, '__init__', Mock(return_value=None))
    @patch.object(utils.s3helpers.S3Helper, 'get')
    def test_non_existing(self, mock_s3_get):
        mock_s3_get.side_effect = boto.exception.S3ResponseError(status=404, reason='')

        batch_id = 4
        ad_group_id = 5

        response = _get_client().get(
            reverse('upload_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Error report does not exist',
            }
        }, json.loads(response.content))

    def test_wrong_batch_id(self):
        batch_id = 4
        ad_group_id = 1

        response = _get_client().get(
            reverse('upload_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Upload batch does not exist',
            }
        }, json.loads(response.content))

    def test_permission(self):
        batch_id = 4
        ad_group_id = 5

        response = _get_client(superuser=False).get(
            reverse('upload_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class CandidateTest(TestCase):

    fixtures = ['test_upload.yaml']

    def test_update_candidate(self):
        batch_id = 5
        ad_group_id = 4
        candidate_id = 4

        resource = {
            'candidate': {
                'id': 4,
                'label': 'new label',
                'url': 'http://zemanta.com/blog',
                'title': 'New title',
                'image_url': 'http://zemanta.com/img.jpg',
                'image_crop': 'center',
                'display_url': 'newurl.com',
                'brand_name': 'New brand name',
                'description': 'New description',
                'call_to_action': 'New cta',
                'primary_tracker_url': '',
                'secondary_tracker_url': '',
            },
            'defaults': [],
        }

        response = _get_client().put(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            json.dumps(resource),
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        self.maxDiff = None
        response = json.loads(response.content)
        expected = {
            'data': {
                'candidates': [{
                    'brand_name':
                    'BranName',
                    'call_to_action': 'Contact us',
                    'description': 'Custom description',
                    'display_url': 'yourbrand.com',
                    'errors': {'__all__': ['Content ad still processing']},
                    'hosted_image_url': None,
                    'id': 5,
                    'image_crop': 'faces',
                    'image_hash': None,
                    'image_height': None,
                    'image_id': None,
                    'image_status': 2,
                    'image_url': 'http://zemanta.com/img1.jpg',
                    'image_width': None,
                    'label': 'content ad 1',
                    'primary_tracker_url': None,
                    'secondary_tracker_url': None,
                    'title': u'Zemanta blog čšž 1',
                    'tracker_urls': '',
                    'url': 'http://zemanta.com/blog1',
                    'url_status': 2
                }, {
                    'brand_name': 'New brand name',
                    'call_to_action': 'New cta',
                    'description': 'New description',
                    'display_url': 'newurl.com',
                    'errors': {},
                    'hosted_image_url': '/abc12345.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                    'id': 4,
                    'image_crop': 'center',
                    'image_hash': '54321cba',
                    'image_height': 500,
                    'image_id': 'abc12345',
                    'image_status': 3,
                    'image_url': 'http://zemanta.com/img.jpg',
                    'image_width': 500,
                    'label': 'new label',
                    'primary_tracker_url': '',
                    'secondary_tracker_url': '',
                    'title': 'New title',
                    'tracker_urls': '',
                    'url': 'http://zemanta.com/blog',
                    'url_status': 3
                }]},
            'success': True}
        self.assertEqual(expected, response)

    def test_delete_candidate(self):
        batch_id = 5
        ad_group_id = 4
        candidate_id = 4

        response = _get_client().delete(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
        }, json.loads(response.content))

        with self.assertRaises(models.ContentAdCandidate.DoesNotExist):
            models.ContentAdCandidate.objects.get(id=candidate_id)

    def test_non_existing_candidate(self):
        batch_id = 5
        ad_group_id = 4
        candidate_id = 555

        resource = {
            'candidate': {
                'id': 555,
                'label': 'new label',
                'url': 'http://zemanta.com/blog',
                'title': 'New title',
                'image_url': 'http://zemanta.com/img.jpg',
                'image_crop': 'center',
                'display_url': 'newurl.com',
                'brand_name': 'New brand name',
                'description': 'New description',
                'call_to_action': 'New cta',
                'primary_tracker_url': '',
                'secondary_tracker_url': '',
            },
            'defaults': [],
        }

        response = _get_client().put(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            json.dumps(resource),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Candidate does not exist',
            }
        }, json.loads(response.content))

    def test_delete_non_existing_candidate(self):
        batch_id = 5
        ad_group_id = 4
        candidate_id = 555

        response = _get_client().delete(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Candidate does not exist',
            }
        }, json.loads(response.content))

    def test_wrong_batch_id(self):
        batch_id = 4
        ad_group_id = 1
        candidate_id = 4

        response = _get_client().put(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Upload batch does not exist',
            }
        }, json.loads(response.content))

    def test_delete_wrong_batch_id(self):
        batch_id = 4
        ad_group_id = 1
        candidate_id = 4

        response = _get_client().delete(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': 'Upload batch does not exist',
            }
        }, json.loads(response.content))

    def test_permission(self):
        batch_id = 4
        ad_group_id = 5
        candidate_id = 4

        response = _get_client(superuser=False).put(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')

    def test_delete_permission(self):
        batch_id = 4
        ad_group_id = 5
        candidate_id = 4

        response = _get_client(superuser=False).delete(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')
