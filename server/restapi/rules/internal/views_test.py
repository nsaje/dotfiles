from django.urls import reverse
from rest_framework import status

import automation.rules
import core.models
import restapi.common.views_base_test
import utils.test_helper
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer


class RuleViewSetTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super().setUp()
        utils.test_helper.add_permissions(self.user, ["fea_can_create_automation_rules"])

        self.request = get_request_mock(self.user)
        self.agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__agency=self.agency)

        self.rule = automation.rules.Rule.objects.create(
            self.request,
            agency=self.agency,
            name="Test rule",
            target_type=automation.rules.TargetType.PUBLISHER,
            action_type=automation.rules.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.01,
            change_limit=2.50,
            cooldown=24,
            window=automation.rules.MetricWindow.LAST_30_DAYS,
            notification_type=automation.rules.NotificationType.ON_RULE_ACTION_PERFORMED,
            notification_recipients=["test@test.com"],
            ad_groups_included=[self.ad_group],
            conditions=[
                {
                    "left_operand_window": automation.rules.MetricWindow.LAST_30_DAYS,
                    "left_operand_type": automation.rules.MetricType.AVG_COST_PER_MINUTE,
                    "left_operand_modifier": 1.0,
                    "operator": automation.rules.Operator.GREATER_THAN,
                    "right_operand_window": automation.rules.MetricWindow.NOT_APPLICABLE,
                    "right_operand_type": automation.rules.ValueType.ABSOLUTE,
                    "right_operand_value": "100",
                }
            ],
        )

    @classmethod
    def rule_repr(
        cls,
        *,
        id=None,
        agency_id=None,
        name,
        ad_groups_included,
        target_type,
        action_type,
        change_step,
        change_limit,
        cooldown,
        notification_type,
        notification_recipients,
        conditions,
    ):
        representation = {
            "name": name,
            "entities": {"adGroup": {"included": ad_groups_included}},
            "targetType": automation.rules.TargetType.get_name(target_type),
            "actionType": automation.rules.ActionType.get_name(action_type),
            "changeStep": change_step,
            "changeLimit": change_limit,
            "actionFrequency": cooldown,
            "notificationType": automation.rules.NotificationType.get_name(notification_type),
            "notificationRecipients": notification_recipients,
            "conditions": [cls.rule_condition_repr(**condition) for condition in conditions],
        }
        if id is not None:
            representation["id"] = str(id)
        if agency_id is not None:
            representation["agencyId"] = str(agency_id)
        return cls.normalize(representation)

    @classmethod
    def rule_condition_repr(
        cls,
        *,
        operator,
        left_operand_type,
        left_operand_window,
        left_operand_modifier,
        right_operand_type,
        right_operand_window,
        right_operand_value,
    ):
        representation = {
            "operator": automation.rules.Operator.get_name(operator),
            "metric": {
                "type": automation.rules.MetricType.get_name(left_operand_type),
                "window": automation.rules.MetricWindow.get_name(left_operand_window),
                "modifier": left_operand_modifier,
            },
            "value": {
                "type": automation.rules.ValueType.get_name(right_operand_type),
                "window": automation.rules.MetricWindow.get_name(right_operand_window),
                "value": str(right_operand_value),
            },
        }
        return cls.normalize(representation)

    def validate_against_db(self, rule):
        rule_db = automation.rules.Rule.objects.get(id=rule["id"])
        expected = self.rule_repr(
            id=rule_db.id,
            agency_id=rule_db.agency_id,
            name=rule_db.name,
            ad_groups_included=[ag.id for ag in rule_db.ad_groups_included.all()],
            target_type=rule_db.target_type,
            action_type=rule_db.action_type,
            change_step=rule_db.change_step,
            change_limit=rule_db.change_limit,
            cooldown=rule_db.cooldown,
            notification_type=rule_db.notification_type,
            notification_recipients=rule_db.notification_recipients,
            conditions=[
                {
                    "operator": condition.operator,
                    "left_operand_type": condition.left_operand_type,
                    "left_operand_window": condition.left_operand_window,
                    "left_operand_modifier": condition.left_operand_modifier,
                    "right_operand_type": condition.right_operand_type,
                    "right_operand_window": condition.right_operand_window,
                    "right_operand_value": condition.right_operand_value,
                }
                for condition in rule_db.conditions.all()
            ],
        )
        self.assertEqual(expected, rule)

    def test_get(self):
        response = self.client.get(
            reverse(
                "restapi.rules.internal:rules_details", kwargs={"agency_id": self.agency.id, "rule_id": self.rule.id}
            )
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK)
        self.validate_against_db(result["data"])

    def test_list(self):
        response = self.client.get(reverse("restapi.rules.internal:rules_list", kwargs={"agency_id": self.agency.id}))
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(1, result["count"])
        self.assertEqual(None, result["next"])
        for rule in result["data"]:
            self.validate_against_db(rule)

    def test_create(self):
        new_agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        new_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__agency=self.agency)
        rule_data = self.rule_repr(
            name="New test campaign",
            ad_groups_included=[new_ad_group.id],
            target_type=automation.rules.TargetType.COUNTRY,
            action_type=automation.rules.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.11,
            change_limit=0.05,
            cooldown=48,
            notification_type=automation.rules.NotificationType.ON_RULE_TRIGGERED,
            notification_recipients=["user@domain.com"],
            conditions=[
                {
                    "left_operand_type": automation.rules.MetricType.AVG_CPC,
                    "left_operand_window": automation.rules.MetricWindow.LAST_7_DAYS,
                    "left_operand_modifier": 1.0,
                    "operator": automation.rules.Operator.GREATER_THAN,
                    "right_operand_type": automation.rules.ValueType.ABSOLUTE,
                    "right_operand_window": automation.rules.MetricWindow.LAST_7_DAYS,
                    "right_operand_value": "2.22",
                }
            ],
        )
        response = self.client.post(
            reverse("restapi.rules.internal:rules_list", kwargs={"agency_id": new_agency.id}),
            data=rule_data,
            format="json",
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED)
        self.validate_against_db(result["data"])

    def test_put(self):
        response = self.client.put(
            reverse(
                "restapi.rules.internal:rules_details", kwargs={"agency_id": self.agency.id, "rule_id": self.rule.id}
            ),
            data={"changeStep": "0.02"},
            format="json",
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK)
        self.validate_against_db(result["data"])
