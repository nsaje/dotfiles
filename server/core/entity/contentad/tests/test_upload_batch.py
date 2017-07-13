from django.test import TestCase
import mock
from utils.magic_mixer import magic_mixer

from dash import constants

import core.entity


class UploadBatchCreate(TestCase):

    def setUp(self):
        self.ad_group = magic_mixer.blend(core.entity.AdGroup)
        self.account = self.ad_group.campaign.account

    def test_create(self):
        batch = core.entity.UploadBatch.objects.create(None, self.account, 'test', self.ad_group)
        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual('test', batch.name)
        self.assertEqual(None, batch.original_filename)

    @mock.patch('core.entity.UploadBatch.generate_cloned_name', return_value='test')
    def test_clone(self, _):
        user = magic_mixer.blend_user()
        source_ad_group = magic_mixer.blend(core.entity.AdGroup)
        batch = core.entity.UploadBatch.objects.clone(user, source_ad_group, self.ad_group)

        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual('test', batch.name)
        self.assertEqual(None, batch.original_filename)

    def test_create_for_file(self):
        batch = core.entity.UploadBatch.objects.create_for_file(
            None, self.account, 'test', self.ad_group, 'filename', True, True)
        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual('test', batch.name)
        self.assertEqual('filename', batch.original_filename)
        self.assertTrue(batch.auto_save)
        self.assertEqual(constants.UploadBatchType.EDIT, batch.type)
