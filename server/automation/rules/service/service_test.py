import mock
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import RuleHistory
from .. import constants
from . import service
from .actions import ValueChangeData


class ServiceTest(TestCase):
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.service._format_stats")
    @mock.patch("redshiftapi.api_rules.query")
    def test_process_publisher_rules(self, mock_stats, mock_format, mock_apply):
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)
        mock_stats.return_value = [123]
        mock_format.return_value = {ag.id: {} for ag in ad_groups}
        mock_apply.return_value = [
            ValueChangeData(target="pub1.com__12", old_value=1.0, new_value=2.0),
            ValueChangeData(target="pub2.com__21", old_value=2.0, new_value=1.0),
        ]
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, ad_groups_included=ad_groups[:4])
        magic_mixer.blend(Rule, target_type=constants.TargetType.OS, ad_groups_included=ad_groups[1:5])
        magic_mixer.blend(
            Rule,
            state=constants.RuleState.PAUSED,
            target_type=constants.TargetType.PUBLISHER,
            ad_groups_included=ad_groups,
        )

        service.process_rules()

        self.assertEqual([mock.call(constants.TargetType.PUBLISHER, [mock.ANY] * 4)], mock_stats.call_args_list)
        self.assertCountEqual(
            [ad_groups[0], ad_groups[1], ad_groups[2], ad_groups[3]], mock_stats.call_args_list[0][0][1]
        )
        self.assertEqual([mock.call(constants.TargetType.PUBLISHER, [123])], mock_format.call_args_list)
        self.assertEqual(4, mock_apply.call_count)
        complete_history = RuleHistory.objects.all()
        self.assertEqual(4, complete_history.count())
        for history in complete_history:
            self.assertEqual(rule, history.rule)
            self.assertTrue(history.ad_group in ad_groups[:4])
            self.assertEqual(constants.ApplyStatus.SUCCESS, history.status)
            self.assertEqual(
                {
                    "pub1.com__12": {"old_value": 1.0, "new_value": 2.0},
                    "pub2.com__21": {"old_value": 2.0, "new_value": 1.0},
                },
                history.changes,
            )
            self.assertEqual("Updated targets: pub1.com__12, pub2.com__21", history.changes_text)

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.service._format_stats")
    @mock.patch("redshiftapi.api_rules.query")
    def test_process_publisher_rules_fail(self, mock_stats, mock_format, mock_apply):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        mock_stats.return_value = [123]
        mock_format.return_value = {ad_group.id: {}}
        mock_apply.side_effect = Exception("test")
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            ad_groups_included=[ad_group],
        )
        self.assertFalse(RuleHistory.objects.exists())

        service.process_rules()

        history = RuleHistory.objects.get()
        self.assertEqual(rule, history.rule)
        self.assertEqual(constants.ApplyStatus.FAILURE, history.status)
        self.assertIsNone(history.changes)
        self.assertTrue("Traceback (most recent call last):" in history.changes_text)

    @mock.patch("automation.rules.service.service._format_stats")
    @mock.patch("redshiftapi.api_rules.query")
    def test_process_publisher_rules_no_changes(self, mock_stats, mock_format):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        mock_stats.return_value = [123]
        mock_format.return_value = {ad_group.id: {}}
        magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            ad_groups_included=[ad_group],
        )
        self.assertFalse(RuleHistory.objects.exists())

        service.process_rules()

        self.assertFalse(RuleHistory.objects.exists())

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

    def test_format_publisher_stats(self):
        target_type = constants.TargetType.PUBLISHER
        stats = [
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "cpc": 0.3,
                "cpm": 0.1,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "cpc": 0.5,
                "cpm": 0.2,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LIFETIME,
                "cpc": None,
                "cpm": 0.8,
            },
            {
                "ad_group_id": 321,
                "source_id": 32,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.1,
                "cpm": 0.2,
            },
            {
                "ad_group_id": 321,
                "source_id": 21,
                "publisher": "pub3.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "cpc": 0.2,
                "cpm": 0.1,
            },
            {
                "ad_group_id": None,
                "source_id": 12,
                "publisher": "pub4.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": None,
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                "source_id": None,
                "publisher": "pub4.com",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {"ad_group_id": 321, "publisher": "pub5", "window_key": None, "cpc": 0.5, "cpm": 0.7},
        ]
        formatted_stats = service._format_stats(target_type, stats)
        self.assertEqual(
            {
                123: {
                    "pub1.com__12": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    },
                    "pub2.com__12": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    },
                },
                321: {
                    "pub1.com__32": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    },
                    "pub3.com__21": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    },
                },
            },
            formatted_stats,
        )
