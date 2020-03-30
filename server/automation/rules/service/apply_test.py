import datetime

import mock
from django.test import TestCase

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import RuleCondition
from .. import RuleTriggerHistory
from .. import constants
from . import apply
from .actions import ValueChangeData


class ApplyTest(TestCase):
    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_on_cooldown(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = True
        conditions_mock.return_value = True

        changes, errors = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)
        self.assertFalse(errors)

        self.assertEqual(3, cooldown_mock.call_count)
        conditions_mock.assert_not_called()
        apply_mock.assert_not_called()
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_does_not_meet_conditions(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = False

        changes, errors = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)
        self.assertFalse(errors)

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

        changes, errors = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)
        self.assertFalse(errors)

        self.assertEqual(3, cooldown_mock.call_count)
        self.assertEqual(3, conditions_mock.call_count)
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_invalid_target_error(self, cooldown_mock, conditions_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF)
        stats = {"-1": {}, "-2": {}, str(ad.id): {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = True

        changes, errors = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertEqual(1, len(changes))
        self.assertEqual(2, len(errors))
        for error in errors:
            self.assertIn(error.target, ["-1", "-2"])
            self.assertEqual("Invalid ad turn off target", str(error.exc))
            self.assertIn("Invalid ad turn off target", error.stack_trace)

        self.assertEqual(3, cooldown_mock.call_count)
        self.assertEqual(3, conditions_mock.call_count)
        self.assertEqual(1, RuleTriggerHistory.objects.count())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_no_changes(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = True
        apply_mock.return_value = ValueChangeData(target="test", old_value=1.0, new_value=1.0)

        changes, errors = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertFalse(changes)
        self.assertFalse(errors)

        self.assertEqual(3, cooldown_mock.call_count)
        self.assertEqual(3, conditions_mock.call_count)
        self.assertEqual(3, apply_mock.call_count)
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    @mock.patch("automation.rules.service.apply._is_on_cooldown")
    def test_apply_rule_write_trigger_history(self, cooldown_mock, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        cooldown_mock.return_value = False
        conditions_mock.return_value = True
        apply_mock.return_value = ValueChangeData(target="test", old_value=1.0, new_value=2.0)

        changes, errors = apply.apply_rule(rule, ad_group, stats, {}, {}, {})
        self.assertEqual(3, len(changes))
        self.assertFalse(errors)

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

    @mock.patch("utils.dates_helper.local_now")
    def test_is_on_cooldown(self, mock_now):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, cooldown=48)
        target = "publisher1.com__234"
        magic_mixer.blend(
            RuleTriggerHistory, ad_group=ad_group, rule=rule, target=target, triggered_dt=datetime.datetime.now()
        )

        mock_now.return_value = datetime.datetime.now() + datetime.timedelta(hours=47)
        self.assertTrue(apply._is_on_cooldown(target, rule, ad_group))

        mock_now.return_value = datetime.datetime.now() + datetime.timedelta(hours=49)
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
            left_operand_window=constants.MetricWindow.LIFETIME,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            operator=constants.Operator.LESS_THAN,
            right_operand_window=constants.MetricWindow.LAST_DAY,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
        )

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LIFETIME: 10.0},
        }
        self.assertTrue(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 5},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LIFETIME: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 0.9, constants.MetricWindow.LIFETIME: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 5},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 0.9, constants.MetricWindow.LIFETIME: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: None, constants.MetricWindow.LIFETIME: 10.0},
        }
        self.assertFalse(apply._meets_all_conditions(rule, stats, {}))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LIFETIME: None},
        }
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
            left_operand_window=constants.MetricWindow.LIFETIME,
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
