from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class AccountSettingsValidationTest(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)

    def test_validate_default_icon_not_square(self):
        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", hash="hash", width=130, height=131, file_size=1000
        )
        changes = {"default_icon": default_icon}
        with self.assertRaises(exceptions.DefaultIconNotSquare):
            self.account.settings._validate_default_icon(changes)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", hash="hash", width=130, height=131, file_size=1000
        )
        changes = {"default_icon": default_icon}
        with self.assertRaises(exceptions.DefaultIconNotSquare):
            self.account.settings._validate_default_icon(changes)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", hash="hash", width=130, height=130, file_size=1000
        )
        changes = {"default_icon": default_icon}
        self.account.settings._validate_default_icon(changes)

    def test_validate_default_icon_too_small(self):
        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", hash="hash", width=127, height=127, file_size=1000
        )
        changes = {"default_icon": default_icon}
        with self.assertRaises(exceptions.DefaultIconTooSmall):
            self.account.settings._validate_default_icon(changes)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", hash="hash", width=128, height=128, file_size=1000
        )
        changes = {"default_icon": default_icon}
        self.account.settings._validate_default_icon(changes)

    def test_validate_default_icon_too_big(self):
        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", hash="hash", width=100000, height=100000, file_size=1000
        )
        changes = {"default_icon": default_icon}
        with self.assertRaises(exceptions.DefaultIconTooBig):
            self.account.settings._validate_default_icon(changes)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", hash="hash", width=9999, height=9999, file_size=1000
        )
        changes = {"default_icon": default_icon}
        self.account.settings._validate_default_icon(changes)
