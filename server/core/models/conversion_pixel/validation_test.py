from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def test_audience_and_additional_pixel(self):
        account = magic_mixer.blend(core.models.Account)
        with self.assertRaises(exceptions.MutuallyExclusivePixelFlagsEnabled):
            core.models.ConversionPixel.objects.create(
                None, account, name="test1", audience_enabled=True, additional_pixel=True
            )
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test", additional_pixel=True)
        with self.assertRaises(exceptions.MutuallyExclusivePixelFlagsEnabled):
            pixel.update(None, audience_enabled=True)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test", audience_enabled=True)
        with self.assertRaises(exceptions.MutuallyExclusivePixelFlagsEnabled):
            pixel.update(None, additional_pixel=True)

    def test_unique_audience_pixel(self):
        account = magic_mixer.blend(core.models.Account)
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="test", audience_enabled=True)
        with self.assertRaises(exceptions.AudiencePixelAlreadyExists):
            core.models.ConversionPixel.objects.create(None, account, name="test1", audience_enabled=True)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test2")
        with self.assertRaises(exceptions.AudiencePixelAlreadyExists):
            pixel.update(None, audience_enabled=True)

    def test_audience_missing(self):
        account = magic_mixer.blend(core.models.Account)
        with self.assertRaises(exceptions.AudiencePixelNotSet):
            core.models.ConversionPixel.objects.create(None, account, name="test1", additional_pixel=True)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test2")
        with self.assertRaises(exceptions.AudiencePixelNotSet):
            pixel.update(None, additional_pixel=True)

    def test_invalid_name(self):
        account = magic_mixer.blend(core.models.Account)
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="test")
        with self.assertRaises(exceptions.DuplicatePixelName):
            core.models.ConversionPixel.objects.create(None, account, name="test")

        core.models.ConversionPixel.objects.create(None, account, skip_notification=True)
        core.models.ConversionPixel.objects.create(None, account, name="", skip_notification=True)

    def test_archive_audience_pixel(self):
        account = magic_mixer.blend(core.models.Account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test", audience_enabled=True)
        with self.assertRaises(exceptions.AudiencePixelCanNotBeArchived):
            pixel.update(None, archived=True)
