import datetime
from unittest import mock

import pytz
from django.urls import reverse
from rest_framework import status

import automation.rules
import core.features.publisher_groups
import core.models
import dash.constants
import restapi.common.views_base_test_case
import utils.test_helper
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class RuleViewSetTest(restapi.common.views_base_test_case.RESTAPITestCase):
    def setUp(self):
        super().setUp()
        utils.test_helper.add_permissions(self.user, ["fea_can_create_automation_rules"])

        self.request = get_request_mock(self.user)
        self.agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=self.agency)

        self.rule = automation.rules.Rule.objects.create(
            self.request,
            agency=self.agency,
            name="Test rule",
            target_type=automation.rules.TargetType.PUBLISHER,
            action_type=automation.rules.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.01,
            change_limit=2.50,
            cooldown=24,
            send_email_subject=None,
            send_email_body=None,
            send_email_recipients=[],
            window=automation.rules.MetricWindow.LAST_30_DAYS,
            notification_type=automation.rules.NotificationType.ON_RULE_ACTION_TRIGGERED,
            notification_recipients=["test@test.com"],
            ad_groups_included=[self.ad_group],
            campaigns_included=[],
            accounts_included=[],
            conditions=[
                {
                    "left_operand_window": automation.rules.MetricWindow.LAST_30_DAYS,
                    "left_operand_type": automation.rules.MetricType.TOTAL_SPEND,
                    "left_operand_modifier": None,
                    "conversion_pixel": None,
                    "conversion_pixel_window": None,
                    "conversion_pixel_attribution": None,
                    "operator": automation.rules.Operator.GREATER_THAN,
                    "right_operand_window": None,
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
        account_id=None,
        name,
        state,
        ad_groups_included,
        campaigns_included,
        accounts_included,
        target_type,
        action_type,
        window,
        change_step,
        change_limit,
        send_email_subject,
        send_email_body,
        send_email_recipients,
        cooldown,
        notification_type,
        notification_recipients,
        publisher_group_id,
        conditions,
        archived=False,
    ):
        agency = core.models.Agency.objects.get(id=agency_id) if agency_id else None
        account = core.models.Account.objects.get(id=account_id) if account_id else None
        representation = {
            "name": name,
            "state": automation.rules.RuleState.get_name(state),
            "agencyId": agency_id,
            "agencyName": agency.name if agency else "",
            "accountId": account_id,
            "entities": {
                "adGroups": {
                    "included": [{"id": str(ag.id), "name": ag.settings.ad_group_name} for ag in ad_groups_included]
                },
                "campaigns": {
                    "included": [
                        {"id": str(campaign.id), "name": campaign.settings.name} for campaign in campaigns_included
                    ]
                },
                "accounts": {
                    "included": [
                        {"id": str(account.id), "name": account.settings.name} for account in accounts_included
                    ]
                },
            },
            "accountName": account.settings.name if account else "",
            "targetType": automation.rules.TargetType.get_name(target_type),
            "actionType": automation.rules.ActionType.get_name(action_type),
            "window": automation.rules.MetricWindow.get_name(window),
            "changeStep": change_step,
            "changeLimit": change_limit,
            "sendEmailSubject": send_email_subject,
            "sendEmailBody": send_email_body,
            "sendEmailRecipients": send_email_recipients,
            "actionFrequency": cooldown,
            "notificationType": automation.rules.NotificationType.get_name(notification_type),
            "notificationRecipients": notification_recipients,
            "publisherGroupId": publisher_group_id,
            "conditions": [cls.rule_condition_repr(**condition) for condition in conditions],
            "archived": archived,
        }
        if id is not None:
            representation["id"] = str(id)
        if agency_id is not None:
            representation["agencyId"] = str(agency_id)
        if account_id is not None:
            representation["accountId"] = str(account_id)
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
        conversion_pixel=None,
        conversion_pixel_window=None,
        conversion_pixel_attribution=None,
    ):
        representation = {
            "operator": automation.rules.Operator.get_name(operator),
            "metric": {
                "type": automation.rules.MetricType.get_name(left_operand_type),
                "window": automation.rules.MetricWindow.get_name(left_operand_window) if left_operand_window else None,
                "modifier": left_operand_modifier,
                "conversionPixel": conversion_pixel,
                "conversionPixelWindow": dash.constants.ConversionWindows.get_name(conversion_pixel_window)
                if conversion_pixel_window
                else None,
                "conversionPixelAttribution": dash.constants.ConversionType.get_name(conversion_pixel_attribution)
                if conversion_pixel_attribution
                else None,
            },
            "value": {
                "type": automation.rules.ValueType.get_name(right_operand_type),
                "window": automation.rules.MetricWindow.get_name(right_operand_window)
                if right_operand_window
                else None,
                "value": str(right_operand_value),
            },
        }
        return cls.normalize(representation)

    def validate_against_db(self, rule):
        rule_db = automation.rules.Rule.objects.get(id=rule["id"])
        expected = self.rule_repr(
            id=rule_db.id,
            agency_id=rule_db.agency_id,
            account_id=rule_db.account_id,
            name=rule_db.name,
            state=rule_db.state,
            ad_groups_included=rule_db.ad_groups_included.all(),
            campaigns_included=rule_db.campaigns_included.all(),
            accounts_included=rule_db.accounts_included.all(),
            target_type=rule_db.target_type,
            action_type=rule_db.action_type,
            window=rule_db.window,
            change_step=rule_db.change_step,
            change_limit=rule_db.change_limit,
            send_email_subject=rule_db.send_email_subject,
            send_email_body=rule_db.send_email_body,
            send_email_recipients=rule_db.send_email_recipients,
            cooldown=rule_db.cooldown,
            notification_type=rule_db.notification_type,
            notification_recipients=rule_db.notification_recipients,
            publisher_group_id=rule_db.publisher_group_id,
            conditions=[
                {
                    "operator": condition.operator,
                    "left_operand_type": condition.left_operand_type,
                    "left_operand_window": condition.left_operand_window,
                    "left_operand_modifier": condition.left_operand_modifier,
                    "right_operand_type": condition.right_operand_type,
                    "right_operand_window": condition.right_operand_window,
                    "right_operand_value": condition.right_operand_value,
                    "conversion_pixel": condition.conversion_pixel,
                    "conversion_pixel_window": condition.conversion_pixel_window,
                    "conversion_pixel_attribution": condition.conversion_pixel_attribution,
                }
                for condition in rule_db.conditions.all()
            ],
        )
        self.assertEqual(expected, rule)

    def test_get(self):
        response = self.client.get(reverse("restapi.rules.internal:rules_details", kwargs={"rule_id": self.rule.id}))
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK)
        self.validate_against_db(result["data"])

    def test_list(self):
        response = self.client.get(reverse("restapi.rules.internal:rules_list"), {"agency_id": self.agency.id})
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(1, result["count"])
        self.assertEqual(None, result["next"])
        for rule in result["data"]:
            self.validate_against_db(rule)

    def test_list_agency_rules(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        another_agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_on_agency = magic_mixer.blend(core.models.Account, agency=agency)
        account_on_another_agency = magic_mixer.blend(core.models.Account, agency=another_agency)

        rules_with_agency = magic_mixer.cycle(3).blend(automation.rules.Rule, agency=agency)
        magic_mixer.cycle(3).blend(automation.rules.Rule, agency=another_agency)
        rules_with_account_on_agency = magic_mixer.cycle(3).blend(automation.rules.Rule, account=account_on_agency)
        magic_mixer.cycle(3).blend(automation.rules.Rule, account=account_on_another_agency)

        response = self.client.get(reverse("restapi.rules.internal:rules_list"), {"agency_id": agency.id})
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rules_with_agency] + [
            item.id for item in rules_with_account_on_agency
        ]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_agency_only_rules(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        another_agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_on_agency = magic_mixer.blend(core.models.Account, agency=agency)
        account_on_another_agency = magic_mixer.blend(core.models.Account, agency=another_agency)

        rules_with_agency = magic_mixer.cycle(3).blend(automation.rules.Rule, agency=agency)
        magic_mixer.cycle(3).blend(automation.rules.Rule, agency=another_agency)
        magic_mixer.cycle(3).blend(automation.rules.Rule, account=account_on_agency)
        magic_mixer.cycle(3).blend(automation.rules.Rule, account=account_on_another_agency)

        response = self.client.get(
            reverse("restapi.rules.internal:rules_list"), {"agency_id": agency.id, "agency_only": True}
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rules_with_agency]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_account_rules(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_on_agency = magic_mixer.blend(core.models.Account, agency=agency)

        rules_with_agency = magic_mixer.cycle(3).blend(automation.rules.Rule, agency=agency)
        rules_with_account = magic_mixer.cycle(3).blend(automation.rules.Rule, account=account_on_agency)

        response = self.client.get(reverse("restapi.rules.internal:rules_list"), {"account_id": account_on_agency.id})
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rules_with_account] + [item.id for item in rules_with_agency]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_with_keyword(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])

        magic_mixer.blend(automation.rules.Rule, agency=agency, name="Rule 1")
        magic_mixer.blend(automation.rules.Rule, agency=agency, name="Rule 2")
        magic_mixer.blend(automation.rules.Rule, agency=agency, name="Rule test 3")

        r = self.client.get(reverse("restapi.rules.internal:rules_list"), {"keyword": "test", "agencyId": agency.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 1)

        r = self.client.get(reverse("restapi.rules.internal:rules_list"), {"keyword": "rule", "agencyId": agency.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 3)

    def test_create(self):
        rule_data = self.rule_repr(
            name="New test rule",
            state=automation.rules.RuleState.ENABLED,
            agency_id=self.agency.id,
            ad_groups_included=[self.ad_group],
            campaigns_included=[],
            accounts_included=[],
            target_type=automation.rules.TargetType.PUBLISHER,
            action_type=automation.rules.ActionType.DECREASE_BID_MODIFIER,
            window=5,
            change_step=0.11,
            change_limit=0.05,
            send_email_subject=None,
            send_email_body=None,
            send_email_recipients=[],
            cooldown=48,
            notification_type=automation.rules.NotificationType.ON_RULE_RUN,
            notification_recipients=["user@domain.com"],
            publisher_group_id=None,
            conditions=[
                {
                    "left_operand_type": automation.rules.MetricType.AVG_CPC,
                    "left_operand_window": automation.rules.MetricWindow.LAST_7_DAYS,
                    "left_operand_modifier": None,
                    "operator": automation.rules.Operator.GREATER_THAN,
                    "right_operand_type": automation.rules.ValueType.ABSOLUTE,
                    "right_operand_window": None,
                    "right_operand_value": "2.22",
                }
            ],
        )
        response = self.client.post(reverse("restapi.rules.internal:rules_list"), data=rule_data, format="json")
        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED)
        self.validate_against_db(result["data"])

    def test_create_publisher_group(self):
        other_agency = magic_mixer.blend(core.models.Agency)
        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=other_agency, name="test pub group"
        )
        rule_data = self.rule_repr(
            name="New test rule",
            state=automation.rules.RuleState.ENABLED,
            agency_id=self.agency.id,
            ad_groups_included=[self.ad_group],
            campaigns_included=[],
            accounts_included=[],
            target_type=automation.rules.TargetType.PUBLISHER,
            action_type=automation.rules.ActionType.ADD_TO_PUBLISHER_GROUP,
            window=5,
            change_step=None,
            change_limit=None,
            send_email_subject=None,
            send_email_body=None,
            send_email_recipients=[],
            cooldown=48,
            notification_type=automation.rules.NotificationType.ON_RULE_RUN,
            notification_recipients=["user@domain.com"],
            publisher_group_id=invalid_publisher_group.id,
            conditions=[
                {
                    "left_operand_type": automation.rules.MetricType.AVG_CPC,
                    "left_operand_window": automation.rules.MetricWindow.LAST_7_DAYS,
                    "left_operand_modifier": None,
                    "operator": automation.rules.Operator.GREATER_THAN,
                    "right_operand_type": automation.rules.ValueType.ABSOLUTE,
                    "right_operand_window": None,
                    "right_operand_value": "2.22",
                }
            ],
        )

        response = self.client.post(reverse("restapi.rules.internal:rules_list"), data=rule_data, format="json")
        result = self.assertResponseError(response, "MissingDataError")

        valid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=self.agency, name="test pub group"
        )
        rule_data["publisher_group_id"] = valid_publisher_group.id

        response = self.client.post(reverse("restapi.rules.internal:rules_list"), data=rule_data, format="json")
        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED)
        self.validate_against_db(result["data"])

    def test_put(self):
        response = self.client.put(
            reverse("restapi.rules.internal:rules_details", kwargs={"rule_id": self.rule.id}),
            data={"agencyId": self.agency.id, "changeStep": "0.02"},
            format="json",
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK)
        self.validate_against_db(result["data"])


