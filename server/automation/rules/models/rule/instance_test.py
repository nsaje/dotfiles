from django.test import TestCase

import core.models
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer

from ... import constants
from . import model


class RuleInstanceTest(TestCase):
    def test_update(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)

        rule = magic_mixer.blend(
            model.Rule,
            agency=agency,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
        )
        rule.update(
            request,
            name="Test rule",
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
                    "left_operand_modifier": None,
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
        self.assertEqual(None, condition.left_operand_modifier)
        self.assertEqual(constants.Operator.GREATER_THAN, condition.operator)
        self.assertEqual(None, condition.right_operand_window)
        self.assertEqual(constants.ValueType.ABSOLUTE, condition.right_operand_type)
        self.assertEqual("100", condition.right_operand_value)

    def test_archive(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        rule = magic_mixer.blend(model.Rule, agency=agency, accounts_included=[account])
        self.assertEqual(rule.archived, False)

        rule.archive(request)
        self.assertEqual(rule.archived, True)

    def test_restore(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        rule = magic_mixer.blend(model.Rule, agency=agency, archived=True, accounts_included=[account])
        self.assertEqual(rule.archived, True)

        rule.restore(request)
        self.assertEqual(rule.archived, False)

    def test_update_valid_agency(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        rule = magic_mixer.blend(model.Rule, account=account, ad_groups_included=[ad_group])

        rule.update(request, agency=agency, account=None)

        self.assertEqual(rule.agency, agency)
        self.assertEqual(rule.account, None)

    def test_update_valid_agency_and_ad_group_included(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        rule = magic_mixer.blend(model.Rule, account=account)

        rule.update(request, agency=agency, account=None, ad_groups_included=[ad_group])

        self.assertEqual(rule.agency, agency)
        self.assertEqual(rule.account, None)
        self.assertEqual([ad_group for ad_group in rule.ad_groups_included.all()], [ad_group])

    def test_update_invalid_agency_with_included_accounts(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_account = magic_mixer.blend(core.models.Account, agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, accounts_included=[included_account])

        another_agency = magic_mixer.blend(core.models.Agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=another_agency, account=None)

    def test_update_invalid_agency_with_included_campaigns(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_campaign = magic_mixer.blend(core.models.Campaign, account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, campaigns_included=[included_campaign])

        another_agency = magic_mixer.blend(core.models.Agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=another_agency, account=None)

    def test_update_invalid_agency_with_included_ag_groups(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, ad_groups_included=[included_ad_group])

        another_agency = magic_mixer.blend(core.models.Agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=another_agency, account=None)

    def test_update_invalid_agency_and_ad_group_included(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)

        rule = magic_mixer.blend(model.Rule, account=account)

        agency = magic_mixer.blend(core.models.Agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=agency, account=None, ad_groups_included=[ad_group])

    def test_update_valid_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        rule = magic_mixer.blend(model.Rule, agency=agency, ad_groups_included=[ad_group])

        rule.update(request, agency=None, account=account)

        self.assertEqual(rule.agency, None)
        self.assertEqual(rule.account, account)

    def test_update_valid_account_and_ad_group_included(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        rule = magic_mixer.blend(model.Rule, agency=agency)

        rule.update(request, agency=None, account=account, ad_groups_included=[ad_group])

        self.assertEqual(rule.agency, None)
        self.assertEqual(rule.account, account)
        self.assertEqual([ad_group for ad_group in rule.ad_groups_included.all()], [ad_group])

    def test_update_invalid_account_with_included_accounts(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_account = magic_mixer.blend(core.models.Account, agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, accounts_included=[included_account])

        another_agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=another_agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=None, account=account)

    def test_update_invalid_account_with_included_campaigns(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_campaign = magic_mixer.blend(core.models.Campaign, account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, campaigns_included=[included_campaign])

        another_agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=another_agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=None, account=account)

    def test_update_invalid_account_with_with_included_adgroups(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, ad_groups_included=[included_ad_group])

        another_agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=another_agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=None, account=account)

    def test_update_invalid_account_and_ad_group_included(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)

        rule = magic_mixer.blend(model.Rule, agency=agency)

        account = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=None, account=account, ad_groups_included=[ad_group])

    def test_update_without_agency_and_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)

        rule = magic_mixer.blend(model.Rule, agency=agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=None, account=None)

    def test_update_with_agency_and_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency)

        with self.assertRaises(ValidationError):
            rule.update(request, agency=agency, account=account)

    def test_update_valid_accounts_included(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_account = magic_mixer.blend(core.models.Account, agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, accounts_included=[included_account])
        self.assertEqual([account for account in rule.accounts_included.all()], [included_account])

        new_included_account = magic_mixer.blend(core.models.Account, agency=agency)
        rule.update(request, accounts_included=[new_included_account])

        self.assertEqual(rule.accounts_included.get(), new_included_account)

    def test_update_invalid_accounts_included(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_account = magic_mixer.blend(core.models.Account, agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, accounts_included=[included_account])

        another_agency = magic_mixer.blend(core.models.Agency)
        new_included_account = magic_mixer.blend(core.models.Account, agency=another_agency)

        with self.assertRaises(ValidationError):
            rule.update(request, accounts_included=[new_included_account])

    def test_update_valid_campaigns_included(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_campaign = magic_mixer.blend(core.models.Campaign, account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, campaigns_included=[included_campaign])
        self.assertEqual([campaign for campaign in rule.campaigns_included.all()], [included_campaign])

        new_included_campaign = magic_mixer.blend(core.models.Campaign, account__agency=agency)
        rule.update(request, campaigns_included=[new_included_campaign])

        self.assertEqual([campaign for campaign in rule.campaigns_included.all()], [new_included_campaign])

    def test_update_invalid_campaigns_included_on_agency(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_campaign = magic_mixer.blend(core.models.Campaign, account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, campaigns_included=[included_campaign])

        another_agency = magic_mixer.blend(core.models.Agency)
        new_included_campaign = magic_mixer.blend(core.models.Campaign, account__agency=another_agency)

        with self.assertRaises(ValidationError):
            rule.update(request, campaigns_included=[new_included_campaign])

    def test_update_invalid_campaigns_included_on_account(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        included_campaign = magic_mixer.blend(core.models.Campaign, account=account)

        rule = magic_mixer.blend(model.Rule, account=account, campaigns_included=[included_campaign])

        another_account = magic_mixer.blend(core.models.Account)
        new_included_campaign = magic_mixer.blend(core.models.Campaign, account=another_account)

        with self.assertRaises(ValidationError):
            rule.update(request, campaigns_included=[new_included_campaign])

    def test_update_valid_ad_groups_included(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_ad_groups = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, ad_groups_included=[included_ad_groups])
        self.assertEqual([ad_group for ad_group in rule.ad_groups_included.all()], [included_ad_groups])

        new_included_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)
        rule.update(request, ad_groups_included=[new_included_ad_group])

        self.assertEqual([ad_group for ad_group in rule.ad_groups_included.all()], [new_included_ad_group])

    def test_update_invalid_ad_groups_included_on_agency(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        included_ad_groups = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=agency)

        rule = magic_mixer.blend(model.Rule, agency=agency, ad_groups_included=[included_ad_groups])

        another_agency = magic_mixer.blend(core.models.Agency)
        new_included_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=another_agency)

        with self.assertRaises(ValidationError):
            rule.update(request, ad_groups_included=[new_included_ad_group])

    def test_update_invalid_ad_groups_included_on_account(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        included_ad_groups = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        rule = magic_mixer.blend(model.Rule, account=account, ad_groups_included=[included_ad_groups])

        another_account = magic_mixer.blend(core.models.Account)
        new_included_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=another_account)

        with self.assertRaises(ValidationError):
            rule.update(request, ad_groups_included=[new_included_ad_group])
