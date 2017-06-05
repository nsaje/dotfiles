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

    def test_put(self):
        videoasset = magic_mixer.blend(dash.features.videoassets.models.VideoAsset,
                                       status=dash.features.videoassets.constants.VideoAssetStatus.NOT_UPLOADED)

        data = {'status': 'PROCESSING'}
        r = self.client.put(
            reverse('service.videoassets', kwargs={'videoasset_id': videoasset.id}),
            data=data, format='json')
        self.assertEqual(r.content, '{"data":"ok"}')
        videoasset.refresh_from_db()
        self.assertEqual(videoasset.status, dash.features.videoassets.constants.VideoAssetStatus.PROCESSING)
