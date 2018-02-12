import json

from rest_framework.test import APIClient
from django.test import TestCase
from django.core.urlresolvers import reverse

from zemauth.models import User

from utils.magic_mixer import magic_mixer
import dash.features.videoassets.models
import dash.features.videoassets.constants


class VideoUploadCallbackTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)
        self.videoasset = magic_mixer.blend(dash.features.videoassets.models.VideoAsset,
                                            status=dash.features.videoassets.constants.VideoAssetStatus.NOT_UPLOADED)

    def test_put(self):
        data = {'status': 'PROCESSING', 'duration': 23, 'formats': [{
            'width': 123,
            'height': 321,
            'bitrate': 4500,
            'mime': 'video/mp4',
            'filename': 'x.mp4'
        }]}
        r = self.client.put(
            reverse('service.videoassets', kwargs={'videoasset_id': self.videoasset.id}),
            data=data, format='json')
        self.assertEqual(json.loads(r.content), {"data": "ok"})
        self.videoasset.refresh_from_db()
        self.assertEqual(self.videoasset.status, dash.features.videoassets.constants.VideoAssetStatus.PROCESSING)
        self.assertEqual(self.videoasset.duration, 23)
        self.assertEqual(self.videoasset.formats[0]['width'], 123)
        self.assertEqual(self.videoasset.formats[0]['filename'], 'x.mp4')

    def test_put_error(self):
        data = {'status': 'PROCESSING_ERROR', 'errorCode': 4006}
        r = self.client.put(
            reverse('service.videoassets', kwargs={'videoasset_id': self.videoasset.id}),
            data=data, format='json')
        self.assertEqual(json.loads(r.content), {"data": "ok"})
        self.videoasset.refresh_from_db()
        self.assertEqual(self.videoasset.status, dash.features.videoassets.constants.VideoAssetStatus.PROCESSING_ERROR)
        self.assertEqual(self.videoasset.error_code, '4006')
