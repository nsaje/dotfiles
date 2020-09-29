from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def test_invalid_name(self):
        account = magic_mixer.blend(core.models.Account)
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="test")
        with self.assertRaises(exceptions.DuplicatePixelName):
            core.models.ConversionPixel.objects.create(None, account, name="test")

        core.models.ConversionPixel.objects.create(None, account, skip_notification=True)
        core.models.ConversionPixel.objects.create(None, account, name="", skip_notification=True)
