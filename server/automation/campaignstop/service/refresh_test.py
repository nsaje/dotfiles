import datetime
import decimal
import itertools

import mock
import pytz
from django.test import TestCase

import core.models
from utils import dates_helper
from utils import test_helper
from utils.magic_mixer import magic_mixer

from .. import RealTimeCampaignDataHistory
from .. import RealTimeDataHistory
from . import refresh


class RefreshRealtimeDataTest(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)
        self.campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.source_type = magic_mixer.blend(core.models.SourceType, budgets_tz=pytz.utc)
        self.source = magic_mixer.blend(core.models.Source, source_type=self.source_type)
        magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group, source=self.source)

        self.data = {"spend": [{"source": self.source, "spend": decimal.Decimal("12.0")}]}

    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_refresh_realtime_data(self, mock_get_realtime_data):
        mock_get_realtime_data.return_value = self.data

        self.assertFalse(RealTimeDataHistory.objects.exists())
        self.assertFalse(RealTimeCampaignDataHistory.objects.exists())

        refresh.refresh_realtime_data()
        self.assertEqual(1, RealTimeDataHistory.objects.count())
        self.assertEqual(1, RealTimeCampaignDataHistory.objects.count())

        history = RealTimeDataHistory.objects.get()
        self.assertEqual(self.ad_group.id, history.ad_group_id)
        self.assertEqual(self.source.id, history.source_id)
        self.assertEqual(dates_helper.utc_today(), history.date)
        self.assertEqual(self.data["spend"][0]["spend"], history.etfm_spend)

        campaign_history = RealTimeCampaignDataHistory.objects.get()
        self.assertEqual(self.campaign.id, campaign_history.campaign_id)
        self.assertEqual(dates_helper.utc_today(), campaign_history.date)
        self.assertEqual(self.data["spend"][0]["spend"], campaign_history.etfm_spend)

    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_refresh_archived_adgroup_today(self, mock_get_realtime_data):
        mock_get_realtime_data.return_value = self.data

        self.ad_group.archive(None)

        self.assertFalse(RealTimeDataHistory.objects.exists())
        self.assertFalse(RealTimeCampaignDataHistory.objects.exists())

        refresh.refresh_realtime_data()
        self.assertEqual(1, RealTimeDataHistory.objects.count())
        self.assertEqual(1, RealTimeCampaignDataHistory.objects.count())

        history = RealTimeDataHistory.objects.get()
        self.assertEqual(self.ad_group.id, history.ad_group_id)
        self.assertEqual(self.source.id, history.source_id)
        self.assertEqual(dates_helper.utc_today(), history.date)
        self.assertEqual(self.data["spend"][0]["spend"], history.etfm_spend)

        campaign_history = RealTimeCampaignDataHistory.objects.get()
        self.assertEqual(self.campaign.id, campaign_history.campaign_id)
        self.assertEqual(dates_helper.utc_today(), campaign_history.date)
        self.assertEqual(self.data["spend"][0]["spend"], campaign_history.etfm_spend)

    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_refresh_archived_adgroup_in_the_past(self, mock_get_realtime_data):
        mock_get_realtime_data.return_value = self.data

        with mock.patch("utils.dates_helper.utc_now") as mock_now:
            mock_now.return_value = datetime.datetime(2000, 1, 1)
            self.ad_group.archive(None)

        self.assertFalse(RealTimeDataHistory.objects.exists())
        self.assertFalse(RealTimeCampaignDataHistory.objects.exists())

        refresh.refresh_realtime_data()
        self.assertFalse(RealTimeDataHistory.objects.exists())

        # empty campaign history
        campaign_history = RealTimeCampaignDataHistory.objects.get()
        self.assertEqual(self.campaign.id, campaign_history.campaign_id)
        self.assertEqual(dates_helper.utc_today(), campaign_history.date)
        self.assertEqual(0, campaign_history.etfm_spend)

    @mock.patch("automation.campaignstop.service.refresh.metrics_compat")
    @mock.patch("automation.campaignstop.service.refresh.logger")
    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_refresh_realtime_data_exception(self, mock_get_realtime_data, mock_logger, mock_metrics_compat):
        mock_get_realtime_data.side_effect = Exception()

        self.assertFalse(RealTimeDataHistory.objects.exists())
        self.assertFalse(RealTimeCampaignDataHistory.objects.exists())

        refresh.refresh_realtime_data()
        self.assertFalse(RealTimeDataHistory.objects.exists())

        mock_metrics_compat.incr.assert_called_once_with("campaignstop.refresh.error", 1, level="adgroup")
        mock_logger.exception.assert_called_once()

    @mock.patch("automation.campaignstop.service.refresh.metrics_compat")
    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_refresh_realtime_data_source_error(self, mock_get_realtime_data, mock_metrics_compat):
        source_1 = self.source
        source_2 = magic_mixer.blend(core.models.Source, source_type__budgets_tz=pytz.utc, bidder_slug="s_2")
        RealTimeDataHistory.objects.create(
            ad_group=self.ad_group, source=source_1, date=dates_helper.utc_today(), etfm_spend="1.0"
        )
        RealTimeDataHistory.objects.create(
            ad_group=self.ad_group, source=source_2, date=dates_helper.utc_today(), etfm_spend="5.0"
        )

        mock_get_realtime_data.return_value = {
            "spend": [{"source": source_1, "spend": decimal.Decimal("12.0")}],
            "errors": {source_2.bidder_slug: "Error"},
        }

        refresh.refresh_realtime_data()

        current_source_1 = RealTimeDataHistory.objects.filter(source=source_1).latest("created_dt")
        current_source_2 = RealTimeDataHistory.objects.filter(source=source_2).latest("created_dt")
        campaign_data = RealTimeCampaignDataHistory.objects.filter(campaign=self.campaign).latest("created_dt")
        self.assertEqual(decimal.Decimal("12.0"), current_source_1.etfm_spend)
        self.assertEqual(decimal.Decimal("5.0"), current_source_2.etfm_spend)
        self.assertEqual(decimal.Decimal("17.0"), campaign_data.etfm_spend)

        mock_metrics_compat.incr.assert_called_once_with(
            "campaignstop.refresh.error", 1, level="source", source=source_2.bidder_slug
        )

    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_add_updated_history_entry(self, mock_get_realtime_data):
        mock_get_realtime_data.return_value = self.data

        old_history = RealTimeDataHistory.objects.create(
            ad_group=self.ad_group, source=self.source, date=dates_helper.utc_today(), etfm_spend="5.0"
        )
        self.assertEqual(1, RealTimeDataHistory.objects.count())

        refresh.refresh_realtime_data()
        self.assertEqual(2, RealTimeDataHistory.objects.count())

        old_history.refresh_from_db()
        self.assertEqual(decimal.Decimal("5.0"), old_history.etfm_spend)

        new_history = RealTimeDataHistory.objects.latest("created_dt")
        self.assertEqual(self.ad_group.id, new_history.ad_group_id)
        self.assertEqual(self.source.id, new_history.source_id)
        self.assertEqual(dates_helper.utc_today(), new_history.date)
        self.assertEqual(self.data["spend"][0]["spend"], new_history.etfm_spend)

    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_update_for_custom_campaign(self, mock_get_realtime_data):
        campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=False)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group, source=self.source)

        mock_get_realtime_data.return_value = self.data

        self.assertFalse(RealTimeDataHistory.objects.exists())

        refresh.refresh_realtime_data([campaign])
        self.assertFalse(RealTimeDataHistory.objects.exists())

    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats_without_caching")
    def test_multiple(self, mock_get_realtime_data):
        campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)
        ad_groups = magic_mixer.cycle(2).blend(core.models.AdGroup, campaign=campaign)
        sources = magic_mixer.cycle(2).blend(core.models.Source, source_type=self.source_type)
        for ad_group, source in itertools.product(ad_groups, sources):
            magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group, source=source)

        rt_stats_before = {
            ad_groups[0]: {
                "spend": [
                    {"source": sources[0], "spend": decimal.Decimal("2.0")},
                    {"source": sources[1], "spend": decimal.Decimal("3.0")},
                ]
            },
            ad_groups[1]: {
                "spend": [
                    {"source": sources[0], "spend": decimal.Decimal("8.0")},
                    {"source": sources[1], "spend": decimal.Decimal("1.0")},
                ]
            },
        }
        mock_get_realtime_data.side_effect = lambda ad_group, **kwargs: rt_stats_before[ad_group]
        refresh.refresh_realtime_data([campaign])

        rt_stats_after = {
            ad_groups[0]: {
                "spend": [
                    {"source": sources[0], "spend": decimal.Decimal("2.0")},
                    {"source": sources[1], "spend": decimal.Decimal("3.0")},
                ]
            },
            ad_groups[1]: {"spend": [{"source": sources[0], "spend": decimal.Decimal("8.0")}]},
        }
        mock_get_realtime_data.side_effect = lambda ad_group, **kwargs: rt_stats_after[ad_group]
        refresh.refresh_realtime_data([campaign])

        campaign_history = RealTimeCampaignDataHistory.objects.filter(date=dates_helper.local_today()).latest(
            "created_dt"
        )
        self.assertEqual(campaign, campaign_history.campaign)
        self.assertEqual(decimal.Decimal("14.0"), campaign_history.etfm_spend)

        for ad_group, stats in list(rt_stats_after.items()):
            for stat in stats["spend"]:
                history = RealTimeDataHistory.objects.filter(ad_group=ad_group, source=stat["source"]).latest(
                    "created_dt"
                )
                self.assertEqual(dates_helper.utc_today(), history.date)
                self.assertEqual(stat["spend"], history.etfm_spend)


