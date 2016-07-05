# -*- coding: utf-8 -*-
from mock import patch
from django.test import TestCase, override_settings

from dash import constants
from dash import models
from dash import upload

import utils.s3helpers

valid_candidate = {
    'label': 'test',
    'url': 'http://zemanta.com/test-content-ad',
    'title': 'test content ad',
    'image_url': 'http://zemanta.com/test-image.jpg',
    'image_crop': 'faces',
    'display_url': 'zemanta.com',
    'brand_name': 'zemanta',
    'description': 'zemanta content ad',
    'call_to_action': 'read more',
    'primary_tracker_url': 'https://example.com/px1.png',
    'secondary_tracker_url': 'https://example.com/px2.png',
}

invalid_candidate = {
    'label': 'repeat' * 21,
    'url': 'ftp://zemanta.com/test-content-ad',
    'image_url': 'file://zemanta.com/test-image.jpg',
    'image_crop': 'landscape',
    'display_url': 'zemanta.com' * 10,
    'primary_tracker_url': 'http://example.com/px1.png',
    'secondary_tracker_url': 'http://example.com/px2.png',
}


class InsertCandidatesTestCase(TestCase):
    fixtures = ['test_upload.yaml']

    def test_insert_candidates(self):
        data = [valid_candidate]

        ad_group = models.AdGroup.objects.get(id=1)
        batch_name = 'batch1'
        filename = 'test_upload.csv'
        self.assertEqual(0, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        upload.insert_candidates(data, ad_group, batch_name, filename)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(filename, batch.original_filename)

        candidate = models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual(valid_candidate['label'], candidate.label)
        self.assertEqual(valid_candidate['url'], candidate.url)
        self.assertEqual(valid_candidate['title'], candidate.title)
        self.assertEqual(valid_candidate['image_url'], candidate.image_url)
        self.assertEqual(valid_candidate['image_crop'], candidate.image_crop)
        self.assertEqual(valid_candidate['display_url'], candidate.display_url)
        self.assertEqual(valid_candidate['brand_name'], candidate.brand_name)
        self.assertEqual(valid_candidate['description'], candidate.description)
        self.assertEqual(valid_candidate['call_to_action'], candidate.call_to_action)
        self.assertEqual(valid_candidate['primary_tracker_url'], candidate.primary_tracker_url)
        self.assertEqual(valid_candidate['secondary_tracker_url'], candidate.secondary_tracker_url)

    def test_empty_candidate(self):
        data = [{}]

        ad_group = models.AdGroup.objects.get(id=1)
        batch_name = 'batch1'
        filename = 'test_upload.csv'
        self.assertEqual(0, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        upload.insert_candidates(data, ad_group, batch_name, filename)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(filename, batch.original_filename)

        candidate = models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual('', candidate.label)
        self.assertEqual('', candidate.url)
        self.assertEqual('', candidate.title)
        self.assertEqual('', candidate.image_url)
        self.assertEqual('center', candidate.image_crop)
        self.assertEqual('', candidate.display_url)
        self.assertEqual('Example', candidate.brand_name)
        self.assertEqual('', candidate.description)
        self.assertEqual('Read more', candidate.call_to_action)
        self.assertEqual('', candidate.primary_tracker_url)
        self.assertEqual('', candidate.secondary_tracker_url)


class PersistCandidatesTestCase(TestCase):
    fixtures = ['test_upload.yaml']

    @patch.object(utils.s3helpers.S3Helper, 'put')
    def test_valid_candidates(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=2)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        candidate = batch.contentadcandidate_set.get()

        upload.persist_candidates(batch)
        self.assertEqual(0, batch.contentadcandidate_set.count())
        self.assertEqual(1, batch.contentad_set.count())
        self.assertFalse(mock_s3helper_put.called)

        content_ad = batch.contentad_set.get()

        self.assertEqual(candidate.label, content_ad.label)
        self.assertEqual(candidate.url, content_ad.url)
        self.assertEqual(candidate.title, content_ad.title)
        self.assertEqual(candidate.display_url, content_ad.display_url)
        self.assertEqual(candidate.description, content_ad.description)
        self.assertEqual(candidate.brand_name, content_ad.brand_name)
        self.assertEqual(candidate.call_to_action, content_ad.call_to_action)
        self.assertEqual([candidate.primary_tracker_url, candidate.secondary_tracker_url], content_ad.tracker_urls)
        self.assertEqual(candidate.image_id, content_ad.image_id)
        self.assertEqual(candidate.image_width, content_ad.image_width)
        self.assertEqual(candidate.image_height, content_ad.image_height)
        self.assertEqual(candidate.image_hash, content_ad.image_hash)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

    @patch.object(utils.s3helpers.S3Helper, 'put')
    def test_invalid_candidates(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=3)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        with self.assertRaises(upload.CandidateErrorsRemaining):
            upload.persist_candidates(batch)

        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

    @patch.object(utils.s3helpers.S3Helper, 'put')
    def test_invalid_batch_status(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=2)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        batch.status = constants.UploadBatchStatus.CANCELLED
        batch.save()

        with self.assertRaises(upload.InvalidBatchStatus):
            upload.persist_candidates(batch)

        # check that nothing changed
        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.CANCELLED, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())
        self.assertFalse(mock_s3helper_put.called)


class CancelUploadTestCase(TestCase):
    fixtures = ['test_upload.yaml']

    def test_cancel(self):
        ad_group = models.AdGroup.objects.get(id=2)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())

        upload.cancel_upload(batch)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.CANCELLED, batch.status)
        self.assertEqual(0, batch.contentadcandidate_set.count())

    def test_invalid_status(self):
        ad_group = models.AdGroup.objects.get(id=2)
        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()

        batch.status = constants.UploadBatchStatus.DONE
        batch.save()

        with self.assertRaises(upload.InvalidBatchStatus):
            upload.cancel_upload(batch)


