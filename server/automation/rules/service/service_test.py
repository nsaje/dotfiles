import mock
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import constants
from . import service


class ServiceTest(TestCase):
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.service._format_stats")
    @mock.patch("redshiftapi.api_rules.query")
    def test_process_rules(self, mock_stats, mock_format, mock_apply):
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)
        mock_stats.return_value = [123]
        mock_format.return_value = {ag.id: {} for ag in ad_groups}
        magic_mixer.blend(Rule, target=constants.TargetType.PUBLISHER, ad_groups_included=ad_groups[:4])
        magic_mixer.blend(Rule, target=constants.TargetType.OS, ad_groups_included=ad_groups[1:5])

        service.process_rules()

        self.assertEqual([mock.call(constants.TargetType.PUBLISHER, [mock.ANY] * 4)], mock_stats.call_args_list)
        self.assertCountEqual(
            [ad_groups[0], ad_groups[1], ad_groups[2], ad_groups[3]], mock_stats.call_args_list[0][0][1]
        )

        self.assertEqual([mock.call(constants.TargetType.PUBLISHER, [123])], mock_format.call_args_list)

        self.assertEqual(4, mock_apply.call_count)

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

    def test_format_stats(self):
        target = constants.TargetType.PUBLISHER
        stats = [
            {
                "ad_group_id": 123,
                "publisher_id": "pub1",
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                "publisher_id": "pub1",
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "cpc": 0.3,
                "cpm": 0.1,
            },
            {
                "ad_group_id": 123,
                "publisher_id": "pub2",
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "cpc": 0.5,
                "cpm": 0.2,
            },
            {
                "ad_group_id": 123,
                "publisher_id": "pub2",
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LIFETIME,
                "cpc": None,
                "cpm": 0.8,
            },
            {
                "ad_group_id": 321,
                "publisher_id": "pub1",
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.1,
                "cpm": 0.2,
            },
            {
                "ad_group_id": 321,
                "publisher_id": "pub3",
                "publisher": "pub3.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "cpc": 0.2,
                "cpm": 0.1,
            },
            {
                "ad_group_id": None,
                "publisher_id": "pub4",
                "publisher": "pub4.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                "publisher_id": None,
                "publisher": "None",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {"ad_group_id": 321, "publisher": "pub5", "window_key": None, "cpc": 0.5, "cpm": 0.7},
        ]
        formatted_stats = service._format_stats(target, stats)
        self.assertEqual(
            {
                123: {
                    "pub1": {
                        "publisher": "pub1.com",
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    },
                    "pub2": {
                        "publisher": "pub2.com",
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    },
                },
                321: {
                    "pub1": {
                        "publisher": "pub1.com",
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    },
                    "pub3": {
                        "publisher": "pub3.com",
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    },
                },
            },
            formatted_stats,
        )