class RefreshIfStaleTest(TestCase):
    def setUp(self):
        self.campaign_current_data = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)
        self.campaign_stale_data = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)
        self.campaign_no_data = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)
        self.campaign_without_campaing_stop = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=False)

        self.utc_now_mock = datetime.datetime(2018, 5, 28, 12)
        with test_helper.disable_auto_now_add(RealTimeCampaignDataHistory, "created_dt"):
            RealTimeCampaignDataHistory.objects.create(
                campaign=self.campaign_current_data,
                date=self.utc_now_mock.date(),
                created_dt=self.utc_now_mock - datetime.timedelta(seconds=300),
                etfm_spend="1.0",
            )
            RealTimeCampaignDataHistory.objects.create(
                campaign=self.campaign_current_data,
                date=self.utc_now_mock.date(),
                created_dt=self.utc_now_mock - datetime.timedelta(seconds=60),
                etfm_spend="1.0",
            )
            RealTimeCampaignDataHistory.objects.create(
                campaign=self.campaign_stale_data,
                date=self.utc_now_mock.date(),
                created_dt=self.utc_now_mock - datetime.timedelta(seconds=300),
                etfm_spend="1.0",
            )

    @mock.patch("automation.campaignstop.service.refresh.refresh_realtime_data")
    def test_current(self, mock_refresh):
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            mock_utc_now.return_value = self.utc_now_mock
            refresh.refresh_if_stale([self.campaign_current_data])
            called_with_campaigns = list(mock_refresh.call_args[0][0])
            self.assertEqual([], called_with_campaigns)

    @mock.patch("automation.campaignstop.service.refresh.refresh_realtime_data")
    def test_stale(self, mock_refresh):
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            mock_utc_now.return_value = self.utc_now_mock
            refresh.refresh_if_stale([self.campaign_stale_data])
            called_with_campaigns = list(mock_refresh.call_args[0][0])
            self.assertEqual([self.campaign_stale_data], called_with_campaigns)

    @mock.patch("automation.campaignstop.service.refresh.refresh_realtime_data")
    def test_no_data(self, mock_refresh):
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            mock_utc_now.return_value = self.utc_now_mock
            refresh.refresh_if_stale([self.campaign_no_data])
            called_with_campaigns = list(mock_refresh.call_args[0][0])
            self.assertEqual([self.campaign_no_data], called_with_campaigns)

    @mock.patch("automation.campaignstop.service.refresh.refresh_realtime_data")
    def test_campaign_stop_disabled(self, mock_refresh):
        with mock.patch("utils.dates_helper.utc_now") as mock_utc_now:
            mock_utc_now.return_value = self.utc_now_mock
            refresh.refresh_if_stale([self.campaign_without_campaing_stop])
            called_with_campaigns = list(mock_refresh.call_args[0][0])
            self.assertEqual([], called_with_campaigns)