class GetCandidatesWithErrorsTestCase(TestCase):
    fixtures = ['test_upload.yaml']

    def test_valid_candidate(self):
        data = [valid_candidate]

        # prepare candidate
        ad_group = models.AdGroup.objects.get(id=1)
        batch, candidates = upload.insert_candidates(data, ad_group, 'batch1', 'test_upload.csv')

        result = upload.get_candidates_with_errors(candidates)
        self.assertEqual([{
            'label': 'test',
            'url': 'http://zemanta.com/test-content-ad',
            'title': 'test content ad',
            'image_url': 'http://zemanta.com/test-image.jpg',
            'image_crop': 'faces',
            'display_url': 'zemanta.com',
            'brand_name': 'zemanta',
            'description': 'zemanta content ad',
            'call_to_action': 'read more',
            'primary_tracker_url': 'https://example.com/px1.png',
            'secondary_tracker_url': 'https://example.com/px2.png',
            'hosted_image_url': None,
            'image_hash': None,
            'errors': {
                '__all__': ['Content ad still processing'],
            },
            'image_width': None,
            'label': 'test',
            'image_id': None,
            'image_height': None,
            'url_status': 1,
            'image_status': 1,
            'id': candidates[0].id,
        }], result)

    def test_invalid_candidate(self):
        data = [invalid_candidate]

        # prepare candidate
        ad_group = models.AdGroup.objects.get(id=1)
        batch, candidates = upload.insert_candidates(data, ad_group, 'batch1', 'test_upload.csv')

        self.maxDiff = None
        result = upload.get_candidates_with_errors(candidates)
        self.assertEqual([{
            'hosted_image_url': None,
            'image_crop': 'landscape',
            'primary_tracker_url': 'http://example.com/px1.png',
            'image_hash': None,
            'description': '',
            'call_to_action': 'Read more',
            'title': '',
            'url': 'ftp://zemanta.com/test-content-ad',
            'errors': {
                'image_crop': [u'Choose a valid image crop'],
                'description': [u'Missing description'],
                '__all__': [u'Content ad still processing'],
                'title': [u'Missing title'],
                'url': [u'Invalid URL'],
                'display_url': [u'Display URL too long (max 25 characters)'],
                'label': [u'Label too long (max 100 characters)'],
                'image_url': [u'Invalid image URL'],
                'primary_tracker_url': [u'Impression tracker URLs have to be HTTPS'],
                'secondary_tracker_url': [u'Impression tracker URLs have to be HTTPS'],
            },
            'display_url': 'zemanta.comzemanta.comzemanta.comzemanta.comzemanta.com'
                           'zemanta.comzemanta.comzemanta.comzemanta.comzemanta.com',
            'brand_name': 'Example',
            'image_width': None,
            'label': 'repeat'  * 21,
            'image_id': None,
            'image_height': None,
            'image_url': 'file://zemanta.com/test-image.jpg',
            'url_status': 1,
            'image_status': 1,
            'secondary_tracker_url': 'http://example.com/px2.png',
            'id': candidates[0].id,
        }], result)


