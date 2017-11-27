import decimal
import mock

from django.test import TestCase
import pytz

import core.entity
import core.source
from utils.magic_mixer import magic_mixer
from utils import dates_helper

from .. import RealTimeDataHistory
import refresh_realtime_data


class RefreshRealtimeDataTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)
        source_type = magic_mixer.blend(core.source.SourceType, budgets_tz=pytz.utc)
        self.source = magic_mixer.blend(core.source.Source, source_type=source_type)
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=self.ad_group, source=self.source)

        self.data = [{
            'source': self.source,
            'spend': decimal.Decimal('12.0'),
        }]

    @mock.patch('dash.features.realtimestats.service.get_ad_group_sources_stats')
    def test_refresh_realtime_data(self, mock_get_realtime_data):
        mock_get_realtime_data.return_value = self.data

        self.assertFalse(RealTimeDataHistory.objects.exists())

        refresh_realtime_data.refresh_realtime_data()
        self.assertEqual(1, RealTimeDataHistory.objects.count())

        history = RealTimeDataHistory.objects.get()
        self.assertEqual(self.ad_group.id, history.ad_group_id)
        self.assertEqual(self.source.id, history.source_id)
        self.assertEqual(dates_helper.utc_today(), history.date)
        self.assertEqual(self.data[0]['spend'], history.etfm_spend)

    @mock.patch('dash.features.realtimestats.service.get_ad_group_sources_stats')
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

    @mock.patch('dash.features.realtimestats.service.get_ad_group_sources_stats')
    def test_update_for_custom_campaign(self, mock_get_realtime_data):
        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=False)
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)
        magic_mixer.blend(core.entity.AdGroupSource, ad_group=ad_group, source=self.source)

        mock_get_realtime_data.return_value = self.data

        self.assertFalse(RealTimeDataHistory.objects.exists())

        refresh_realtime_data.refresh_realtime_data([campaign])
        self.assertEqual(1, RealTimeDataHistory.objects.count())
