import mock
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import constants
from . import service


class ServiceTest(TestCase):
    @mock.patch("automation.rules.service.service._get_ad_groups_stats")
    @mock.patch("automation.rules.service.service.apply_rule")
    def test_process_rules(self, mock_apply, mock_stats):
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)
        mock_stats.return_value = {ag.id: {} for ag in ad_groups}
        magic_mixer.blend(Rule, target=constants.TargetType.PUBLISHER, ad_groups_included=ad_groups[:4])
        magic_mixer.blend(Rule, target=constants.TargetType.OS, ad_groups_included=ad_groups[1:5])
        service.process_rules()
        self.assertEqual(
            [
                mock.call([]),
                mock.call([]),
                mock.call([mock.ANY] * 4),
                mock.call([]),
                mock.call([]),
                mock.call([]),
                mock.call([]),
                mock.call([mock.ANY] * 4),
                mock.call([]),
            ],
            mock_stats.call_args_list,
        )
        self.assertCountEqual(
            [ad_groups[0], ad_groups[1], ad_groups[2], ad_groups[3]], mock_stats.call_args_list[2][0][0]
        )
        self.assertCountEqual(
            [ad_groups[1], ad_groups[2], ad_groups[3], ad_groups[4]], mock_stats.call_args_list[7][0][0]
        )
        self.assertEqual(8, mock_apply.call_count)

    def test_get_rules_by_ad_group_map(self):
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)
        rule_1 = magic_mixer.blend(Rule, ad_groups_included=ad_groups[:3])
        rule_2 = magic_mixer.blend(Rule, ad_groups_included=ad_groups[3:5])
        rule_3 = magic_mixer.blend(Rule, ad_groups_included=ad_groups[1:4])

        rules_map = service._get_rules_by_ad_group_map([rule_1, rule_2, rule_3])
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
