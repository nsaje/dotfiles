# -*- coding: utf-8 -*-
import json

from mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from dash import constants
from dash import models
from zemauth.models import User


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

    @patch('utils.lambda_helper.invoke_lambda', MagicMock())
    def test_post(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Primary impression tracker url,Secondary impression tracker url,Brand name,Display URL,'
            'Call to Action,Description\nhttp://zemanta.com/test-content-ad,test content ad,'
            'http://zemanta.com/test-image.jpg,test,entropy,https://t.zemanta.com/px1.png,'
            'https://t.zemanta.com/px2.png,Zemanta,zemanta.com,Click for more,description'
        )
        response = _get_client().post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            {
                'candidates': mock_file,
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
                'batch_name': 'batch 1',
                'candidates': [expected_candidate],
            }
        }, json.loads(response.content))

        self.assertEqual('batch 1', batch.name)
        self.assertEqual('test_upload.csv', batch.original_filename)

        self.assertEqual('test', candidate.label)
        self.assertEqual('http://zemanta.com/test-content-ad', candidate.url)
        self.assertEqual('test content ad', candidate.title)
        self.assertEqual('http://zemanta.com/test-image.jpg', candidate.image_url)
        self.assertEqual('entropy', candidate.image_crop)
        self.assertEqual('https://t.zemanta.com/px1.png', candidate.primary_tracker_url)
        self.assertEqual('https://t.zemanta.com/px2.png', candidate.secondary_tracker_url)
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
            'URL,Title,Image URL,Label,Image Crop,Primary impression tracker url,'
            'Secondary impression tracker url,Description,Display URL,brand name\nhttp://example.com/test-content-ad,'
            'test content ad,http://zemanta.com/test-image.jpg,test,entropy,https://t.zemanta.com/px1.png,'
            'https://t.zemanta.com/px2.png,description,example.com,Example'
        )
        response = _get_client().post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            {
                'candidates': mock_file,
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
                'batch_name': 'batch 1',
                'candidates': [expected_candidate],
            }
        }, json.loads(response.content))

        self.assertEqual('batch 1', batch.name)
        self.assertEqual('test_upload.csv', batch.original_filename)

        self.assertEqual('test', candidate.label)
        self.assertEqual('http://example.com/test-content-ad', candidate.url)
        self.assertEqual('test content ad', candidate.title)
        self.assertEqual('http://zemanta.com/test-image.jpg', candidate.image_url)
        self.assertEqual('entropy', candidate.image_crop)
        self.assertEqual('https://t.zemanta.com/px1.png', candidate.primary_tracker_url)
        self.assertEqual('https://t.zemanta.com/px2.png', candidate.secondary_tracker_url)
        self.assertEqual('example.com', candidate.display_url)
        self.assertEqual('Example', candidate.brand_name)
        self.assertEqual('description', candidate.description)
        self.assertEqual('Read more', candidate.call_to_action)

    @patch('utils.lambda_helper.invoke_lambda', MagicMock())
    def test_post_errors(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            'test_upload.csv',
            'URL,Title,Image URL,Label,Image Crop,Primary impression tracker url,Secondary impression tracker url\n'
            'ahttp://zemanta.com/test-content-ad,test content ad,ahttp://zemanta.com/test-image.jpg,'
            'testtoolonglabelforthecontentadcandidatelabelfield,entropy,'
            'http://t.zemanta.com/px1.png,https://t.zemanta.com/px2.png'
        )
        response = _get_client().post(
            reverse('upload_csv', kwargs={'ad_group_id': ad_group_id}),
            {
                'candidates': mock_file,
                'batch_name': 'batch 1',
            },
            follow=True
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate['errors'] = {
            '__all__': ['Content ad still processing'],
            'description': ['Missing description'],
            'primary_tracker_url': ['Impression tracker URLs have to be HTTPS'],
            'image_url': ['Invalid image URL'],
            'display_url': ['Missing display URL'],
            'url': ['Invalid URL'],
            'brand_name': ['Missing brand name'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual({
            'success': True,
            'data': {
                'batch_id': batch.id,
                'batch_name': 'batch 1',
                'candidates': [expected_candidate],
            }
        }, json.loads(response.content))


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


class UploadSaveTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    @staticmethod
    def _mock_insert_redirects(content_ads):
        return {
            str(content_ad.id): {
                'redirect': {
                    'url': 'http://example.com',
                },
                'redirectid': 'abc123',
            } for content_ad in content_ads
        }

    @patch('utils.redirector_helper.insert_redirects')
    def test_ok(self, mock_insert_batch):
        mock_insert_batch.side_effect = self._mock_insert_redirects
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
            }
        }, json.loads(response.content))
        self.assertEqual(
            models.History.objects.filter(
                ad_group=ad_group_id,
                level=constants.HistoryLevel.AD_GROUP,
            ).latest('created_dt').changes_text,
            'Imported batch "batch 2" with 1 content ad.',
        )

    @patch('utils.redirector_helper.insert_redirects')
    def test_change_batch_name(self, mock_insert_batch):
        mock_insert_batch.side_effect = self._mock_insert_redirects

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

    @patch('utils.redirector_helper.insert_redirects')
    def test_errors(self, mock_insert_batch):
        mock_insert_batch.side_effect = self._mock_insert_redirects

        batch_id = 3
        ad_group_id = 4

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
                'message': 'Save not permitted - candidate errors exist'
            }
        }, json.loads(response.content))

    @patch('utils.redirector_helper.insert_redirects')
    def test_redirector_error(self, mock_insert_batch):
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
        self.assertEqual(0, models.ContentAd.objects.filter(ad_group_id=ad_group_id).count())

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
        self.assertEqual(
            'URL,Title,Image URL,Display URL,Brand name,Description,Call to action,'
            'Label,Image crop,Primary impression tracker URL,Secondary impression'
            ' tracker URL\r\nhttp://zemanta.com/blog,Zemanta blog čšž,'
            'http://zemanta.com/img.jpg,zemanta.com,Zemanta,Zemanta blog,Read more,'
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


class UploadBatchTest(TestCase):

    fixtures = ['test_upload.yaml']

    def test_create_empty_batch(self):
        ad_group_id = 1
        batch_name = 'test'

        response = _get_client().post(
            reverse('upload_batch', kwargs={'ad_group_id': ad_group_id}),
            json.dumps({'batch_name': batch_name}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        batch = models.UploadBatch.objects.latest('created_dt')
        new_candidate = batch.contentadcandidate_set.get()

        response = json.loads(response.content)
        self.assertEqual({
            'data': {
                'batch_id': batch.id,
                'batch_name': batch_name,
                'candidates': [
                    new_candidate.to_dict(),
                ],
            },
            'success': True,
        }, response)

    def test_create_empty_batch_invalid_batch_name(self):
        ad_group_id = 1
        batch_name = ''

        response = _get_client().post(
            reverse('upload_batch', kwargs={'ad_group_id': ad_group_id}),
            json.dumps({'batch_name': batch_name}),
            content_type='application/json',
            follow=True,
        )
        self.assertEqual(400, response.status_code)


class CandidateTest(TestCase):

    fixtures = ['test_upload.yaml']

    def test_get_candidate(self):
        batch_id = 1
        ad_group_id = 2
        candidate_id = 1

        response = _get_client().get(
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
        self.assertEqual(400, response.status_code)

    def test_get_candidate_list(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client().get(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                }
            ),
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        response = json.loads(response.content)
        self.assertEqual({
            u'data': {
                u'candidates': [{
                    u'id': 1,
                    u'label': u'content ad 1',
                    u'url': u'http://zemanta.com/blog',
                    u'title': u'Zemanta blog čšž',
                    u'image_url': u'http://zemanta.com/img.jpg',
                    u'image_crop': u'entropy',
                    u'display_url': u'zemanta.com',
                    u'brand_name': u'Zemanta',
                    u'description': u'Zemanta blog',
                    u'call_to_action': u'Read more',
                    u'errors': {
                        u'__all__': [u'Content ad still processing'],
                    },
                    u'hosted_image_url': None,
                    u'image_height': None,
                    u'image_width': None,
                    u'image_id': None,
                    u'image_hash': None,
                    u'image_status': constants.AsyncUploadJobStatus.PENDING_START,
                    u'url_status': constants.AsyncUploadJobStatus.PENDING_START,
                    u'primary_tracker_url': None,
                    u'secondary_tracker_url': None,
                }]
            },
            u'success': True,
        }, response)

    def test_add_candidate(self):
        batch_id = 1
        ad_group_id = 2

        response = _get_client().post(
            reverse(
                'upload_candidate',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                }
            ),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        response = json.loads(response.content)
        candidate = models.ContentAdCandidate.objects.latest('created_dt')

        self.assertEqual({
            'data': {
                'candidate': {
                    'id': candidate.id,
                    'label': '',
                    'url': '',
                    'title': '',
                    'image_url': None,
                    'image_crop': constants.ImageCrop.CENTER,
                    'display_url': '',
                    'brand_name': '',
                    'description': '',
                    'call_to_action': constants.DEFAULT_CALL_TO_ACTION,
                    'primary_tracker_url': None,
                    'secondary_tracker_url': None,
                    'image_hash': None,
                    'image_height': None,
                    'image_width': None,
                    'image_id': None,
                    'image_status': constants.AsyncUploadJobStatus.PENDING_START,
                    'url_status': constants.AsyncUploadJobStatus.PENDING_START,
                    'hosted_image_url': None,
                }
            },
            'success': True,
        }, response)

    def test_add_candidate_with_id(self):
        batch_id = 1
        ad_group_id = 2
        candidate_id = 1

        response = _get_client().post(
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
        self.assertEqual(400, response.status_code)

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


class CandidateUpdateTest(TestCase):

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

        response = _get_client().post(
            reverse(
                'upload_candidate_update',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            {'data': json.dumps(resource)},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        response = json.loads(response.content)
        expected = {
            u'data': {
                u'updated_fields': {
                    u'brand_name': u'New brand name',
                    u'call_to_action': u'New cta',
                    u'description': u'New description',
                    u'display_url': u'newurl.com',
                    u'image_crop': u'center',
                    u'image_url': u'http://zemanta.com/img.jpg',
                    u'label': u'new label',
                    u'primary_tracker_url': u'',
                    u'secondary_tracker_url': u'',
                    u'title': u'New title',
                    u'url': u'http://zemanta.com/blog',
                },
                u'errors': {},
            },
            u'success': True}
        self.assertEqual(expected, response)

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

        response = _get_client().post(
            reverse(
                'upload_candidate_update',
                kwargs={
                    'ad_group_id': ad_group_id,
                    'batch_id': batch_id,
                    'candidate_id': candidate_id
                }
            ),
            {'data': json.dumps(resource)},
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

        response = _get_client().post(
            reverse(
                'upload_candidate_update',
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
