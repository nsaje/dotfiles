from django import test

import core.models
from utils.magic_mixer import magic_mixer


class AccountSettingsModelTest(test.TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)

    def test_get_base_default_icon_url(self):
        default_icon = magic_mixer.blend(core.models.ImageAsset, image_id="default_icon", width=240, height=240)
        self.account.settings.update_unsafe(None, default_icon=default_icon)
        self.assertEqual("/default_icon.jpg", self.account.settings.get_base_default_icon_url())

    def test_get_default_icon_url(self):
        default_icon = magic_mixer.blend(core.models.ImageAsset, image_id="default_icon", width=240, height=240)
        self.account.settings.update_unsafe(None, default_icon=default_icon)
        self.assertEqual(
            "/default_icon.jpg?w=240&h=240&fit=crop&crop=center", self.account.settings.get_default_icon_url()
        )
        self.assertEqual(
            "/default_icon.jpg?w=700&h=700&fit=crop&crop=center", self.account.settings.get_default_icon_url(700)
        )
