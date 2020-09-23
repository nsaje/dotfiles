import datetime
import decimal

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
    def test_apply_rule_on_cooldown(self, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, cooldown=24, target_type=constants.TargetType.PUBLISHER)
        RuleTriggerHistory.objects.create(rule=rule, ad_group=ad_group, target="publisher1.com__234")
        RuleTriggerHistory.objects.create(rule=rule, ad_group=ad_group, target="publisher2.com__345")
        RuleTriggerHistory.objects.create(rule=rule, ad_group=ad_group, target="publisher3.com__456")
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        conditions_mock.return_value = True

        changes, condition_values = apply.apply_rule(rule, ad_group, stats, {}, {}, {}, None)
        self.assertFalse(changes)
        self.assertFalse(condition_values)

        conditions_mock.assert_not_called()
        apply_mock.assert_not_called()

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    def test_apply_rule_does_not_meet_conditions(self, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, cooldown=24)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        conditions_mock.return_value = False

        changes, condition_values = apply.apply_rule(rule, ad_group, stats, {}, {}, {}, None)
        self.assertFalse(changes)
        self.assertFalse(condition_values)

        self.assertEqual(3, conditions_mock.call_count)
        apply_mock.assert_not_called()
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    def test_apply_rule_ad_archived(self, conditions_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad1 = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, archived=True)
        ad2 = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, archived=True)
        ad3 = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, archived=True)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF, cooldown=24
        )
        stats = {str(ad1.id): {}, str(ad2.id): {}, str(ad3.id): {}}

        conditions_mock.return_value = True

        changes, condition_values = apply.apply_rule(rule, ad_group, stats, {}, {}, {}, None)
        self.assertFalse(changes)
        self.assertFalse(condition_values)

        self.assertEqual(3, conditions_mock.call_count)
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    def test_apply_rule_archived(self, conditions_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, archived=True)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        with self.assertRaises(exceptions.RuleArchived):
            apply.apply_rule(rule, ad_group, stats, {}, {}, {}, None)

    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    def test_apply_rule_invalid_target_error(self, conditions_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF, cooldown=24
        )
        stats = {"-1": {}, "-2": {}, str(ad.id): {}}

        conditions_mock.return_value = True

        with self.assertRaisesRegex(Exception, "Invalid ad turn off target"):
            apply.apply_rule(rule, ad_group, stats, {}, {}, {}, None)

        self.assertEqual(0, RuleTriggerHistory.objects.count())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    def test_apply_rule_no_changes(self, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, cooldown=24)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        conditions_mock.return_value = True
        apply_mock.return_value = ValueChangeData(target="test", old_value=1.0, new_value=1.0)

        changes, condition_values = apply.apply_rule(rule, ad_group, stats, {}, {}, {}, None)
        self.assertFalse(changes)
        self.assertFalse(condition_values)

        self.assertEqual(3, conditions_mock.call_count)
        self.assertEqual(3, apply_mock.call_count)
        self.assertFalse(RuleTriggerHistory.objects.exists())

    @mock.patch("automation.rules.service.apply._apply_action")
    @mock.patch("automation.rules.service.apply._meets_all_conditions")
    def test_apply_rule_write_trigger_history(self, conditions_mock, apply_mock):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, cooldown=24)
        stats = {"publisher1.com__234": {}, "publisher2.com__345": {}, "publisher3.com__456": {}}

        conditions_mock.return_value = True
        apply_mock.return_value = ValueChangeData(target="test", old_value=1.0, new_value=2.0)

        changes, condition_values = apply.apply_rule(rule, ad_group, stats, {}, {}, {}, None)
        self.assertEqual(3, len(changes))

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
        condition_1 = magic_mixer.blend(
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
        condition_2 = magic_mixer.blend(
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
        condition_3 = magic_mixer.blend(
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

        changes, condition_values = apply.apply_rule(
            rule, ad_group, stats, ad_group_settings, content_ad_settings, budgets_data, None
        )
        self.assertEqual(changes, [ValueChangeData(target=str(ad.id), old_value=1.0, new_value=1.01)])
        self.assertEqual(
            condition_values,
            {
                str(ad.id): {
                    str(condition_1.id): apply.ConditionValues(
                        left_operand_value="ad group name", right_operand_value="name"
                    ),
                    str(condition_2.id): apply.ConditionValues(
                        left_operand_value="ad title", right_operand_value="title"
                    ),
                    str(condition_3.id): apply.ConditionValues(
                        left_operand_value=500, right_operand_value=decimal.Decimal("1000")
                    ),
                }
            },
        )

    @mock.patch("utils.dates_helper.utc_now")
    def test_prefetch_targets_on_cooldown(self, mock_now):
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
        self.assertTrue(target in apply._prefetch_targets_on_cooldown(rule, ad_group))

        mock_now.return_value = mock_utc_now
        self.assertFalse(target in apply._prefetch_targets_on_cooldown(rule, ad_group))

    def test_meet_all_conditions_left_operand_stats(self):
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER)
        condition_1 = magic_mixer.blend(
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
        condition_2 = magic_mixer.blend(
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
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertEqual(computed, {condition_1: (14.0, 10.0), condition_2: (10.0, 11.0)})
        self.assertTrue(apply._meets_all_conditions(computed))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 5},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertEqual(computed, {condition_1: (10.0, 10.0), condition_2: (10.0, 11.0)})
        self.assertFalse(apply._meets_all_conditions(computed))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 0.9, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertEqual(computed, {condition_1: (14.0, 10.0), condition_2: (10.0, 9.9)})
        self.assertFalse(apply._meets_all_conditions(computed))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 5},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 0.9, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertEqual(computed, {condition_1: (10.0, 10.0), condition_2: (10.0, 9.9)})
        self.assertFalse(apply._meets_all_conditions(computed))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: None, constants.MetricWindow.LAST_60_DAYS: 10.0},
        }
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertEqual(computed, {condition_1: (14.0, 10.0), condition_2: (10.0, None)})
        self.assertFalse(apply._meets_all_conditions(computed))

        stats = {
            "clicks": {constants.MetricWindow.LAST_3_DAYS: 7},
            "local_etfm_cost": {constants.MetricWindow.LAST_DAY: 1.0, constants.MetricWindow.LAST_60_DAYS: None},
        }
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertEqual(computed, {condition_1: (14.0, 10.0), condition_2: (0.0, 11.0)})
        self.assertTrue(apply._meets_all_conditions(computed))

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
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertTrue(apply._meets_all_conditions(computed))

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
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertTrue(apply._meets_all_conditions(computed))

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
            conversion_pixel=None,
            conversion_pixel_window=dash.constants.ConversionWindows.LEQ_7_DAYS,
            conversion_pixel_attribution=constants.ConversionAttributionType.CLICK,
        )

        stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_3_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0}
        }
        with self.assertRaisesRegexp(
            exceptions.NoCPAGoal,
            "Conversion pixel could not be determined from campaign goals - no CPA goal is set on the ad group’s campaign",
        ):
            apply._compute_values_by_condition(rule, stats, {}, None)

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
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertTrue(apply._meets_all_conditions(computed))

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
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        # should evaluate to False since avg data is unknown and thus not comparable
        self.assertFalse(apply._meets_all_conditions(computed))

    def test_meet_all_conditions_invalid_operator(self):
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER)
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
            apply._compute_values_by_condition(rule, {}, {}, None)

    def test_stats_condition_conversions_pixel_specified(self):
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, window=constants.MetricWindow.LAST_3_DAYS
        )
        conversion_pixel = magic_mixer.blend(core.models.ConversionPixel, slug="testslug")
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_7_DAYS,
            left_operand_type=constants.MetricType.CONVERSIONS,
            operator=constants.Operator.GREATER_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
            conversion_pixel=conversion_pixel,
            conversion_pixel_window=dash.constants.ConversionWindows.LEQ_7_DAYS,
            conversion_pixel_attribution=constants.ConversionAttributionType.CLICK,
        )

        stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_3_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0},
            "conversions": {
                constants.MetricWindow.LAST_3_DAYS: {
                    "testslug": {24: {"count_click": 5}, 168: {"count_click": 5}, 720: {"count_click": 5}}
                },
                constants.MetricWindow.LAST_7_DAYS: {
                    "testslug": {24: {"count_click": 15}, 168: {"count_click": 15}, 720: {"count_click": 15}}
                },
            },
        }
        computed = apply._compute_values_by_condition(rule, stats, {}, None)
        self.assertTrue(apply._meets_all_conditions(computed))

    def test_stats_condition_conversions_default_campaign_goal(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        conversion_pixel = magic_mixer.blend(core.models.ConversionPixel, slug="testslug", account=campaign.account)
        campaign_goal = magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=campaign,
            primary=True,
            type=dash.constants.CampaignGoalKPI.CPA,
            conversion_goal__pixel=conversion_pixel,
            conversion_goal__goal_id="testslug",
            conversion_goal__conversion_window=dash.constants.ConversionWindows.LEQ_7_DAYS,
        )
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            window=constants.MetricWindow.LAST_3_DAYS,
            ad_groups_included=[ad_group],
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_7_DAYS,
            left_operand_type=constants.MetricType.CONVERSIONS,
            operator=constants.Operator.GREATER_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
            conversion_pixel=None,
            conversion_pixel_window=dash.constants.ConversionWindows.LEQ_7_DAYS,
            conversion_pixel_attribution=constants.ConversionAttributionType.CLICK,
        )

        stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_3_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0},
            "conversions": {
                constants.MetricWindow.LAST_3_DAYS: {
                    "testslug": {24: {"count_click": 5}, 168: {"count_click": 5}, 720: {"count_click": 5}}
                },
                constants.MetricWindow.LAST_7_DAYS: {
                    "testslug": {24: {"count_click": 15}, 168: {"count_click": 15}, 720: {"count_click": 15}}
                },
            },
        }
        computed = apply._compute_values_by_condition(rule, stats, {}, campaign_goal)
        self.assertTrue(apply._meets_all_conditions(computed))

    def test_stats_condition_conversions_no_default_campaign_goal_exception(self):
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, window=constants.MetricWindow.LAST_3_DAYS
        )
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_window=constants.MetricWindow.LAST_7_DAYS,
            left_operand_type=constants.MetricType.CONVERSIONS,
            operator=constants.Operator.GREATER_THAN,
            right_operand_window=None,
            right_operand_type=constants.ValueType.TOTAL_SPEND,
            right_operand_value="11.0",
            conversion_pixel=None,
            conversion_pixel_window=dash.constants.ConversionWindows.LEQ_7_DAYS,
            conversion_pixel_attribution=constants.ConversionAttributionType.CLICK,
        )

        stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_3_DAYS: 1.0, constants.MetricWindow.LAST_60_DAYS: 10.0},
            "conversions": {},
        }
        with self.assertRaises(exceptions.NoCPAGoal):
            apply._compute_values_by_condition(rule, stats, {}, None)

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
        self.rule = magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER)

    def test_left_operand_number_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.DAYS_SINCE_ACCOUNT_CREATED,
            operator=constants.Operator.GREATER_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1",
        )
        settings_dict = {"days_since_account_created": 23}
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertTrue(apply._meets_all_conditions(computed))

    def test_left_operand_string_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.ACCOUNT_NAME,
            operator=constants.Operator.CONTAINS,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="exceptional",
        )
        settings_dict = {"account_name": "My exceptionally performing account"}
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertTrue(apply._meets_all_conditions(computed))

    def test_left_operand_date_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.ACCOUNT_CREATED_DATE,
            operator=constants.Operator.GREATER_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1999-12-31",
        )
        settings_dict = {"account_created_date": datetime.date(2000, 1, 1)}
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertTrue(apply._meets_all_conditions(computed))

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
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertFalse(apply._meets_all_conditions(computed))

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
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertFalse(apply._meets_all_conditions(computed))

    def test_left_operand_constant_type(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.CAMPAIGN_TYPE,
            operator=constants.Operator.EQUALS,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="1",
        )
        settings_dict = {"campaign_type": dash.constants.CampaignType.CONTENT}
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertTrue(apply._meets_all_conditions(computed))

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
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertFalse(apply._meets_all_conditions(computed))

    def test_left_operand_ad_group_end_date_none(self):
        RuleCondition.objects.create(
            rule=self.rule,
            left_operand_type=constants.MetricType.AD_GROUP_END_DATE,
            operator=constants.Operator.LESS_THAN,
            right_operand_type=constants.ValueType.ABSOLUTE,
            right_operand_value="2002-01-01",
        )
        settings_dict = {"ad_group_end_date": None, "campaign_budget_end_date": datetime.date(2000, 1, 1)}
        computed = apply._compute_values_by_condition(self.rule, {}, settings_dict, None)
        self.assertTrue(apply._meets_all_conditions(computed))
