from django.test import TestCase

import core.models
import dash.constants
import dash.history_helpers
from utils.magic_mixer import magic_mixer


class AdGroupInstanceTest(TestCase):
    def test_history_ad_group_created(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(core.models.AdGroup)
        magic_mixer.cycle(5).blend(core.models.AdGroupSource, ad_group=ad_group)

        ad_group.write_history_created(request)

        history = dash.history_helpers.get_ad_group_history(ad_group)

        self.assertEqual(len(history), 7)
        self.assertRegex(
            history.first().changes_text, r"Created settings and automatically created campaigns for 5 sources .*"
        )

    def test_archive_restore(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(dash.constants.AdGroupSettingsState.ACTIVE, ad_group.settings.state)
        ad_group.archive(request)
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ad_group.settings.state)
        ad_group.restore(request)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ad_group.settings.state)