class UpdateCandidateTest(TestCase):

    fixtures = ['test_upload.yaml']

    def setUp(self):
        candidate_id = 4
        self.candidate = models.ContentAdCandidate.objects.get(id=candidate_id)
        self.other_candidate = self.candidate.batch.contentadcandidate_set.exclude(id=candidate_id).get()
        self.new_candidate = {
            'id': candidate_id,
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
        }
        self.defaults = ['image_crop', 'display_url', 'brand_name', 'description', 'call_to_action']

    def test_update_candidate(self):
        upload.update_candidate(self.new_candidate, [], self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.label, self.new_candidate['label'])
        self.assertEqual(self.candidate.url, self.new_candidate['url'])
        self.assertEqual(self.candidate.title, self.new_candidate['title'])
        self.assertEqual(self.candidate.image_url, self.new_candidate['image_url'])
        self.assertEqual(self.candidate.image_crop, self.new_candidate['image_crop'])
        self.assertEqual(self.candidate.display_url, self.new_candidate['display_url'])
        self.assertEqual(self.candidate.brand_name, self.new_candidate['brand_name'])
        self.assertEqual(self.candidate.description, self.new_candidate['description'])
        self.assertEqual(self.candidate.call_to_action, self.new_candidate['call_to_action'])
        self.assertEqual(self.candidate.primary_tracker_url, self.new_candidate['primary_tracker_url'])
        self.assertEqual(self.candidate.secondary_tracker_url, self.new_candidate['secondary_tracker_url'])

        self.other_candidate.refresh_from_db()
        self.assertNotEqual(self.other_candidate.image_crop, self.new_candidate['image_crop'])
        self.assertNotEqual(self.other_candidate.display_url, self.new_candidate['display_url'])
        self.assertNotEqual(self.other_candidate.brand_name, self.new_candidate['brand_name'])
        self.assertNotEqual(self.other_candidate.description, self.new_candidate['description'])
        self.assertNotEqual(self.other_candidate.call_to_action, self.new_candidate['call_to_action'])

    def test_update_with_defaults(self):
        upload.update_candidate(self.new_candidate, self.defaults, self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.label, self.new_candidate['label'])
        self.assertEqual(self.candidate.url, self.new_candidate['url'])
        self.assertEqual(self.candidate.title, self.new_candidate['title'])
        self.assertEqual(self.candidate.image_url, self.new_candidate['image_url'])
        self.assertEqual(self.candidate.image_crop, self.new_candidate['image_crop'])
        self.assertEqual(self.candidate.display_url, self.new_candidate['display_url'])
        self.assertEqual(self.candidate.brand_name, self.new_candidate['brand_name'])
        self.assertEqual(self.candidate.description, self.new_candidate['description'])
        self.assertEqual(self.candidate.call_to_action, self.new_candidate['call_to_action'])
        self.assertEqual(self.candidate.primary_tracker_url, self.new_candidate['primary_tracker_url'])
        self.assertEqual(self.candidate.secondary_tracker_url, self.new_candidate['secondary_tracker_url'])

        self.other_candidate.refresh_from_db()
        self.assertEqual(self.other_candidate.image_crop, self.new_candidate['image_crop'])
        self.assertEqual(self.other_candidate.display_url, self.new_candidate['display_url'])
        self.assertEqual(self.other_candidate.brand_name, self.new_candidate['brand_name'])
        self.assertEqual(self.other_candidate.description, self.new_candidate['description'])
        self.assertEqual(self.other_candidate.call_to_action, self.new_candidate['call_to_action'])

    def test_unknown_defaults(self):
        defaults = ['title', 'url', 'label', 'image_url', 'primary_tracker_url', 'secondary_tracker_url']
        upload.update_candidate(self.new_candidate, defaults, self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.label, self.new_candidate['label'])
        self.assertEqual(self.candidate.url, self.new_candidate['url'])
        self.assertEqual(self.candidate.title, self.new_candidate['title'])
        self.assertEqual(self.candidate.image_url, self.new_candidate['image_url'])
        self.assertEqual(self.candidate.image_crop, self.new_candidate['image_crop'])
        self.assertEqual(self.candidate.display_url, self.new_candidate['display_url'])
        self.assertEqual(self.candidate.brand_name, self.new_candidate['brand_name'])
        self.assertEqual(self.candidate.description, self.new_candidate['description'])
        self.assertEqual(self.candidate.call_to_action, self.new_candidate['call_to_action'])
        self.assertEqual(self.candidate.primary_tracker_url, self.new_candidate['primary_tracker_url'])
        self.assertEqual(self.candidate.secondary_tracker_url, self.new_candidate['secondary_tracker_url'])

        self.other_candidate.refresh_from_db()
        self.assertNotEqual(self.other_candidate.label, self.new_candidate['label'])
        self.assertNotEqual(self.other_candidate.url, self.new_candidate['url'])
        self.assertNotEqual(self.other_candidate.title, self.new_candidate['title'])
        self.assertNotEqual(self.other_candidate.image_url, self.new_candidate['image_url'])
        self.assertNotEqual(self.other_candidate.primary_tracker_url, self.new_candidate['primary_tracker_url'])
        self.assertNotEqual(self.other_candidate.secondary_tracker_url, self.new_candidate['secondary_tracker_url'])

    def test_invalid_candidate_fields(self):
        new_candidate = {
            'id': self.candidate.id,
            'ad_group_id': 55,
            'batch_id': 1234,
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
        }

        upload.update_candidate(new_candidate, self.defaults, self.candidate.batch)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.ad_group_id, 4)
        self.assertEqual(self.candidate.batch_id, 5)

    @patch('dash.upload.invoke_external_validation')
    def test_invoke_external_validation(self, mock_invoke):
        upload.update_candidate(self.new_candidate, [], self.candidate.batch)
        self.assertFalse(mock_invoke.called)

        new_candidate = {
            'id': self.candidate.id,
            'label': 'new label',
            'url': 'http://zemanta.com/new-blog',
            'title': 'New title',
            'image_url': 'http://zemanta.com/new-img.jpg',
            'image_crop': 'center',
            'display_url': 'newurl.com',
            'brand_name': 'New brand name',
            'description': 'New description',
            'call_to_action': 'New cta',
            'primary_tracker_url': '',
            'secondary_tracker_url': '',
        }

        upload.update_candidate(new_candidate, [], self.candidate.batch)
        self.assertTrue(mock_invoke.called)


