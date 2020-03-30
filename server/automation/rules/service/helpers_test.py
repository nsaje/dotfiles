from django.test import TestCase

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from .. import models
from . import helpers


class RulesMapTest(TestCase):
    def test_get_rules_by_ad_group_map(self):
        ad_groups_archived = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=True)
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=False)
        for ag in ad_groups + ad_groups_archived:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        ad_groups_inactive = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=False)
        for ag in ad_groups_inactive:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)

        rule_1 = magic_mixer.blend(
            models.Rule, ad_groups_included=ad_groups[:3] + ad_groups_inactive[:3] + ad_groups_archived[:3]
        )
        rule_2 = magic_mixer.blend(
            models.Rule, ad_groups_included=ad_groups[3:5] + ad_groups_inactive[3:5] + ad_groups_archived[3:5]
        )
        rule_3 = magic_mixer.blend(
            models.Rule, ad_groups_included=ad_groups[1:4] + ad_groups_inactive[1:4] + ad_groups_archived[1:4]
        )

        rules_map = helpers.get_rules_by_ad_group_map([rule_1, rule_2, rule_3])
        self.assertEqual(
            {
                ad_groups[0]: [rule_1],
                ad_groups[1]: [rule_1, rule_3],
                ad_groups[2]: [rule_1, rule_3],
                ad_groups[3]: [rule_2, rule_3],
                ad_groups[4]: [rule_2],
            },
            rules_map,
        )
