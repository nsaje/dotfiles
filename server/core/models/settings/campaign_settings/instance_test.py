from django.test import TestCase
from mock import patch

import core.models
import dash.constants
import utils.exc
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

    @patch("utils.redirector_helper.insert_adgroup")
    @patch("utils.k1_helper.update_ad_groups")
    def test_r1_k1_propagation(self, mock_ping_adgroups, mock_insert_adgroup):
        campaign = magic_mixer.blend(core.models.Campaign)
        magic_mixer.cycle(10).blend(core.models.AdGroup, campaign=campaign)
        campaign.settings.update_unsafe(None, enable_ga_tracking=False)

        campaign.settings.update(None, name="abc")
        self.assertEqual(mock_insert_adgroup.call_count, 0)
        self.assertEqual(mock_ping_adgroups.call_count, 0)

        mock_insert_adgroup.reset_mock()
        mock_ping_adgroups.reset_mock()
        campaign.settings.update(None, enable_ga_tracking=True)
        self.assertEqual(mock_insert_adgroup.call_count, 10)
        self.assertEqual(mock_ping_adgroups.call_count, 0)

        mock_insert_adgroup.reset_mock()
        mock_ping_adgroups.reset_mock()
        campaign.settings.update(None, iab_category="IAB2")
        self.assertEqual(mock_insert_adgroup.call_count, 0)
        self.assertEqual(mock_ping_adgroups.call_count, 1)

    @patch("automation.autopilot.recalculate_budgets_campaign")
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
