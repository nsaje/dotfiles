from mock import patch

from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer
import utils.exc


class InstanceTestCase(TestCase):
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

    @patch.object(core.models.AdGroup, "archive")
    def test_archiving(self, mock_adgroup_archive):
        campaign = magic_mixer.blend(core.models.Campaign)
        magic_mixer.cycle(10).blend(core.models.AdGroup, campaign=campaign)
        campaign.settings.update(None, archived=True)
        self.assertEqual(mock_adgroup_archive.call_count, 10)
        mock_adgroup_archive.reset_mock()
        campaign.settings.update(None, archived=False)
        self.assertEqual(mock_adgroup_archive.call_count, 0)

    @patch.object(core.models.AdGroup, "can_archive", return_value=False)
    def test_cant_archive_adgroup_fail(self, mock_adgroup_can_archive):
        campaign = magic_mixer.blend(core.models.Campaign)
        magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        with self.assertRaises(utils.exc.ForbiddenError):
            campaign.settings.update(None, archived=True)
        self.assertFalse(campaign.settings.archived)

    @patch.object(core.models.Account, "is_archived", return_value=True)
    def test_cant_restore_account_fail(self, mock_adgroup_can_archive):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        campaign.settings.update(None, archived=True)
        with self.assertRaises(utils.exc.ForbiddenError):
            campaign.settings.update(None, archived=False)
