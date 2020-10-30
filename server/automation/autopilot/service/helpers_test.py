from decimal import Decimal

from django import test
from mock import patch

from dash import constants
from dash import models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import helpers


class AutopilotHelpersTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    @patch("dash.models.AdGroup.get_running_status_by_sources_setting")
    @patch("dash.models.AdGroup.get_running_status")
    def test_get_active_ad_groups_on_autopilot(self, mock_running_status, mock_running_status_by_sources):
        mock_running_status.return_value = constants.AdGroupRunningStatus.ACTIVE
        mock_running_status_by_sources.return_value = constants.AdGroupRunningStatus.ACTIVE
        all_ap_adgs = helpers.get_active_ad_groups_on_autopilot()
        self.assertEqual(len(all_ap_adgs), 3)
        self.assertFalse(models.AdGroup.objects.get(id=2) in all_ap_adgs)

    @patch("utils.k1_helper.update_ad_group")
    def test_update_ad_group_daily_budget(self, mock_k1_update_ad_group):
        ag = models.AdGroup.objects.get(id=1)
        ap = constants.SystemUserType.AUTOPILOT

        helpers.update_ad_group_daily_budget(ag, Decimal("123"))

        mock_k1_update_ad_group.assert_called()

        self.assertEqual(ag.settings.daily_budget, Decimal("123"))
        self.assertEqual(ag.settings.system_user, ap)


class AutopilotGetEntitiesTestCase(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ad_group_1 = cls._create_adgroup()
        cls.ad_group_2 = cls._create_adgroup()

    @classmethod
    def _create_adgroup(cls):
        ad_group = magic_mixer.blend(models.AdGroup, campaign__account__agency__uses_realtime_autopilot=True)
        ad_group.settings.update_unsafe(
            None,
            state=constants.AdGroupSettingsState.ACTIVE,
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )
        ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        return ad_group

    def setUp(self):
        self.ad_group_1.settings.refresh_from_db()
        self.ad_group_1.campaign.settings.refresh_from_db()
        self.ad_group_2.settings.refresh_from_db()
        self.ad_group_2.campaign.settings.refresh_from_db()

    def _find_in_result(self, result, ad_group):
        return result.get(ad_group.campaign, [])

    def test_campaign_autopilot(self):
        result = helpers.get_autopilot_entities()
        self.assertIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    @patch("automation.campaignstop.get_campaignstop_states")
    def test_campaign_stopped(self, mock_get_campaignstop_states):
        mock_get_campaignstop_states.return_value = {
            self.ad_group_1.campaign_id: {"allowed_to_run": False},
            self.ad_group_2.campaign_id: {"allowed_to_run": False},
        }

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertNotIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_campaign_autopilot_off(self):
        self.ad_group_1.campaign.settings.update_unsafe(None, autopilot=False)

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_realtime_autopilot(self):
        self.ad_group_1.settings.update_unsafe(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        )
        self.ad_group_2.settings.update_unsafe(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        )
        self.ad_group_1.campaign.settings.update_unsafe(None, autopilot=False)

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_one_campaign(self):
        result = helpers.get_autopilot_entities(campaign=self.ad_group_1.campaign)
        self.assertIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertNotIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_one_campaign_ad_group_paused(self):
        self.ad_group_1.settings.update_unsafe(None, state=constants.AdGroupSettingsState.INACTIVE)

        result = helpers.get_autopilot_entities(campaign=self.ad_group_1.campaign)
        self.assertNotIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertNotIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_adgroup_paused(self):
        self.ad_group_1.settings.update_unsafe(None, state=constants.AdGroupSettingsState.INACTIVE)

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_adgroup_past(self):
        self.ad_group_1.settings.update_unsafe(None, end_date=dates_helper.day_before(dates_helper.local_today()))

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_adgroup_future(self):
        self.ad_group_1.settings.update_unsafe(None, start_date=dates_helper.day_after(dates_helper.local_today()))

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_1, self._find_in_result(result, self.ad_group_1))
        self.assertIn(self.ad_group_2, self._find_in_result(result, self.ad_group_2))

    def test_select_related(self):
        result = helpers.get_autopilot_entities()

        with self.assertNumQueries(0):
            for campaign in result:
                campaign.settings
                for ad_group in result[campaign]:
                    ad_group.settings
