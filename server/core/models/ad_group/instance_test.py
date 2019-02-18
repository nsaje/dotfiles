from django.test import TestCase

import core.models
from dash import history_helpers
from utils.magic_mixer import magic_mixer


class AdGroupHistory(TestCase):
    def test_history_ad_group_created(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(core.models.AdGroup)
        magic_mixer.cycle(5).blend(core.models.AdGroupSource, ad_group=ad_group)

        ad_group.write_history_created(request)

        history = history_helpers.get_ad_group_history(ad_group)

        self.assertEqual(len(history), 7)
        self.assertRegex(
            history.first().changes_text, r"Created settings and automatically created campaigns for 5 sources .*"
        )
