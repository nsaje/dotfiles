from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from ... import constants
from . import model


class RuleInstanceTest(TestCase):
    def test_update(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency)
        rule.update(
            request,
            name="Test rule",
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.01,
            change_limit=2.50,
            cooldown=24,
            window=constants.MetricWindow.LAST_30_DAYS,
            notification_type=constants.NotificationType.ON_RULE_ACTION_TRIGGERED,
            notification_recipients=["test@test.com"],
            ad_groups_included=[ad_group],
            conditions=[
                {
                    "left_operand_window": constants.MetricWindow.LAST_30_DAYS,
                    "left_operand_type": constants.MetricType.TOTAL_SPEND,
                    "left_operand_modifier": 1.0,
                    "operator": constants.Operator.GREATER_THAN,
                    "right_operand_window": None,
                    "right_operand_type": constants.ValueType.ABSOLUTE,
                    "right_operand_value": "100",
                }
            ],
        )

        self.assertEqual(request.user, rule.modified_by)
        self.assertEqual(agency, rule.agency)
        self.assertEqual("Test rule", rule.name)
        self.assertEqual(constants.TargetType.PUBLISHER, rule.target_type)
        self.assertEqual(constants.ActionType.INCREASE_BID_MODIFIER, rule.action_type)
        self.assertEqual(0.01, rule.change_step)
        self.assertEqual(2.50, rule.change_limit)
        self.assertEqual(24, rule.cooldown)
        self.assertEqual(constants.MetricWindow.LAST_30_DAYS, rule.window)
        self.assertEqual(constants.NotificationType.ON_RULE_ACTION_TRIGGERED, rule.notification_type)
        self.assertEqual(["test@test.com"], rule.notification_recipients)
        self.assertEqual([ad_group], list(rule.ad_groups_included.all()))

        conditions = list(rule.conditions.all())
        self.assertEqual(1, len(conditions))

        condition = conditions[0]
        self.assertEqual(constants.MetricWindow.LAST_30_DAYS, condition.left_operand_window)
        self.assertEqual(constants.MetricType.TOTAL_SPEND, condition.left_operand_type)
        self.assertEqual(1.0, condition.left_operand_modifier)
        self.assertEqual(constants.Operator.GREATER_THAN, condition.operator)
        self.assertEqual(None, condition.right_operand_window)
        self.assertEqual(constants.ValueType.ABSOLUTE, condition.right_operand_type)
        self.assertEqual("100", condition.right_operand_value)
