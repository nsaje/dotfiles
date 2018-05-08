import datetime
import decimal
import mock
import itertools

from django.conf import settings
from django.test import TestCase
import pytz

import core.features.yahoo_accounts
import core.entity
import core.source
import dash.constants
from utils.magic_mixer import magic_mixer
from utils import dates_helper

from .. import RealTimeDataHistory, RealTimeCampaignDataHistory
from . import refresh_realtime_data


class RefreshRealtimeDataTest(TestCase):

    def setUp(self):
        self.account = magic_mixer.blend(core.entity.Account, yahoo_account__budgets_tz='America/Los_Angeles')
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True, account=self.account)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)
        self.source_type = magic_mixer.blend(core.source.SourceType, budgets_tz=pytz.utc)
        self.source = magic_mixer.blend(core.source.Source, source_type=self.source_type)
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=self.source)

        self.data = {
            'stats': [{
                'source': self.source,
                'spend': decimal.Decimal('12.0'),
            }]
        }

    # @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats_without_caching')
    # def test_refresh_realtime_data(self, mock_get_realtime_data):
    #     mock_get_realtime_data.return_value = self.data

    #     self.assertFalse(RealTimeDataHistory.objects.exists())
    #     self.assertFalse(RealTimeCampaignDataHistory.objects.exists())

    #     refresh_realtime_data()
    #     self.assertEqual(1, RealTimeDataHistory.objects.count())
    #     self.assertEqual(1, RealTimeCampaignDataHistory.objects.count())

    #     history = RealTimeDataHistory.objects.get()
    #     self.assertEqual(self.ad_group.id, history.ad_group_id)
    #     self.assertEqual(self.source.id, history.source_id)
    #     self.assertEqual(dates_helper.utc_today(), history.date)
    #     self.assertEqual(self.data['stats'][0]['spend'], history.etfm_spend)

    #     campaign_history = RealTimeCampaignDataHistory.objects.get()
    #     self.assertEqual(self.campaign.id, campaign_history.campaign_id)
    #     self.assertEqual(dates_helper.utc_today(), campaign_history.date)
    #     self.assertEqual(self.data['stats'][0]['spend'], campaign_history.etfm_spend)

    @mock.patch('automation.campaignstop.service.refresh.influx')
    @mock.patch('automation.campaignstop.service.refresh.logger')
    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats_without_caching')
    def test_refresh_realtime_data_exception(self, mock_get_realtime_data, mock_logger, mock_influx):
        mock_get_realtime_data.side_effect = Exception()

        self.assertFalse(RealTimeDataHistory.objects.exists())
        self.assertFalse(RealTimeCampaignDataHistory.objects.exists())

        refresh_realtime_data()
        self.assertFalse(RealTimeDataHistory.objects.exists())

        mock_influx.incr.assert_called_once_with('campaignstop.refresh.error', 1, level='adgroup')
        mock_logger.exception.assert_called_once()

    # @mock.patch('automation.campaignstop.service.refresh.influx')
    # @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats_without_caching')
    # def test_refresh_realtime_data_source_error(self, mock_get_realtime_data, mock_influx):
    #     source_1 = self.source
    #     source_2 = magic_mixer.blend(core.source.Source, source_type__budgets_tz=pytz.utc, bidder_slug='s_2')
    #     RealTimeDataHistory.objects.create(
    #         ad_group=self.ad_group,
    #         source=source_1,
    #         date=dates_helper.utc_today(),
    #         etfm_spend='1.0',
    #     )
    #     RealTimeDataHistory.objects.create(
    #         ad_group=self.ad_group,
    #         source=source_2,
    #         date=dates_helper.utc_today(),
    #         etfm_spend='5.0',
    #     )

    #     mock_get_realtime_data.return_value = {
    #         'stats': [{
    #             'source': source_1,
    #             'spend': decimal.Decimal('12.0'),
    #         }],
    #         'errors': {
    #             source_2.bidder_slug: 'Error',
    #         }
    #     }

    #     refresh_realtime_data()

    #     current_source_1 = RealTimeDataHistory.objects.filter(source=source_1).latest('created_dt')
    #     current_source_2 = RealTimeDataHistory.objects.filter(source=source_2).latest('created_dt')
    #     campaign_data = RealTimeCampaignDataHistory.objects.filter(campaign=self.campaign).latest('created_dt')
    #     self.assertEqual(decimal.Decimal('12.0'), current_source_1.etfm_spend)
    #     self.assertEqual(decimal.Decimal('5.0'), current_source_2.etfm_spend)
    #     self.assertEqual(decimal.Decimal('17.0'), campaign_data.etfm_spend)

    #     mock_influx.incr.assert_called_once_with('campaignstop.refresh.error', 1, level='source', source=source_2.bidder_slug)

    # @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats_without_caching')
    # def test_add_updated_history_entry(self, mock_get_realtime_data):
    #     mock_get_realtime_data.return_value = self.data

    #     old_history = RealTimeDataHistory.objects.create(
    #         ad_group=self.ad_group,
    #         source=self.source,
    #         date=dates_helper.utc_today(),
    #         etfm_spend='5.0',
    #     )
    #     self.assertEqual(1, RealTimeDataHistory.objects.count())

    #     refresh_realtime_data()
    #     self.assertEqual(2, RealTimeDataHistory.objects.count())

    #     old_history.refresh_from_db()
    #     self.assertEqual(decimal.Decimal('5.0'), old_history.etfm_spend)

    #     new_history = RealTimeDataHistory.objects.latest('created_dt')
    #     self.assertEqual(self.ad_group.id, new_history.ad_group_id)
    #     self.assertEqual(self.source.id, new_history.source_id)
    #     self.assertEqual(dates_helper.utc_today(), new_history.date)
    #     self.assertEqual(self.data['stats'][0]['spend'], new_history.etfm_spend)

    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats_without_caching')
    def test_update_for_custom_campaign(self, mock_get_realtime_data):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=False)
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=ad_group, source=self.source)

        mock_get_realtime_data.return_value = self.data

        self.assertFalse(RealTimeDataHistory.objects.exists())

        refresh_realtime_data([campaign])
        self.assertFalse(RealTimeDataHistory.objects.exists())

    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats_without_caching')
    def test_refresh_budgets_tz_behind_source(self, mock_get_realtime_data):
        yahoo_source_type = magic_mixer.blend(
            core.source.SourceType, type=dash.constants.SourceType.YAHOO)
        yahoo_source = magic_mixer.blend(core.source.Source, source_type=yahoo_source_type)
        magic_mixer.blend(
            core.entity.AdGroupSource,
            ad_group=self.ad_group,
            source=yahoo_source,
        )

        data = {
            'stats': [{
                'source': yahoo_source,
                'spend': decimal.Decimal('10.0')
            }]
        }
        mock_get_realtime_data.return_value = data

        today = dates_helper.local_today()
        yesterday = dates_helper.local_yesterday()
        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            local_tz_offset = datetime.datetime.now(pytz.timezone(settings.DEFAULT_TIME_ZONE)).utcoffset()
            mock_utc_now.return_value = datetime.datetime(today.year, today.month, today.day) - local_tz_offset

            refresh_realtime_data([self.campaign])

        history = RealTimeDataHistory.objects.get()
        self.assertEqual(self.ad_group.id, history.ad_group_id)
        self.assertEqual(yahoo_source.id, history.source_id)
        self.assertEqual(dates_helper.local_yesterday(), history.date)
        self.assertEqual(data['stats'][0]['spend'], history.etfm_spend)

        campaign_history_today = RealTimeCampaignDataHistory.objects.get(date=today)
        self.assertEqual(self.campaign.id, campaign_history_today.campaign_id)
        self.assertEqual(today, campaign_history_today.date)
        self.assertEqual(0, campaign_history_today.etfm_spend)

        campaign_history_yesterday = RealTimeCampaignDataHistory.objects.get(date=yesterday)
        self.assertEqual(self.campaign.id, campaign_history_yesterday.campaign_id)
        self.assertEqual(yesterday, campaign_history_yesterday.date)
        self.assertEqual(data['stats'][0]['spend'], campaign_history_yesterday.etfm_spend)

    # @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats_without_caching')
    # def test_multiple(self, mock_get_realtime_data):
    #     campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)
    #     ad_groups = magic_mixer.cycle(2).blend(core.entity.AdGroup, campaign=campaign)
    #     sources = magic_mixer.cycle(2).blend(core.source.Source, source_type=self.source_type)
    #     for ad_group, source in itertools.product(ad_groups, sources):
    #         magic_mixer.blend(core.entity.AdGroupSource, ad_group=ad_group, source=source)

    #     rt_stats_before = {
    #         ad_groups[0]: {'stats': [{'source': sources[0], 'spend': decimal.Decimal('2.0')},
    #                                  {'source': sources[1], 'spend': decimal.Decimal('3.0')}]},
    #         ad_groups[1]: {'stats': [{'source': sources[0], 'spend': decimal.Decimal('8.0')},
    #                                  {'source': sources[1], 'spend': decimal.Decimal('1.0')}]},
    #     }
    #     mock_get_realtime_data.side_effect = lambda ad_group, **kwargs: rt_stats_before[ad_group]
    #     refresh_realtime_data([campaign])

    #     rt_stats_after = {
    #         ad_groups[0]: {'stats': [{'source': sources[0], 'spend': decimal.Decimal('2.0')},
    #                                  {'source': sources[1], 'spend': decimal.Decimal('3.0')}]},
    #         ad_groups[1]: {'stats': [{'source': sources[0], 'spend': decimal.Decimal('8.0')}]},
    #     }
    #     mock_get_realtime_data.side_effect = lambda ad_group, **kwargs: rt_stats_after[ad_group]
    #     refresh_realtime_data([campaign])

    #     campaign_history = RealTimeCampaignDataHistory.objects.filter(
    #         date=dates_helper.local_today()).latest('created_dt')
    #     self.assertEqual(campaign, campaign_history.campaign)
    #     self.assertEqual(decimal.Decimal('14.0'), campaign_history.etfm_spend)

    #     for ad_group, stats in list(rt_stats_after.items()):
    #         for stat in stats['stats']:
    #             history = RealTimeDataHistory.objects.filter(
    #                 ad_group=ad_group, source=stat['source']).latest('created_dt')
    #             self.assertEqual(dates_helper.utc_today(), history.date)
    #             self.assertEqual(stat['spend'], history.etfm_spend)
