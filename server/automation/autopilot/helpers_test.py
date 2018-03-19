from decimal import Decimal
from mock import patch

from django import test

from . import helpers
from dash import constants
from dash import models
from utils import dates_helper
from utils.magic_mixer import magic_mixer


class AutopilotHelpersTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    @patch('dash.models.AdGroup.get_running_status_by_sources_setting')
    @patch('dash.models.AdGroup.get_running_status')
    def test_get_active_ad_groups_on_autopilot(self, mock_running_status, mock_running_status_by_sources):
        mock_running_status.return_value = constants.AdGroupRunningStatus.ACTIVE
        mock_running_status_by_sources.return_value = constants.AdGroupRunningStatus.ACTIVE
        all_ap_adgs, all_ap_adgs_settings = helpers.get_active_ad_groups_on_autopilot()
        cpc_ap_adgs, cpc_ap_adgs_settings = helpers.get_active_ad_groups_on_autopilot(autopilot_state=3)
        budget_ap_adgs, budget_ap_adgs_settings = helpers.get_active_ad_groups_on_autopilot(autopilot_state=1)
        self.assertEqual(len(all_ap_adgs), 3)
        self.assertTrue(adg in all_ap_adgs for adg in cpc_ap_adgs + budget_ap_adgs)
        for adg_settings in all_ap_adgs_settings:
            self.assertEqual(adg_settings, adg_settings.ad_group.get_current_settings())
            self.assertTrue(adg_settings.autopilot_state in [
                constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
                constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET])
        for adg_settings in cpc_ap_adgs_settings:
            self.assertEqual(adg_settings, adg_settings.ad_group.get_current_settings())
            self.assertTrue(adg_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC)
        for adg_settings in budget_ap_adgs_settings:
            self.assertEqual(adg_settings, adg_settings.ad_group.get_current_settings())
            self.assertTrue(adg_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        self.assertFalse(models.AdGroup.objects.get(id=2) in cpc_ap_adgs + budget_ap_adgs + all_ap_adgs)

    def test_update_ad_group_source_values(self):
        ag_source = models.AdGroupSource.objects.get(id=1)
        ag_source_settings = ag_source.get_current_settings()
        old_daily_budget = ag_source_settings.daily_budget_cc
        old_cpc = ag_source_settings.cpc_cc
        old_count = models.AdGroupSourceSettings.objects.count()
        helpers.update_ad_group_source_values(ag_source, {
            'daily_budget_cc': old_daily_budget + Decimal('10'),
            'cpc_cc': old_cpc + Decimal('0.5')})
        new_count = models.AdGroupSourceSettings.objects.count()
        self.assertNotEqual(new_count, old_count)
        self.assertEqual(ag_source_settings.daily_budget_cc, old_daily_budget + Decimal('10'))
        self.assertEqual(ag_source_settings.cpc_cc, old_cpc + Decimal('0.5'))

    def test_get_autopilot_active_sources_settings(self):
        adgroups = models.AdGroup.objects.filter(id__in=[1, 2, 3])
        ad_groups_and_settings = {adg: adg.get_current_settings() for adg in adgroups}
        active_enabled_sources = helpers.get_autopilot_active_sources_settings(ad_groups_and_settings)
        for ag_source_setting in active_enabled_sources:
            self.assertTrue(ag_source_setting.state == constants.AdGroupSettingsState.ACTIVE)
            self.assertTrue(ag_source_setting.ad_group_source.ad_group in adgroups)

        source = models.AdGroupSource.objects.get(id=1)
        self.assertTrue(source in [setting.ad_group_source for setting in active_enabled_sources])
        source.settings.update(k1_sync=False, skip_automation=True, state=constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(source.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)
        self.assertFalse(source in [setting.ad_group_source for setting in
                                    helpers.get_autopilot_active_sources_settings(ad_groups_and_settings)])

    @patch('utils.k1_helper.update_ad_group')
    @patch('dash.views.helpers.set_ad_group_sources_cpcs')
    def test_update_ad_group_b1_sources_group_values(self, mock_set_ad_group_sources_cpcs,
                                                     mock_k1_update_ad_group):
        ag = models.AdGroup.objects.get(id=1)

        changes = {
            'cpc_cc': Decimal('0.123'),
            'daily_budget_cc': Decimal('123')
        }
        ap = constants.SystemUserType.AUTOPILOT
        helpers.update_ad_group_b1_sources_group_values(ag, changes, system_user=ap)

        mock_set_ad_group_sources_cpcs.assert_called()

        mock_k1_update_ad_group.assert_called()

        self.assertEqual(ag.settings.b1_sources_group_cpc_cc, Decimal('0.123'))
        self.assertEqual(ag.settings.b1_sources_group_daily_budget, Decimal('123'))
        self.assertEqual(ag.settings.system_user, ap)


class AutopilotGetEntitiesTestCase(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.b1_ad_group_source = cls._create_adgroupsource(source__source_type__type=constants.SourceType.B1)
        cls.ad_group_source = cls._create_adgroupsource(source__source_type__type=constants.SourceType.OUTBRAIN)

    @classmethod
    def _create_adgroupsource(cls, **kwargs):
        ad_group_source = magic_mixer.blend(models.AdGroupSource, **kwargs)
        ad_group_source.settings.update_unsafe(
            None, state=constants.AdGroupSourceSettingsState.ACTIVE)
        ad_group_source.ad_group.settings.update_unsafe(
            None,
            state=constants.AdGroupSettingsState.ACTIVE,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        return ad_group_source

    def assertResultHasAdGroupSource(self, result, ad_group_source=None):
        if ad_group_source is None:
            ad_group_source = self.ad_group_source
        self.assertIn(
            ad_group_source,
            result.get(ad_group_source.ad_group.campaign, {}).get(ad_group_source.ad_group, []),
        )

    def _find_in_result(self, result, ad_group_source):
        return (
            result
            .get(ad_group_source.ad_group.campaign, {})
            .get(ad_group_source.ad_group, [])
        )

    def test_adgroup_budget(self):
        result = helpers.get_autopilot_entities()
        self.assertIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    @patch('automation.campaignstop.get_campaignstop_states')
    def test_campaign_stopped(self, mock_get_campaignstop_states):
        mock_get_campaignstop_states.return_value = {
            self.ad_group_source.ad_group.campaign_id: {'allowed_to_run': False},
            self.b1_ad_group_source.ad_group.campaign_id: {'allowed_to_run': False},
        }

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertNotIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_adgroup_cpc(self):
        self.ad_group_source.ad_group.settings.update_unsafe(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC)

        result = helpers.get_autopilot_entities()
        self.assertIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_campaign_autopilot(self):
        self.ad_group_source.ad_group.settings.update_unsafe(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.ad_group_source.ad_group.campaign.settings.update_unsafe(None, autopilot=True)

        result = helpers.get_autopilot_entities()
        self.assertIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_one_campaign(self):
        result = helpers.get_autopilot_entities(campaign=self.ad_group_source.ad_group.campaign)
        self.assertIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertNotIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_one_adgroup(self):
        result = helpers.get_autopilot_entities(ad_group=self.ad_group_source.ad_group)
        self.assertIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertNotIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_adgroup_inactive(self):
        self.ad_group_source.ad_group.settings.update_unsafe(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_adgroup_paused(self):
        self.ad_group_source.ad_group.settings.update_unsafe(
            None, state=constants.AdGroupSettingsState.INACTIVE)

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_adgroup_past(self):
        self.ad_group_source.ad_group.settings.update_unsafe(
            None, end_date=dates_helper.day_before(dates_helper.local_today()))

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_adgroup_future(self):
        self.ad_group_source.ad_group.settings.update_unsafe(
            None, start_date=dates_helper.day_after(dates_helper.local_today()))

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_adgroup_paused_allrtb(self):
        self.b1_ad_group_source.ad_group.settings.update_unsafe(
            None, b1_sources_group_enabled=True,
            b1_sources_group_state=constants.AdGroupSourceSettingsState.INACTIVE)

        result = helpers.get_autopilot_entities()
        self.assertIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertNotIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_adgroupsource_paused(self):
        self.ad_group_source.settings.update_unsafe(
            None, state=constants.AdGroupSourceSettingsState.INACTIVE)

        result = helpers.get_autopilot_entities()
        self.assertNotIn(self.ad_group_source, self._find_in_result(result, self.ad_group_source))
        self.assertIn(self.b1_ad_group_source, self._find_in_result(result, self.b1_ad_group_source))

    def test_select_related(self):
        result = helpers.get_autopilot_entities()

        with self.assertNumQueries(0):
            for campaign in result:
                campaign.account
                campaign.settings
                for ad_group in result[campaign]:
                    ad_group.settings
                    for ad_group_source in result[campaign][ad_group]:
                        ad_group_source.settings
                        ad_group_source.source.source_type
