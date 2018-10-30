from django.test import TestCase
from django.test import override_settings

from utils.magic_mixer import magic_mixer

from . import constants
from . import models

TEST_URL = "http://example.com/{filename}"

SAMPLE_FORMAT = {"width": 1920, "height": 1080, "bitrate": 4500, "mime": "video/mp4", "filename": "xyz_1080p.mp4"}


class TestModels(TestCase):
    @override_settings(VIDEO_PREVIEW_URL=TEST_URL)
    def test_get_preview_url(self):
        videoasset = magic_mixer.blend(models.VideoAsset, status=constants.VideoAssetStatus.NOT_UPLOADED)
        self.assertEqual(videoasset.get_preview_url(), None)

        videoasset = magic_mixer.blend(
            models.VideoAsset, status=constants.VideoAssetStatus.READY_FOR_USE, formats=[{"filename": "x"}]
        )
        self.assertEqual(videoasset.get_preview_url(), TEST_URL.format(filename="x"))

    def test_validate_format(self):
        models.validate_format(SAMPLE_FORMAT)

        invalid_format = {"bitrate": "hi", "mime": 1.4}
        with self.assertRaises(AssertionError):
            models.validate_format(invalid_format)

    def test_update_progress(self):
        videoasset = magic_mixer.blend(models.VideoAsset, status=constants.VideoAssetStatus.NOT_UPLOADED)
        videoasset.update_progress(
            status=constants.VideoAssetStatus.PROCESSING_ERROR, error_code="403", duration=51, formats=[SAMPLE_FORMAT]
        )
        self.assertEqual(videoasset.status, constants.VideoAssetStatus.PROCESSING_ERROR)
        self.assertEqual(videoasset.error_code, "403")
        self.assertEqual(videoasset.duration, 51)
        self.assertEqual(videoasset.formats, [SAMPLE_FORMAT])
