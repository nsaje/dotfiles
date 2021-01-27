from decimal import Decimal

from django.test import TestCase
from mock import patch

import core.models
import dash.constants
import utils.exc
from core.features.goals import CampaignGoal
from core.features.goals import CampaignGoalValue
from utils.magic_mixer import magic_mixer


class InstanceTestCase(TestCase):
    def test_update(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        initial = {"iab_category": dash.constants.IABCategory.IAB1}
        campaign.settings.update(None, **initial)
        user_changes = {"iab_category": dash.constants.IABCategory.IAB2}
        applied_changes = campaign.settings.update(None, **user_changes)
        expected_changes = {"iab_category": dash.constants.IABCategory.IAB2}
        self.assertEqual(applied_changes, expected_changes)

    @patch("utils.k1_helper.update_ad_groups")
    def test_r1_k1_propagation(self, mock_ping_adgroups):
        campaign = magic_mixer.blend(core.models.Campaign)
        magic_mixer.cycle(10).blend(core.models.AdGroup, campaign=campaign)
        campaign.settings.update_unsafe(None, enable_ga_tracking=False)

        campaign.settings.update(None, name="abc")
        self.assertEqual(mock_ping_adgroups.call_count, 0)

        mock_ping_adgroups.reset_mock()
        campaign.settings.update(None, enable_ga_tracking=True)
        self.assertEqual(mock_ping_adgroups.call_count, 0)

        mock_ping_adgroups.reset_mock()
        campaign.settings.update(None, iab_category="IAB2")
        self.assertEqual(mock_ping_adgroups.call_count, 1)

    @patch("automation.autopilot_legacy.recalculate_budgets_campaign")
    def test_recalculate_autopilot(self, mock_autopilot):
        campaign = magic_mixer.blend(core.models.Campaign)
        campaign.settings.update(None, autopilot=True)
        mock_autopilot.assert_called_once_with(campaign)

    @patch.object(core.features.bcm.BudgetLineItem, "minimize_amount_and_end_today")
    @patch.object(core.models.AdGroup, "archive")
    def test_archiving(self, mock_adgroup_archive, mock_budget_archive):
        campaign = magic_mixer.blend(core.models.Campaign)
        magic_mixer.cycle(10).blend(core.models.AdGroup, campaign=campaign)
        magic_mixer.blend_budget_line_item(campaign=campaign)
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)

        campaign.settings.update(None, archived=True)
        self.assertTrue(campaign.archived)
        self.assertTrue(campaign.settings.archived)
        self.assertEqual(mock_adgroup_archive.call_count, 10)
        self.assertEqual(mock_budget_archive.call_count, 1)

        campaign.settings.update(None, archived=True)

        mock_adgroup_archive.reset_mock()
        mock_budget_archive.reset_mock()
        campaign.settings.update(None, archived=False)
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertEqual(mock_adgroup_archive.call_count, 0)
        self.assertEqual(mock_budget_archive.call_count, 0)

    @patch.object(core.models.Account, "is_archived", return_value=True)
    def test_cant_restore_account_fail(self, mock_account_is_archived):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        campaign.settings.update_unsafe(None, archived=True)
        campaign.archived = True
        campaign.save(None)
        with self.assertRaises(utils.exc.ForbiddenError):
            campaign.settings.update(None, archived=False)

    @patch.object(core.models.Account, "is_archived", return_value=True)
    def test_update_account_archived_fail(self, mock_account_is_archived):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        with self.assertRaises(utils.exc.ForbiddenError):
            campaign.settings.update(None, name="new name")

    def test_update_archived_campaign(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        campaign.archive(None)
        campaign.refresh_from_db()
        self.assertTrue(campaign.archived)
        self.assertTrue(campaign.settings.archived)
        with self.assertRaises(utils.exc.ForbiddenError):
            campaign.settings.update(None, name="new name")
        campaign.settings.update(None, archived=True)
        campaign.settings.update(None, archived=False)
        campaign.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_update_goals_when_restoring_campaign(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = Decimal("1.0")
        request = magic_mixer.blend_request_user(is_superuser=True)
        campaign = magic_mixer.blend(core.models.Campaign, account_currency=dash.constants.Currency.EUR)
        goal1 = magic_mixer.blend(
            core.features.goals.CampaignGoal, campaign=campaign, primary=True, type=dash.constants.CampaignGoalKPI.CPC
        )
        goal2 = magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=campaign,
            primary=False,
            type=dash.constants.CampaignGoalKPI.PAGES_PER_SESSION,
        )
        goal1.add_local_value(request, "0.15")
        goal2.add_local_value(request, 20)
        self.assertEqual(Decimal("0.15"), goal1.get_current_value().value)
        self.assertEqual(20, goal2.get_current_value().value)

        campaign.settings.update_unsafe(None, archived=True)
        mock_get_exchange_rate.return_value = Decimal("3.0")
        campaign.restore(None)
        self.assertEqual(Decimal("0.05"), goal1.get_current_value().value)
        self.assertEqual(20, goal2.get_current_value().value)

    def test_update_archived_campaign_publisher_groups(self):
        account = magic_mixer.blend(core.models.Account)
        publisher_group_1 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, name="test publisher group", account=account
        )
        publisher_group_2 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, name="test publisher group", account=account
        )
        publisher_group_3 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, name="test publisher group", account=account
        )
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign.settings.update(
            None,
            whitelist_publisher_groups=[publisher_group_1.id, publisher_group_2.id],
            blacklist_publisher_groups=[publisher_group_1.id, publisher_group_2.id],
        )
        campaign.archive(None)
        campaign.refresh_from_db()
        self.assertTrue(campaign.archived)
        campaign.settings.update(None, whitelist_publisher_groups=[publisher_group_2.id])
        campaign.settings.update(None, blacklist_publisher_groups=[publisher_group_2.id])
        with self.assertRaises(utils.exc.ForbiddenError):
            campaign.settings.update(None, whitelist_publisher_groups=[publisher_group_3.id])
        with self.assertRaises(utils.exc.ForbiddenError):
            campaign.settings.update(None, blacklist_publisher_groups=[publisher_group_3.id])
        campaign.settings.update(None, whitelist_publisher_groups=[])
        campaign.settings.update(None, blacklist_publisher_groups=[])

    def test_change_name_does_not_affect_goals(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        campaign.settings.update_unsafe(None, name="Initial")

        value = Decimal("0.1500")
        campaign_goal = magic_mixer.blend(CampaignGoal, campaign=campaign)
        campaign_goal_value = magic_mixer.blend(
            CampaignGoalValue, campaign_goal=campaign_goal, value=value, local_value=value
        )

        self.assertEqual(CampaignGoal.objects.filter(campaign=campaign).count(), 1)
        self.assertEqual(CampaignGoal.objects.filter(campaign=campaign).get(), campaign_goal)
        self.assertEqual(CampaignGoalValue.objects.filter(campaign_goal__campaign=campaign).count(), 1)
        self.assertEqual(CampaignGoalValue.objects.filter(campaign_goal__campaign=campaign).get(), campaign_goal_value)

        campaign.settings.update(None, archived=False, name="New")

        self.assertEqual(CampaignGoal.objects.filter(campaign=campaign).count(), 1)
        self.assertEqual(CampaignGoal.objects.filter(campaign=campaign).get(), campaign_goal)
        self.assertEqual(CampaignGoalValue.objects.filter(campaign_goal__campaign=campaign).count(), 1)
        self.assertEqual(CampaignGoalValue.objects.filter(campaign_goal__campaign=campaign).get(), campaign_goal_value)
