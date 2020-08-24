import datetime

import mock
from django.test import TestCase

import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import RuleCondition
from .. import RuleTriggerHistory
from .. import constants
from . import apply
from . import exceptions
from .actions import ValueChangeData


class ApplyTest(TestCase):
    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_on_cooldown(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = True
        conditions_mock.return_value = True

        changes = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)

        self.assertEqual(3, cooldown_mock.call_count)
        conditions_mock.assert_not_called()
        apply_mock.assert_not_called()
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_does_not_meet_conditions(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = False

        changes = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)

        self.assertEqual(3, cooldown_mock.call_count)
        self.assertEqual(3, conditions_mock.call_count)
        apply_mock.assert_not_called()
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_ad_archived(self, cooldown_mock, conditions_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad1 = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, archived=True)
        ad2 = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, archived=True)
        ad3 = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, archived=True)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF)
        stats = {str(ad1.id): {}, str(ad2.id): {}, str(ad3.id): {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = True

        changes = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)

        self.assertEqual(3, cooldown_mock.call_count)
        self.assertEqual(3, conditions_mock.call_count)
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_archived(self, cooldown_mock, conditions_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, archived=True)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        with self.assertRaises(exceptions.RuleArchived):
            apply.apply_rule(rule, ad_group, stats, {}, {}, {})

    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_invalid_target_error(self, cooldown_mock, conditions_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF)
        stats = {"-1": {}, "-2": {}, str(ad.id): {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = True

        with self.assertRaisesRegex(Exception, "Invalid ad turn off target"):
            apply.apply_rule(rule, ad_group, stats, {}, {}, {})

        self.assertEqual(0, RuleTriggerHistory.objects.count())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_no_changes(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = True
        apply_mock.return_value = ValueChangeData(target="test", old_value=1.0, new_value=1.0)

        changes = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)

        self.assertEqual(3, cooldown_mock.call_count)
        self.assertEqual(3, conditions_mock.call_count)
        self.assertEqual(3, apply_mock.call_count)
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_write_trigger_history(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = True
        apply_mock.return_value = ValueChangeData(target="test", old_value=1.0, new_value=2.0)

        changes = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertEqual(3, len(changes))

        self.assertEqual(3, cooldown_mock.call_count)
        self.assertEqual(3, conditions_mock.call_count)
        self.assertEqual(3, apply_mock.call_count)
        self.assertEqual(3, RuleTriggerHistory.objects.all().count())
        self.assertTrue(
            RuleTriggerHistory.objects.filter(ad_group=ad_group, rule=rule, target="publisher1.com__234").exists()
        )
        self.assertTrue(
            RuleTriggerHistory.objects.filter(ad_group=ad_group, rule=rule, target="publisher2.com__345").exists()
        )
        self.assertTrue(
            RuleTriggerHistory.objects.filter(ad_group=ad_group, rule=rule, target="publisher3.com__456").exists()
        )

    def test_apply_content_ad_rule_budget_settings(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.01,
            change_limit=1.5,
            cooldown=24,
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=None,
            left_operand_type=constants.MetricType.AD_GROUP_NAME,
            left_operand_modifier=None,
            operator=constants.Operator.CONTAINS,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="name",
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=None,
            left_operand_type=constants.MetricType.AD_TITLE,
            left_operand_modifier=None,
            operator=constants.Operator.CONTAINS,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="title",
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=None,
            left_operand_type=constants.MetricType.CAMPAIGN_REMAINING_BUDGET,
            left_operand_modifier=None,
            operator=constants.Operator.LESS_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1000",
        )

        stats = {str(ad.id): {}}
        ad_group_settings = {constants.METRIC_SETTINGS_MAPPING[constants.MetricType.AD_GROUP_NAME]: "ad group name"}
        content_ad_settings = {ad.id: {constants.METRIC_SETTINGS_MAPPING[constants.MetricType.AD_TITLE]: "ad title"}}
        budgets_data = {"campaign_remaining_budget": 500}

        changes = apply.apply_rule(rule, ad_group, stats, ad_group_settings, content_ad_settings, budgets_data)
        self.assertEqual(changes, [ValueChangeData(target=str(ad.id), old_value=1.0, new_value=1.01)])

    @mock.patch("utils.dates_helper.utc_now")
    def test_is_on_cooldown(self, mock_now):
        mock_now.return_value = datetime.datetime.now()

        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, cooldown=48)
        target = "publisher1.com__234"
        magic_mixer.blend(
            RuleTriggerHistory, ad_group=ad_group, rule=rule, target=target, triggered_dt=datetime.datetime.utcnow()
        )

        utc_now = datetime.datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        local_now = dates_helper.utc_to_local(utc_now)

        # calculation of midnight instead of setting it directly is done to account for DST
        local_midnight_in_2_days = (local_now + datetime.timedelta(days=2)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        mock_utc_now = dates_helper.local_to_utc_time(local_midnight_in_2_days)

        mock_now.return_value = mock_utc_now - datetime.timedelta(minutes=1)
        self.assertTrue(apply._is_on_cooldown(target, rule, ad_group))

        mock_now.return_value = mock_utc_now
        self.assertFalse(apply._is_on_cooldown(target, rule, ad_group))

    def test_meet_all_conditions_left_operand_stats(self):
        rule = magic_mixer.blend(Rule)
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_3_DAYS,
            left_operand_type=constants.MetricType.CLICKS,
            left_operand_modifier=2.0,
            operator=constants.Operator.GREATER_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="10",
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_60_DAYS,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            operator=constants.Operator.LESS_THAN,
            right_operand_window=constants.MetricWindow.LAST_DAY,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
        )

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        self.assertTrue(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 5},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 0.9, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 5},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 0.9, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: None, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LAST_60_DAYS: None},
        }
        self.assertTrue(apply._meets_all_conditions(rule, stats, {}))

    def test_stats_condition_left_operand_window_none(self):
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, window=constants.MetricWindow.LAST_3_DAYS
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=None,
            left_operand_type=constants.MetricType.CLICKS,
            left_operand_modifier=2.0,
            operator=constants.Operator.GREATER_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="10",
        )

        stats = {"clicks": {constants.MetricWindow.LAST_3_DAYS: 7}}
        self.assertTrue(apply._meets_all_conditions(rule, stats, {}))

    def test_stats_condition_right_operand_window_none(self):
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, window=constants.MetricWindow.LAST_3_DAYS
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_60_DAYS,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            operator=constants.Operator.LESS_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
        )

        stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_3_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0}
        }
        self.assertTrue(apply._meets_all_conditions(rule, stats, {}))

    def test_stats_cpa_metrics_missing(self):
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, window=constants.MetricWindow.LAST_3_DAYS
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_60_DAYS,
            left_operand_type=constants.MetricType.AVG_COST_PER_CONVERSION,
            operator=constants.Operator.LESS_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
        )

        stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_3_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0}
        }
        with self.assertRaisesRegexp(ValueError, "Missing conversion statistics - campaign possibly missing cpa goal"):
            apply._meets_all_conditions(rule, stats, {})

    def test_stats_window_data_missing(self):
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, window=constants.MetricWindow.LAST_30_DAYS
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_3_DAYS,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            operator=constants.Operator.LESS_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="5.0",
        )

        stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_30_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0}
        }
        self.assertTrue(apply._meets_all_conditions(rule, stats, {}))

    def test_stats_window_avg_data_missing(self):
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, window=constants.MetricWindow.LAST_30_DAYS
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_3_DAYS,
            left_operand_type=constants.MetricType.AVG_CPC,
            operator=constants.Operator.LESS_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="5.0",
        )

        stats = {
            "local_etfm_cpc": {constants.MetricWindow.LAST_30_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0}
        }

        # should evaluate to False since avg data is unknown and thus not comparable
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

    def test_meet_all_conditions_invalid_operator(self):
        rule = magic_mixer.blend(Rule)
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_3_DAYS,
            left_operand_type=constants.MetricType.CLICKS,
            left_operand_modifier=2.0,
            operator=constants.Operator.GREATER_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="10",
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_60_DAYS,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            operator=constants.Operator.CONTAINS,
            right_operand_window=constants.MetricWindow.LAST_DAY,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
        )

        with self.assertRaisesRegexp(ValueError, "Invalid operator for left operand"):
            apply._meets_all_conditions(rule, {}, {})

    def test_meets_condition(self):
        test_cases = [
            (constants.Operator.EQUALS, 1.5, 1.5, True),
            (constants.Operator.EQUALS, 1.5, 1.7, False),
            (constants.Operator.NOT_EQUALS, 1.5, 1.7, True),
            (constants.Operator.NOT_EQUALS, 1.5, 1.5, False),
            (constants.Operator.LESS_THAN, 1.3, 1.5, True),
            (constants.Operator.LESS_THAN, 1.5, 1.5, False),
            (constants.Operator.GREATER_THAN, 1.5, 1.3, True),
            (constants.Operator.GREATER_THAN, 1.5, 1.5, False),
            (constants.Operator.EQUALS, datetime.date(2020, 1, 1), datetime.date(2020, 1, 1), True),
            (constants.Operator.EQUALS, datetime.date(2020, 1, 1), datetime.date(2021, 1, 1), False),
            (constants.Operator.NOT_EQUALS, datetime.date(2020, 1, 1), datetime.date(2021, 1, 1), True),
            (constants.Operator.NOT_EQUALS, datetime.date(2020, 1, 1), datetime.date(2020, 1, 1), False),
            (constants.Operator.LESS_THAN, datetime.date(2020, 1, 1), datetime.date(2021, 1, 1), True),
            (constants.Operator.LESS_THAN, datetime.date(2021, 1, 1), datetime.date(2020, 1, 1), False),
            (constants.Operator.GREATER_THAN, datetime.date(2021, 1, 1), datetime.date(2020, 1, 1), True),
            (constants.Operator.GREATER_THAN, datetime.date(2020, 1, 1), datetime.date(2021, 1, 1), False),
            (constants.Operator.CONTAINS, "abcd", "bc", True),
            (constants.Operator.CONTAINS, "abcd", "e", False),
            (constants.Operator.NOT_CONTAINS, "abcd", "e", True),
            (constants.Operator.NOT_CONTAINS, "abcd", "bc", False),
            (constants.Operator.STARTS_WITH, "abcd", "ab", True),
            (constants.Operator.STARTS_WITH, "abcd", "bc", False),
            (constants.Operator.ENDS_WITH, "abcd", "cd", True),
            (constants.Operator.ENDS_WITH, "abcd", "bc", False),
        ]

        for operator, left_value, right_value, result in test_cases:
            self.assertEqual(result, apply._meets_condition(operator, left_value, right_value))

        with self.assertRaises(ValueError):
            apply._meets_condition(1234, 1, 2)


