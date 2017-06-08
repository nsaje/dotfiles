from django.test import TestCase
from django.test import override_settings
from utils.magic_mixer import magic_mixer

import models
import constants

TEST_URL = 'http://example.com/{videoasset_id}'


class TestModels(TestCase):

    @override_settings(VIDEO_PREVIEW_URL=TEST_URL)
    def test_get_preview_url(self):
        videoasset = magic_mixer.blend(models.VideoAsset, status=constants.VideoAssetStatus.NOT_UPLOADED)
        self.assertEqual(videoasset.get_preview_url(), None)

        videoasset = magic_mixer.blend(models.VideoAsset, status=constants.VideoAssetStatus.READY_FOR_USE)
        self.assertEqual(videoasset.get_preview_url(), TEST_URL.format(videoasset_id=videoasset.id))
