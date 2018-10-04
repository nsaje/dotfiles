from django.test import TestCase
import mock
from datetime import datetime

import core.features.bcm
import core.features.goals
from .. import CampaignStopState, RealTimeDataHistory, RealTimeCampaignStopLog
from .. import constants
from . import selection

import dash.constants
from core.models.settings.ad_group_settings import AdGroupSettings
from core.models.settings.ad_group_source_settings import AdGroupSourceSettings
from utils.magic_mixer import magic_mixer
from utils import dates_helper


class UpdateAlmostDepletedTestCase(TestCase):
    def setUp(self):
        self._setup_initial_state()

    def mocked_afternoon_est_now():
        today = datetime.today()
        return datetime(today.year, today.month, today.day, 20)

    def mocked_morning_est_now():
        today = datetime.today()
        return datetime(today.year, today.month, today.day, 8)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_does_not_fail_if_campaign_has_no_campaignstop(self, _):
        CampaignStopState.objects.all().delete()
        campaign_stop_count = CampaignStopState.objects.count()
        self.assertEqual(campaign_stop_count, 0)
        selection.mark_almost_depleted_campaigns()

    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_no_mark(self):
        RealTimeDataHistory.objects.create(
            ad_group=self.ad_group, source=self.source, date=dates_helper.local_today(), etfm_spend=50
        )
        selection.mark_almost_depleted_campaigns()
        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_mark_if_budget_over_end_date(self):
        now = dates_helper.utc_now()
        RealTimeDataHistory.objects.create(
            ad_group=self.ad_group, source=self.source, date=dates_helper.local_today(), etfm_spend=50
        )
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            mock_utc_now.return_value = dates_helper.day_after(now.replace(hour=8))
            selection.mark_almost_depleted_campaigns()
            self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_script_should_produce_log(self, _):
        RealTimeCampaignStopLog.objects.all().delete()
        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=901.0)
        selection.mark_almost_depleted_campaigns()
        self.assertEqual(RealTimeCampaignStopLog.objects.count(), 1)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_mark_almost_depleted_for_one_campaign(self, _):
        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=901.0)
        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_b1_source_type_gets_added_to_budget_if_adg_source_inactive(self, _):
        self.source.source_type.type = dash.constants.SourceType.B1
        self.source.source_type.save()
        self.ad_group.settings.update(None, b1_sources_group_enabled=True)
        self.ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)
        self.assertEqual(self.ad_group_source.settings.state, dash.constants.AdGroupSourceSettingsState.INACTIVE)

        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=901.0)

        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    # @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_morning_est_now)
    # @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    # def test_day_before_yesterday_is_used_when_in_critical_hours(self, _):
    #     self.source.source_type.type = dash.constants.SourceType.B1
    #     self.source.source_type.save()
    #     self.ad_group.settings.update(None, b1_sources_group_enabled=True)
    #     self.ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)
    #     self.assertEqual(self.ad_group_source.settings.state, dash.constants.AdGroupSourceSettingsState.INACTIVE)

    #     today = dates_helper.local_today()
    #     RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=10.0)
    #     yesterday = dates_helper.local_yesterday()
    #     RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=yesterday, etfm_spend=100.0)
    #     day_before_yesterday = dates_helper.days_before(yesterday, 1)
    #     RealTimeDataHistory.objects.create(
    #         ad_group=self.ad_group, source=self.source, date=day_before_yesterday, etfm_spend=1000.0
    #     )

    #     self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
    #     selection.mark_almost_depleted_campaigns()
    #     self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    # @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    # @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    # def test_daily_budget_cc_and_etfm_spend_do_not_set_almost_depleted_to_true(self, _):
    #     active_adg = dash.constants.AdGroupSettingsState.ACTIVE
    #     active_adg_source = dash.constants.AdGroupSourceSettingsState.ACTIVE

    #     adg_setting_state = AdGroupSettings.objects.filter(ad_group=self.ad_group).first().state
    #     self.assertEqual(adg_setting_state, active_adg)
    #     adg_source_setting_state = (
    #         AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).first().state
    #     )
    #     self.assertEqual(adg_source_setting_state, active_adg_source)

    #     self.ad_group_source.settings.update_unsafe(None, daily_budget_cc=800)
    #     today = dates_helper.local_today()
    #     RealTimeDataHistory.objects.create(
    #         ad_group=self.ad_group, source=self.source, date=today, etfm_spend=899.0 - config.THRESHOLD
    #     )

    #     self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
    #     selection.mark_almost_depleted_campaigns()
    #     self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_daily_budget_cc_and_etfm_spend_set_almost_depleted_to_true(self, _):
        active_adg = dash.constants.AdGroupSettingsState.ACTIVE
        active_adg_source = dash.constants.AdGroupSourceSettingsState.ACTIVE

        adg_setting_state = AdGroupSettings.objects.filter(ad_group=self.ad_group).first().state
        self.assertEqual(adg_setting_state, active_adg)
        adg_source_setting_state = (
            AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).first().state
        )
        self.assertEqual(adg_source_setting_state, active_adg_source)

        self.ad_group_source.settings.update_unsafe(None, daily_budget_cc=901)
        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=899.0)

        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_daily_budget_cc_and_etfm_spend_set_almost_depleted_column_to_true(self, _):
        active_adg = dash.constants.AdGroupSettingsState.ACTIVE
        active_adg_source = dash.constants.AdGroupSourceSettingsState.ACTIVE

        adg_setting_state = AdGroupSettings.objects.filter(ad_group=self.ad_group).first().state
        self.assertEqual(adg_setting_state, active_adg)
        adg_source_setting_state = (
            AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).first().state
        )
        self.assertEqual(adg_source_setting_state, active_adg_source)

        self.ad_group_source.settings.update_unsafe(None, daily_budget_cc=899)
        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=901.0)

        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_user_has_both_ad_group_and_ad_group_source_turned_on(self, _):
        active_adg = dash.constants.AdGroupSettingsState.ACTIVE
        active_adg_source = dash.constants.AdGroupSourceSettingsState.ACTIVE

        adg_setting_state = AdGroupSettings.objects.filter(ad_group=self.ad_group).first().state
        self.assertEqual(adg_setting_state, active_adg)
        adg_source_setting_state = (
            AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).first().state
        )
        self.assertEqual(adg_source_setting_state, active_adg_source)

        self.ad_group_source.settings.update_unsafe(None, daily_budget_cc=901)

        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_user_turns_on_ad_group_and_has_ad_group_source_off(self, _):
        inactive_adg = dash.constants.AdGroupSettingsState.INACTIVE
        inactive_adg_source = dash.constants.AdGroupSourceSettingsState.INACTIVE
        self.ad_group.settings.update_unsafe(None, state=inactive_adg)
        self.ad_group_source.settings.update_unsafe(None, state=inactive_adg_source)

        adg_setting_state = AdGroupSettings.objects.filter(ad_group=self.ad_group).first().state
        self.assertEqual(adg_setting_state, inactive_adg)
        adg_source_setting_state = (
            AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).first().state
        )
        self.assertEqual(adg_source_setting_state, inactive_adg_source)

        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=901.0)

        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_user_turns_off_ad_group_and_ad_group_source(self, _):
        self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)
        self.ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)

        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=901.0)

        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_get_spend_method_one_entry(self, _):
        today = dates_helper.local_today()
        adg_sources = [self.ad_group_source]
        adg_source_spends = {(self.ad_group.id, self.source.id, today): 900.000}
        returned_spend = selection._get_max_spend(adg_sources, adg_source_spends)
        self.assertEqual(returned_spend, 900.000)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_get_spend_method_one_entry_with_settings_budget(self, _):
        today = dates_helper.local_today()
        self.ad_group_source.settings.update_unsafe(None, daily_budget_cc=900.0000)
        adg_sources = [self.ad_group_source]
        adg_source_spends = {(self.ad_group.id, self.source.id, today): 800.000}
        returned_spend = selection._get_max_spend(adg_sources, adg_source_spends)
        self.assertEqual(returned_spend, 900.000)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_get_spend_method_multiple_entries(self, _):
        source_type2 = magic_mixer.blend(core.models.source_type.SourceType)
        source2 = magic_mixer.blend(core.models.Source, type=source_type2)
        ad_group2 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        ad_group_source2 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group2, source=source2)
        adg_sources = [self.ad_group_source, ad_group_source2]
        today = dates_helper.local_today()
        adg_source_spends = {
            (self.ad_group.id, self.source.id, today): 900.000,
            (ad_group2.id, source2.id, today): 100.000,
        }
        returned_spend = selection._get_max_spend(adg_sources, adg_source_spends)
        self.assertEqual(returned_spend, 1000.000)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_get_spend_method_multiple_entries_with_source_type_of_b1(self, _):
        today = dates_helper.local_today()
        source_type2 = magic_mixer.blend(core.models.source_type.SourceType, type=dash.constants.SourceType.B1)
        source2 = magic_mixer.blend(core.models.Source, type=source_type2)
        ad_group2 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        ad_group_source2 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group2, source=source2)
        adg_sources = [self.ad_group_source, ad_group_source2]
        adg_source_spends = {
            (self.ad_group.id, self.source.id, today): 900.000,
            (ad_group2.id, source2.id, today): 100.000,
        }
        returned_spend = selection._get_max_spend(adg_sources, adg_source_spends)
        self.assertEqual(returned_spend, 1000.000)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_morning_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_in_critical_hours(self, _):
        today = dates_helper.local_today()
        yesterday = dates_helper.local_yesterday()
        source_type2 = magic_mixer.blend(core.models.source_type.SourceType, type=dash.constants.SourceType.B1)
        source2 = magic_mixer.blend(core.models.Source, type=source_type2)
        ad_group2 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        ad_group_source2 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group2, source=source2)
        adg_sources = [self.ad_group_source, ad_group_source2]
        adg_source_spends = {
            (self.ad_group.id, self.source.id, today): 900.000,
            (self.ad_group.id, self.source.id, yesterday): 500.000,
            (ad_group2.id, source2.id, today): 100.000,
        }
        returned_spend = selection._get_max_spend(adg_sources, adg_source_spends)
        self.assertEqual(returned_spend, 1500.000)

    @mock.patch("utils.dates_helper.utc_now", side_effect=mocked_afternoon_est_now)
    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    def test_when_user_disables_adgroup_we_should_get_realtime_data_from_all_sources(self, _):
        self.source.source_type.save()
        self.ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

        source_2 = magic_mixer.blend(core.models.Source)
        source_3 = magic_mixer.blend(core.models.Source)

        magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group, source=source_2)
        magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group, source=source_3)

        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=self.source, date=today, etfm_spend=200.0)

        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=source_2, date=today, etfm_spend=300.0)

        today = dates_helper.local_today()
        RealTimeDataHistory.objects.create(ad_group=self.ad_group, source=source_3, date=today, etfm_spend=500.0)

        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)
        selection.mark_almost_depleted_campaigns()
        self.assertTrue(CampaignStopState.objects.filter(campaign=self.campaign).first().almost_depleted)

    def _setup_initial_state(self):
        self.today = dates_helper.local_today()
        self.campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)
        user = magic_mixer.blend_user()
        self.campaign.settings.update(None, campaign_manager=user)
        self.campaign_goal = magic_mixer.blend(core.features.goals.CampaignGoal, campaign=self.campaign, primary=True)
        self.campaign_stop_state = magic_mixer.blend(
            CampaignStopState, campaign=self.campaign, almost_depleted=False, state=constants.CampaignStopState.ACTIVE
        )
        self.credit_line_item = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(self.today, 30),
            end_date=dates_helper.days_after(self.today, 30),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=1000,
            license_fee="0.1",
        )
        self.budget_line_item = magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            credit=self.credit_line_item,
            campaign=self.campaign,
            start_date=dates_helper.days_before(self.today, 7),
            end_date=self.today,
            credit_line_item=self.credit_line_item,
            amount=900,
        )
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.source_type = magic_mixer.blend(core.models.source_type.SourceType)
        self.source = magic_mixer.blend(core.models.Source, type=self.source_type)
        self.ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group, source=self.source)
        self.ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
