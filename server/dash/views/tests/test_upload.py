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

    fixtures = ['test_upload_plus.yaml']

    def test_get(self):
        ad_group_id = 1
        response = _get_client().get(
            reverse('upload_plus_csv', kwargs={'ad_group_id': ad_group_id}),
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
            reverse('upload_plus_csv', kwargs={'ad_group_id': ad_group_id}),
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
            reverse('upload_plus_csv', kwargs={'ad_group_id': ad_group_id}),
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
            reverse('upload_plus_csv', kwargs={'ad_group_id': ad_group_id}),
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
            reverse('upload_plus_csv', kwargs={'ad_group_id': ad_group_id}),
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
            reverse('upload_plus_csv', kwargs={'ad_group_id': ad_group_id}),
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
                        'label': ['Label too long (max 25 characters)'],
                    }
                },
            }
        }, json.loads(response.content))

    def test_post_permission(self):
        ad_group_id = 1
        response = _get_client(superuser=False).post(
            reverse('upload_plus_csv', kwargs={'ad_group_id': ad_group_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class UploadMultipleTestCase(TestCase):

    fixtures = ['test_upload_plus.yaml']

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
            reverse('upload_plus_multiple', kwargs={'ad_group_id': ad_group_id}),
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
            reverse('upload_plus_multiple', kwargs={'ad_group_id': ad_group_id}),
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
            reverse('upload_plus_multiple', kwargs={'ad_group_id': ad_group_id}),
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
            'label': ['Label too long (max 25 characters)'],
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
            reverse('upload_plus_multiple', kwargs={'ad_group_id': ad_group_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class UploadStatusTestCase(TestCase):

    fixtures = ['test_upload_plus.yaml']

    def test_pending(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client().get(
            reverse('upload_plus_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'candidates': {
                    '1': {
                        'image_status': constants.AsyncUploadJobStatus.PENDING_START,
                        'url_status': constants.AsyncUploadJobStatus.PENDING_START,
                    }
                }
            }
        }, json.loads(response.content))

    def test_ok(self):
        batch_id = 2
        ad_group_id = 3

        response = _get_client().get(
            reverse('upload_plus_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'candidates': {
                    '2': {
                        'image_status': constants.AsyncUploadJobStatus.OK,
                        'url_status': constants.AsyncUploadJobStatus.OK,
                    }
                }
            }
        }, json.loads(response.content))

    def test_failed(self):
        batch_id = 3
        ad_group_id = 4

        response = _get_client().get(
            reverse('upload_plus_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'candidates': {
                    '3': {
                        'image_status': constants.AsyncUploadJobStatus.FAILED,
                        'url_status': constants.AsyncUploadJobStatus.FAILED,
                    }
                }
            }
        }, json.loads(response.content))

    def test_permission(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client(superuser=False).get(
            reverse('upload_plus_status', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class UploadSaveTestCase(TestCase):

    fixtures = ['test_upload_plus.yaml']

    @patch.object(utils.s3helpers.S3Helper, '__init__', Mock(return_value=None))
    @patch.object(utils.s3helpers.S3Helper, 'put')
    @patch('utils.redirector_helper.insert_redirect')
    def test_ok(self, mock_insert_redirect, mock_s3_put):
        mock_insert_redirect.return_value = {
            'redirect': {
                'url': 'http://example.com',
            },
            'redirectid': 'abc123',
        }
        batch_id = 2
        ad_group_id = 3

        response = _get_client().post(
            reverse('upload_plus_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
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
    def test_errors(self, mock_s3_put):
        batch_id = 3
        ad_group_id = 4

        response = _get_client().post(
            reverse('upload_plus_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'success': True,
            'data': {
                'num_errors': 1,
                'error_report': reverse('upload_plus_error_report',
                                        kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id})
            }
        }, json.loads(response.content))
        self.assertEqual(
            models.History.objects.filter(
                ad_group=ad_group_id,
                type=constants.HistoryType.AD_GROUP,
            ).latest('created_dt').changes_text,
            'Imported batch "batch 3" with 0 content ads.',
        )

    @patch.object(utils.s3helpers.S3Helper, 'put')
    @patch('utils.redirector_helper.insert_redirect')
    def test_redirector_error(self, mock_insert_redirect, mock_s3_put):
        mock_insert_redirect.side_effect = Exception()

        batch_id = 2
        ad_group_id = 3

        response = _get_client().post(
            reverse('upload_plus_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
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
            reverse('upload_plus_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
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
            reverse('upload_plus_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': None,
            }
        }, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

    def test_permission(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client(superuser=False).post(
            reverse('upload_plus_save', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')


class UploadCancelTestCase(TestCase):

    fixtures = ['test_upload_plus.yaml']

    def test_valid(self):
        batch_id = 1
        ad_group_id = 2

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().post(
            reverse('upload_plus_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
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
            reverse('upload_plus_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
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
            reverse('upload_plus_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': None,
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
            reverse('upload_plus_cancel', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)


class UploadErrorReport(TestCase):

    fixtures = ['test_upload_plus.yaml']

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
            reverse('upload_plus_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
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
            reverse('upload_plus_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': None,
            }
        }, json.loads(response.content))

    def test_wrong_batch_id(self):
        batch_id = 4
        ad_group_id = 1

        response = _get_client().get(
            reverse('upload_plus_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual({
            'success': False,
            'data': {
                'error_code': 'MissingDataError',
                'message': None,
            }
        }, json.loads(response.content))

    def test_permission(self):
        batch_id = 4
        ad_group_id = 5

        response = _get_client(superuser=False).get(
            reverse('upload_plus_error_report', kwargs={'ad_group_id': ad_group_id, 'batch_id': batch_id}),
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')