class SettingsOperandTest(TestCase):
    def setUp(self):
        self.rule = magic_mixer.blend(Rule)

    def test_left_operand_number_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.DAYS_SINCE_ACCOUNT_CREATED,
            operator=constants.Operator.GREATER_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1",
        )
        settings_dict = {"days_since_account_created": 23}
        self.assertTrue(apply._meets_all_conditions(self.rule, {}, settings_dict))

    def test_left_operand_string_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.ACCOUNT_NAME,
            operator=constants.Operator.CONTAINS,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="exceptional",
        )
        settings_dict = {"account_name": "My exceptionally performing account"}
        self.assertTrue(apply._meets_all_conditions(self.rule, {}, settings_dict))

    def test_left_operand_date_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.ACCOUNT_CREATED_DATE,
            operator=constants.Operator.GREATER_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1999-12-31",
        )
        settings_dict = {"account_created_date": datetime.date(2000, 1, 1)}
        self.assertTrue(apply._meets_all_conditions(self.rule, {}, settings_dict))

    def test_left_operand_date_type_with_date_modifier(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.ACCOUNT_CREATED_DATE,
            left_operand_modifier=1,
            operator=constants.Operator.LESS_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1999-12-31",
        )
        settings_dict = {"account_created_date": datetime.date(1999, 12, 30)}
        self.assertFalse(apply._meets_all_conditions(self.rule, {}, settings_dict))

    def test_left_operand_date_type_with_date_modifier_negative(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.ACCOUNT_CREATED_DATE,
            left_operand_modifier=-1,
            operator=constants.Operator.GREATER_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1999-12-31",
        )
        settings_dict = {"account_created_date": datetime.date(2000, 1, 1)}
        self.assertFalse(apply._meets_all_conditions(self.rule, {}, settings_dict))

    def test_left_operand_constant_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.CAMPAIGN_TYPE,
            operator=constants.Operator.EQUALS,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1",
        )
        settings_dict = {"campaign_type": dash.constants.CampaignType.CONTENT}
        self.assertTrue(apply._meets_all_conditions(self.rule, {}, settings_dict))

    def test_left_operand_ad_group_end_date(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.AD_GROUP_END_DATE,
            operator=constants.Operator.LESS_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="2002-01-01",
        )
        settings_dict = {
            "ad_group_end_date": datetime.date(2003, 1, 1),
            "campaign_budget_end_date": datetime.date(2000, 1, 1),
        }
        self.assertFalse(apply._meets_all_conditions(self.rule, {}, settings_dict))

    def test_left_operand_ad_group_end_date_none(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.AD_GROUP_END_DATE,
            operator=constants.Operator.LESS_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="2002-01-01",
        )
        settings_dict = {"ad_group_end_date": None, "campaign_budget_end_date": datetime.date(2000, 1, 1)}
        self.assertTrue(apply._meets_all_conditions(self.rule, {}, settings_dict))
