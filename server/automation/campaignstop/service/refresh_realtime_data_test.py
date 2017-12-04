import datetime
import decimal
import mock
import itertools

from django.conf import settings
from django.test import TestCase
import pytz

import core.entity
import core.source
from utils.magic_mixer import magic_mixer
from utils import dates_helper

from .. import RealTimeDataHistory, RealTimeCampaignDataHistory
import refresh_realtime_data


class RefreshRealtimeDataTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)
        self.source_type = magic_mixer.blend(core.source.SourceType, budgets_tz=pytz.utc)
        self.source = magic_mixer.blend(core.source.Source, source_type=self.source_type)
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=self.source)

        self.data = [{
            'source': self.source,
            'spend': decimal.Decimal('12.0'),
        }]

    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats')
    def test_refresh_realtime_data(self, mock_get_realtime_data):
        mock_get_realtime_data.return_value = self.data

        self.assertFalse(RealTimeDataHistory.objects.exists())
        self.assertFalse(RealTimeCampaignDataHistory.objects.exists())

        refresh_realtime_data.refresh_realtime_data()
        self.assertEqual(1, RealTimeDataHistory.objects.count())
        self.assertEqual(1, RealTimeCampaignDataHistory.objects.count())

        history = RealTimeDataHistory.objects.get()
        self.assertEqual(self.ad_group.id, history.ad_group_id)
        self.assertEqual(self.source.id, history.source_id)
        self.assertEqual(dates_helper.utc_today(), history.date)
        self.assertEqual(self.data[0]['spend'], history.etfm_spend)

        campaign_history = RealTimeCampaignDataHistory.objects.get()
        self.assertEqual(self.campaign.id, campaign_history.campaign_id)
        self.assertEqual(dates_helper.utc_today(), campaign_history.date)
        self.assertEqual(self.data[0]['spend'], campaign_history.etfm_spend)

    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats')
    def test_add_updated_history_entry(self, mock_get_realtime_data):
        mock_get_realtime_data.return_value = self.data

        old_history = RealTimeDataHistory.objects.create(
            ad_group=self.ad_group,
            source=self.source,
            date=dates_helper.utc_today(),
            etfm_spend='5.0',
        )
        self.assertEqual(1, RealTimeDataHistory.objects.count())

        refresh_realtime_data.refresh_realtime_data()
        self.assertEqual(2, RealTimeDataHistory.objects.count())

        old_history.refresh_from_db()
        self.assertEqual(decimal.Decimal('5.0'), old_history.etfm_spend)

        new_history = RealTimeDataHistory.objects.latest('created_dt')
        self.assertEqual(self.ad_group.id, new_history.ad_group_id)
        self.assertEqual(self.source.id, new_history.source_id)
        self.assertEqual(dates_helper.utc_today(), new_history.date)
        self.assertEqual(self.data[0]['spend'], new_history.etfm_spend)

    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats')
    def test_update_for_custom_campaign(self, mock_get_realtime_data):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=False)
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=ad_group, source=self.source)

        mock_get_realtime_data.return_value = self.data

        self.assertFalse(RealTimeDataHistory.objects.exists())

        refresh_realtime_data.refresh_realtime_data([campaign])
        self.assertEqual(1, RealTimeDataHistory.objects.count())

    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats')
    def test_refresh_budgets_tz_behind_source(self, mock_get_realtime_data):
        pt_source_type = magic_mixer.blend(
            core.source.SourceType, budgets_tz=pytz.timezone('America/Los_Angeles'))
        pt_source = magic_mixer.blend(core.source.Source, source_type=pt_source_type)
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=pt_source)

        data = [{
            'source': pt_source,
            'spend': decimal.Decimal('10.0')
        }]
        mock_get_realtime_data.return_value = data

        today = dates_helper.local_today()
        yesterday = dates_helper.local_yesterday()
        with mock.patch('utils.dates_helper.utc_now') as mock_utc_now:
            local_tz_offset = datetime.datetime.now(pytz.timezone(settings.DEFAULT_TIME_ZONE)).utcoffset()
            mock_utc_now.return_value = datetime.datetime(today.year, today.month, today.day) - local_tz_offset

            refresh_realtime_data.refresh_realtime_data([self.campaign])

        history = RealTimeDataHistory.objects.get()
        self.assertEqual(self.ad_group.id, history.ad_group_id)
        self.assertEqual(pt_source.id, history.source_id)
        self.assertEqual(dates_helper.local_yesterday(), history.date)
        self.assertEqual(data[0]['spend'], history.etfm_spend)

        campaign_history_today = RealTimeCampaignDataHistory.objects.get(date=today)
        self.assertEqual(self.campaign.id, campaign_history_today.campaign_id)
        self.assertEqual(today, campaign_history_today.date)
        self.assertEqual(0, campaign_history_today.etfm_spend)

        campaign_history_yesterday = RealTimeCampaignDataHistory.objects.get(date=yesterday)
        self.assertEqual(self.campaign.id, campaign_history_yesterday.campaign_id)
        self.assertEqual(yesterday, campaign_history_yesterday.date)
        self.assertEqual(data[0]['spend'], campaign_history_yesterday.etfm_spend)

    @mock.patch('dash.features.realtimestats.get_ad_group_sources_stats')
    def test_multiple(self, mock_get_realtime_data):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=False)
        ad_groups = magic_mixer.cycle(2).blend(core.entity.AdGroup, campaign=campaign)
        sources = magic_mixer.cycle(2).blend(core.source.Source, source_type=self.source_type)
        for ad_group, source in itertools.product(ad_groups, sources):
            magic_mixer.blend(core.entity.AdGroupSource, ad_group=ad_group, source=source)

        rt_stats_before = {
            ad_groups[0]: [{'source': sources[0], 'spend': decimal.Decimal('2.0')},
                           {'source': sources[1], 'spend': decimal.Decimal('3.0')}],
            ad_groups[1]: [{'source': sources[0], 'spend': decimal.Decimal('8.0')},
                           {'source': sources[1], 'spend': decimal.Decimal('1.0')}],
        }
        mock_get_realtime_data.side_effect = lambda ad_group: rt_stats_before[ad_group]
        refresh_realtime_data.refresh_realtime_data([campaign])

        rt_stats_after = {
            ad_groups[0]: [{'source': sources[0], 'spend': decimal.Decimal('2.0')},
                           {'source': sources[1], 'spend': decimal.Decimal('3.0')}],
            ad_groups[1]: [{'source': sources[0], 'spend': decimal.Decimal('8.0')}],
        }
        mock_get_realtime_data.side_effect = lambda ad_group: rt_stats_after[ad_group]
        refresh_realtime_data.refresh_realtime_data([campaign])

        campaign_history = RealTimeCampaignDataHistory.objects.filter(
            date=dates_helper.local_today()).latest('created_dt')
        self.assertEqual(campaign, campaign_history.campaign)
        self.assertEqual(decimal.Decimal('14.0'), campaign_history.etfm_spend)

        for ad_group, stats in rt_stats_after.items():
            for stat in stats:
                history = RealTimeDataHistory.objects.filter(
                    ad_group=ad_group, source=stat['source']).latest('created_dt')
                self.assertEqual(dates_helper.utc_today(), history.date)
                self.assertEqual(stat['spend'], history.etfm_spend)