class GetCandidatesCsvTestCase(TestCase):

    fixtures = ['test_upload.yaml']

    def test_candidates_csv(self):
        batch = models.UploadBatch.objects.get(id=1)
        content = upload.get_candidates_csv(batch)
        self.assertEqual('Url,Title,Image url,Display url,Brand name,Description,Call to action,'
                         'Label,Image crop,Primary tracker url,Secondary tracker url\r\nhttp://zemanta.com/blog,'
                         'Zemanta blog čšž,http://zemanta.com/img.jpg,zemanta.com,Zemanta,Zemanta blog,Read more,'
                         'content ad 1,entropy,,\r\n', content)


@patch('utils.lambda_helper.invoke_lambda')
class UploadTest(TestCase):
    fixtures = ['test_api.yaml']

    @override_settings(
        LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME='content-upload',
        LAMBDA_CONTENT_UPLOAD_NAMESPACE='name/space'
    )
    def test_lambda_invoke(self, mock_lambda):
        content_ads_data = [
            {
                'url': 'http://test.url.com/page1',
                'image_url': 'http://test.url.com/image1.png',
            },
            {
                'url': 'http://test.url.com/page2',
                'image_url': 'http://test.url.com/image2.png',
            }
        ]

        ad_group = models.AdGroup.objects.get(pk=1)
        batch, candidates = upload.insert_candidates(
            content_ads_data,
            ad_group,
            'Test batch',
            'test_upload.csv',
        )
        for candidate in candidates:
            upload.invoke_external_validation(candidate, batch)

        self.assertEqual(mock_lambda.call_count, 2)

        (lambda_name1, lambda_data1), _ = mock_lambda.call_args_list[0]
        (lambda_name2, lambda_data2), _ = mock_lambda.call_args_list[1]

        self.assertEqual(lambda_name1, 'content-upload')
        self.assertEqual(lambda_data1['adGroupID'], 1)
        self.assertEqual(lambda_data1['imageUrl'], 'http://test.url.com/image1.png')
        self.assertEqual(lambda_data1['pageUrl'], 'http://test.url.com/page1')
        self.assertEqual(lambda_data1['namespace'], 'name/space')
        self.assertTrue(lambda_data1['batchID'])
        self.assertTrue(lambda_data1['candidateID'])

        self.assertEqual(lambda_name2, 'content-upload')
        self.assertEqual(lambda_data2['adGroupID'], 1)
        self.assertEqual(lambda_data2['imageUrl'], 'http://test.url.com/image2.png')
        self.assertEqual(lambda_data2['pageUrl'], 'http://test.url.com/page2')
        self.assertEqual(lambda_data2['namespace'], 'name/space')
        self.assertTrue(lambda_data2['batchID'])
        self.assertTrue(lambda_data2['candidateID'])

    def test_process_callback(self, *mocks):
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = upload.insert_candidates(
            [{
                "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                "image_url": "http://static1.squarespace.com/image.jpg",

            }],
            ad_group,
            'Test batch',
            'test_upload.csv',
        )
        upload.process_callback({
            "id": candidates[0].pk,
            "url": {
                "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                "valid": True,
                "targetUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
            },
            "image": {
                "valid": True,
                "width": 1500,
                "hash": "0000000000000000",
                "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e14",
                "height": 245,
                "originUrl": "http://static1.squarespace.com/image.jpg",
            }
        })

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.OK)