class RuleHistoryViewSetTest(restapi.common.views_base_test_case.RESTAPITestCase):
    def test_list_account_rules_histories(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_on_agency = magic_mixer.blend(core.models.Account, agency=agency)

        rule_with_agency = magic_mixer.blend(automation.rules.Rule, agency=agency)
        rule_with_account_on_agency = magic_mixer.blend(automation.rules.Rule, account=account_on_agency)

        magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule_with_agency)
        rule_histories_with_account_on_agency = magic_mixer.cycle(3).blend(
            automation.rules.RuleHistory, rule=rule_with_account_on_agency
        )

        response = self.client.get(
            reverse("restapi.rules.internal:rules_history"), {"account_id": account_on_agency.id}
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rule_histories_with_account_on_agency]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_agency_rules_histories(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        another_agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_on_agency = magic_mixer.blend(core.models.Account, agency=agency)
        account_on_another_agency = magic_mixer.blend(core.models.Account, agency=another_agency)

        rule_with_agency = magic_mixer.blend(automation.rules.Rule, agency=agency)
        rule_with_another_agency = magic_mixer.blend(automation.rules.Rule, agency=another_agency)
        rule_with_account_on_agency = magic_mixer.blend(automation.rules.Rule, account=account_on_agency)
        rule_with_account_on_another_agency = magic_mixer.blend(
            automation.rules.Rule, account=account_on_another_agency
        )

        rule_histories_with_agency = magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule_with_agency)
        magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule_with_another_agency)
        rule_histories_with_account_on_agency = magic_mixer.cycle(3).blend(
            automation.rules.RuleHistory, rule=rule_with_account_on_agency
        )
        magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule_with_account_on_another_agency)

        response = self.client.get(reverse("restapi.rules.internal:rules_history"), {"agency_id": agency.id})
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rule_histories_with_agency] + [
            item.id for item in rule_histories_with_account_on_agency
        ]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_rule_rules_histories(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])

        rule = magic_mixer.blend(automation.rules.Rule, agency=agency)

        rule_histories = magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule)
        magic_mixer.cycle(3).blend(automation.rules.RuleHistory)

        response = self.client.get(
            reverse("restapi.rules.internal:rules_history"), {"agency_id": agency.id, "rule_id": rule.id}
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rule_histories]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_ad_group_rules_histories(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(core.models.AdGroup)

        rule = magic_mixer.blend(automation.rules.Rule, agency=agency)

        rule_histories = magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule, ad_group=ad_group)
        magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule)

        response = self.client.get(
            reverse("restapi.rules.internal:rules_history"), {"agency_id": agency.id, "ad_group_id": ad_group.id}
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rule_histories]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_start_date_rules_histories(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])

        rule = magic_mixer.blend(automation.rules.Rule, agency=agency)

        mocked = datetime.datetime(2020, 3, 1, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            rule_histories = magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule)

        mocked = datetime.datetime(2019, 12, 1, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule)

        response = self.client.get(
            reverse("restapi.rules.internal:rules_history"), {"agency_id": agency.id, "start_date": "2020-01-01"}
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rule_histories]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_end_date_rules_histories(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])

        rule = magic_mixer.blend(automation.rules.Rule, agency=agency)

        mocked = datetime.datetime(2020, 3, 1, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            rule_histories = magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule)

        mocked = datetime.datetime(2020, 6, 1, 0, 0, 0, tzinfo=pytz.utc)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
            magic_mixer.cycle(3).blend(automation.rules.RuleHistory, rule=rule)

        response = self.client.get(
            reverse("restapi.rules.internal:rules_history"), {"agency_id": agency.id, "end_date": "2020-05-01"}
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rule_histories]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_rule_rules_histories_without_changes(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])

        rule = magic_mixer.blend(
            automation.rules.Rule,
            agency=agency,
            target_type=automation.rules.TargetType.COUNTRY,
            action_type=automation.rules.ActionType.INCREASE_BID_MODIFIER,
        )

        rule_histories = magic_mixer.cycle(3).blend(
            automation.rules.RuleHistory, rule=rule, changes={"UK": {"old_value": 0.1, "new_value": 0.2}}
        )
        magic_mixer.cycle(3).blend(
            automation.rules.RuleHistory, changes={}, status=automation.rules.ApplyStatus.SUCCESS
        )

        response = self.client.get(
            reverse("restapi.rules.internal:rules_history"),
            {"agency_id": agency.id, "rule_id": rule.id, "show_entries_without_changes": False},
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)

        response_ids = [int(item.get("id")) for item in result["data"]]
        expected_response_ids = [item.id for item in rule_histories]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))
