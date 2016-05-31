from mock import patch
from django.test import TestCase, override_settings

import dash.models
import dash.upload_plus


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
            'Test batch'
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
            'Test batch'
        )
        dash.upload_plus.process_callback({
            "id": candidates[0].pk,
            "url": {
                "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                "valid": True,
                "targetUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
            },
            "image": {
                "width": 1500,
                "hash": "0000000000000000",
                "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e14",
                "height": 245
            }
        })

        candidate = dash.models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, dash.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, dash.AsyncUploadJobStatus.OK)
