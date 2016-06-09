from mock import patch
from django.test import TestCase, override_settings

import dash.models
import dash.upload_plus

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
    'tracker_urls': 'https://t.zemanta.com/px1.png https://t.zemanta.com/px2.png',
}

invalid_candidate = {
    'label': 'test' * 10,
    'url': 'ftp://zemanta.com/test-content-ad',
    'image_url': 'file://zemanta.com/test-image.jpg',
    'image_crop': 'landscape',
    'display_url': 'zemanta.com' * 10,
    'tracker_urls': 'http://t.zemanta.com/px1.png http://t.zemanta.com/px2.png',
}


class InsertCandidatesTestCase(TestCase):
    fixtures = ['test_upload_plus.yaml']

    def test_insert_candidates(self):
        data = [valid_candidate]

        ad_group = dash.models.AdGroup.objects.get(id=1)
        batch_name = 'batch1'
        filename = 'test_upload.csv'
        self.assertEqual(0, dash.models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        dash.upload_plus.insert_candidates(data, ad_group, batch_name, filename)
        self.assertEqual(1, dash.models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, dash.models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = dash.models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(1, batch.batch_size)
        self.assertEqual(filename, batch.original_filename)

        candidate = dash.models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual(valid_candidate['label'], candidate.label)
        self.assertEqual(valid_candidate['url'], candidate.url)
        self.assertEqual(valid_candidate['title'], candidate.title)
        self.assertEqual(valid_candidate['image_url'], candidate.image_url)
        self.assertEqual(valid_candidate['image_crop'], candidate.image_crop)
        self.assertEqual(valid_candidate['display_url'], candidate.display_url)
        self.assertEqual(valid_candidate['brand_name'], candidate.brand_name)
        self.assertEqual(valid_candidate['description'], candidate.description)
        self.assertEqual(valid_candidate['call_to_action'], candidate.call_to_action)
        self.assertEqual(valid_candidate['tracker_urls'], candidate.tracker_urls)

    def test_empty_candidate(self):
        data = [{}]

        ad_group = dash.models.AdGroup.objects.get(id=1)
        batch_name = 'batch1'
        filename = 'test_upload.csv'
        self.assertEqual(0, dash.models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        dash.upload_plus.insert_candidates(data, ad_group, batch_name, filename)
        self.assertEqual(1, dash.models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, dash.models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = dash.models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(1, batch.batch_size)
        self.assertEqual(filename, batch.original_filename)

        candidate = dash.models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual('', candidate.label)
        self.assertEqual('', candidate.url)
        self.assertEqual('', candidate.title)
        self.assertEqual('', candidate.image_url)
        self.assertEqual('center', candidate.image_crop)
        self.assertEqual('', candidate.display_url)
        self.assertEqual('', candidate.brand_name)
        self.assertEqual('', candidate.description)
        self.assertEqual('', candidate.call_to_action)
        self.assertEqual('', candidate.tracker_urls)


class PersistCandidatesTestCase(TestCase):
    fixtures = ['test_upload_plus.yaml']

    @patch.object(utils.s3helpers.S3Helper, 'put')
    def test_valid_candidates(self, mock_s3helper_put):
        batch = dash.models.UploadBatch.objects.get(id=2)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        candidate = batch.contentadcandidate_set.get()

        dash.upload_plus.persist_candidates(batch)
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
        self.assertEqual(candidate.tracker_urls.split(' '), content_ad.tracker_urls)
        self.assertEqual(candidate.image_id, content_ad.image_id)
        self.assertEqual(candidate.image_width, content_ad.image_width)
        self.assertEqual(candidate.image_height, content_ad.image_height)
        self.assertEqual(candidate.image_hash, content_ad.image_hash)

        batch.refresh_from_db()
        self.assertEqual(dash.constants.UploadBatchStatus.DONE, batch.status)
        self.assertEqual(0, batch.num_errors)
        self.assertEqual(None, batch.error_report_key)

    @patch.object(utils.s3helpers.S3Helper, 'put')
    def test_invalid_candidates(self, mock_s3helper_put):
        batch = dash.models.UploadBatch.objects.get(id=3)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        dash.upload_plus.persist_candidates(batch)
        self.assertEqual(0, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        self.assertTrue(mock_s3helper_put.called)

        s3_key, content = mock_s3helper_put.call_args[0]
        self.assertTrue(s3_key.startswith('contentads/errors/3/test_upload'))
        self.assertTrue(s3_key.endswith('.csv'))
        self.assertEqual(
            'url,title,image_url,tracker_urls,display_url,brand_name,description,call_to_action,label,image_crop,errors'
            '\r\nhttp://zemanta.com/blog,Zemanta blog,http://zemanta.com/img.jpg,,zemanta.com,Zemanta,Zemanta blog,Read'
            ' more,content ad 1,entropy,"Content unreachable, Image could not be processed"\r\n', content)

        batch.refresh_from_db()
        self.assertEqual(dash.constants.UploadBatchStatus.DONE, batch.status)
        self.assertEqual(1, batch.num_errors)
        self.assertEqual(s3_key, batch.error_report_key)

    @patch.object(utils.s3helpers.S3Helper, 'put')
    def test_invalid_batch_status(self, mock_s3helper_put):
        batch = dash.models.UploadBatch.objects.get(id=2)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        batch.status = dash.constants.UploadBatchStatus.CANCELLED
        batch.save()

        with self.assertRaises(dash.upload_plus.InvalidBatchStatus):
            dash.upload_plus.persist_candidates(batch)

        # check that nothing changed
        batch.refresh_from_db()
        self.assertEqual(dash.constants.UploadBatchStatus.CANCELLED, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())
        self.assertFalse(mock_s3helper_put.called)


class CancelUploadTestCase(TestCase):
    fixtures = ['test_upload_plus.yaml']

    def test_cancel(self):
        ad_group = dash.models.AdGroup.objects.get(id=2)
        self.assertEqual(1, dash.models.UploadBatch.objects.filter(ad_group=ad_group).count())

        batch = dash.models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(dash.constants.UploadBatchStatus.IN_PROGRESS, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())

        dash.upload_plus.cancel_upload(batch)

        batch.refresh_from_db()
        self.assertEqual(dash.constants.UploadBatchStatus.CANCELLED, batch.status)
        self.assertEqual(0, batch.contentadcandidate_set.count())

    def test_invalid_status(self):
        ad_group = dash.models.AdGroup.objects.get(id=2)
        batch = dash.models.UploadBatch.objects.filter(ad_group=ad_group).get()

        batch.status = dash.constants.UploadBatchStatus.DONE
        batch.save()

        with self.assertRaises(dash.upload_plus.InvalidBatchStatus):
            dash.upload_plus.cancel_upload(batch)


class ValidateCandidatesTestCase(TestCase):
    fixtures = ['test_upload_plus.yaml']

    def test_valid_candidate(self):
        data = [valid_candidate]

        # prepare candidate
        ad_group = dash.models.AdGroup.objects.get(id=1)
        batch, candidates = dash.upload_plus.insert_candidates(data, ad_group, 'batch1', 'test_upload.csv')

        errors = dash.upload_plus.validate_candidates(candidates)
        self.assertFalse(errors)

    def test_invalid_candidate(self):
        data = [invalid_candidate]

        # prepare candidate
        ad_group = dash.models.AdGroup.objects.get(id=1)
        batch, candidates = dash.upload_plus.insert_candidates(data, ad_group, 'batch1', 'test_upload.csv')

        errors = dash.upload_plus.validate_candidates(candidates)
        self.assertEquals({
            candidates[0].id: {
                'label': [u'Label too long (max 25 characters)'],
                'title': [u'Missing title'],
                'url': [u'Invalid URL'],
                'image_url': [u'Invalid image URL'],
                'image_crop': [u'Image crop landscape is not supported'],
                'description': [u'Missing description'],
                'display_url': [u'Display URL too long (max 25 characters)'],
                'brand_name': [u'Missing brand name'],
                'call_to_action': [u'Missing call to action'],
                'tracker_urls': [u'Invalid tracker URLs']
            }
        }, errors)


@patch('utils.lambda_helper.invoke_lambda')
class UploadPlusTest(TestCase):
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

        ad_group = dash.models.AdGroup.objects.get(pk=1)
        _, candidates = dash.upload_plus.insert_candidates(
            content_ads_data,
            ad_group,
            'Test batch',
            'test_upload.csv',
        )
        for candidate in candidates:
            dash.upload_plus.invoke_external_validation(candidate)

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
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        _, candidates = dash.upload_plus.insert_candidates(
            [{
                "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                "image_url": "http://static1.squarespace.com/image.jpg",

            }],
            ad_group,
            'Test batch',
            'test_upload.csv',
        )
        dash.upload_plus.process_callback({
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
                "height": 245
            }
        })

        candidate = dash.models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, dash.constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, dash.constants.AsyncUploadJobStatus.OK)
