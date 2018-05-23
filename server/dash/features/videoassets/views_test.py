import mock
from django.core.urlresolvers import reverse
from rest_framework.test import APIClient

from utils.magic_mixer import magic_mixer

import core.entity.account
import restapi.common.views_base_test
from . import models


class VideoAssetTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        self.user = magic_mixer.blend_user(permissions=['fea_video_upload'])
        self.account = magic_mixer.blend(core.entity.Account, users=[self.user])
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        patcher = mock.patch('boto3.client')
        self.boto3_get_client = patcher.start()
        self.addCleanup(patcher.stop)

    def test_permissions(self):
        video_asset = magic_mixer.blend(models.VideoAsset)
        r = self.client.get(reverse('videoassets_details',
                                    kwargs=dict(videoasset_id=video_asset.id,
                                                account_id=video_asset.account.id)))
        r = self.assertResponseError(r, 'MissingDataError')

    def test_get(self):
        video_asset = magic_mixer.blend(models.VideoAsset, account=self.account, name='myvideo',
                                        error_code='4006')
        r = self.client.get(reverse('videoassets_details',
                                    kwargs=dict(videoasset_id=video_asset.id,
                                                account_id=video_asset.account.id)))
        r = self.assertResponseValid(r)
        self.assertEqual(r['data']['name'], video_asset.name)
        self.assertEqual(r['data']['errorCode'], video_asset.error_code)

    def test_post(self):
        mock_s3_client = mock.Mock()
        mock_s3_client.generate_presigned_url.return_value = 'http://mypresigned.com'
        self.boto3_get_client.return_value = mock_s3_client
        data = {
            'name': 'myvideo',
            'upload': {
                'type': 'DIRECT_UPLOAD',
            }
        }
        r = self.client.post(reverse('videoassets_list', kwargs=dict(account_id=self.account.id)),
                             data=data, format='json')
        r = self.assertResponseValid(r)
        self.assertEqual(r['data']['name'], 'myvideo')
        self.assertEqual(r['data']['account'], str(self.account.id))
        self.assertEqual(r['data']['status'], 'NOT_UPLOADED')
        self.assertEqual(r['data']['upload']['url'], 'http://mypresigned.com')

        mock_s3_client.generate_presigned_url.assert_called_once()
