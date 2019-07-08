import mock
from django.test import TestCase

import dash.constants
from utils.magic_mixer import magic_mixer

from . import model
from .. import ad_group


class UploadBatchCreate(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(ad_group.AdGroup)
        self.account = self.ad_group.campaign.account

    def test_create(self):
        batch = model.UploadBatch.objects.create(None, self.account, "test", self.ad_group)
        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual("test", batch.name)
        self.assertEqual(None, batch.original_filename)

    @mock.patch("core.models.UploadBatch.generate_cloned_name", return_value="test")
    def test_clone(self, _):
        user = magic_mixer.blend_user()
        source_ad_group = magic_mixer.blend(ad_group.AdGroup)
        batch = model.UploadBatch.objects.clone(user, source_ad_group, self.ad_group)

        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual("test", batch.name)
        self.assertEqual(None, batch.original_filename)

    def test_create_for_file(self):
        batch = model.UploadBatch.objects.create_for_file(
            None, self.account, "test", self.ad_group, "filename", True, True
        )
        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual("test", batch.name)
        self.assertEqual("filename", batch.original_filename)
        self.assertTrue(batch.auto_save)
        self.assertEqual(dash.constants.UploadBatchType.EDIT, batch.type)
