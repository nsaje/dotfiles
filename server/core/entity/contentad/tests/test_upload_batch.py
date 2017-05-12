from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash import constants
from dash import models

from .. import upload_batch


class UploadBatchCreate(TestCase):

    def setUp(self):
        self.ad_group = magic_mixer.blend(models.AdGroup)

    def test_create(self):
        batch = upload_batch.UploadBatch.objects.create(None, 'test', self.ad_group.id)
        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual('test', batch.name)
        self.assertEqual(None, batch.original_filename)

    def test_create_for_file(self):
        batch = upload_batch.UploadBatch.objects.create_for_file(None, 'test', self.ad_group.id, 'filename', True, True)
        self.assertEqual(self.ad_group.id, batch.ad_group_id)
        self.assertEqual('test', batch.name)
        self.assertEqual('filename', batch.original_filename)
        self.assertTrue(batch.auto_save)
        self.assertEqual(constants.UploadBatchType.EDIT, batch.type)
