import datetime
import mock

import dash.constants
import dash.models

from django.core import management
from django.test import TestCase

from utils import statsd_helper


class MonitorPublisherBlacklistTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.patcher = mock.patch('reports.redshift.get_cursor')
        self.get_cursor = self.patcher.start()

    @mock.patch('utils.statsd_helper.statsd_gauge')
    def test_run_adgroup(self, statsd_gauge_mock):
        dash.models.PublisherBlacklist.objects.create(
            name='bollocks.com',
            ad_group=dash.models.AdGroup.objects.get(pk=1),
            source=dash.models.Source.objects.get(tracking_slug='b1_adiant'),
            status=dash.constants.PublisherStatus.BLACKLISTED,
        )

        self.get_cursor().dictfetchall.return_value = [
            {
                'domain': u'bollocks.com',
                'adgroup_id': 1,
                'exchange': u'adiant',
                'billing_cost_nano_sum': 0.0,
                'impressions_sum': 1000,
                'clicks_sum': 0L,
                'ctr': 0.0,
                'external_id': u'1234567890',
             }
        ]
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        management.call_command('monitor_blacklist', blacklisted_before=tomorrow.date().isoformat())
        statsd_gauge_mock.assert_has_calls(
            [
                mock.call('dash.blacklisted_publisher_stats.impressions', 1000)
            ]
        )

    @mock.patch('utils.statsd_helper.statsd_gauge')
    def test_run_global(self, statsd_gauge_mock):
        dash.models.PublisherBlacklist.objects.create(
            name='bollocks.com',
            everywhere=True,
            source=dash.models.Source.objects.get(tracking_slug='b1_adiant'),
            status=dash.constants.PublisherStatus.BLACKLISTED,
        )

        self.get_cursor().dictfetchall.return_value = [
            {
                'domain': u'bollocks.com',
                'adgroup_id': 1,
                'exchange': u'adiant',
                'billing_cost_nano_sum': 0.0,
                'impressions_sum': 1000,
                'clicks_sum': 0L,
                'ctr': 0.0,
                'external_id': u'1234567890',
             }
        ]
        management.call_command('monitor_blacklist')

        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        management.call_command('monitor_blacklist', blacklisted_before=tomorrow.date().isoformat())
        statsd_gauge_mock.assert_has_calls(
            [
                mock.call('dash.blacklisted_publisher_stats.global_impressions', 1000)
            ]
        )

    def test_run_outbrain(self):
        dash.models.PublisherBlacklist.objects.create(
            name='bollocks.com',
            account=dash.models.Account.objects.get(pk=1),
            source=dash.models.Source.objects.get(tracking_slug='outbrain'),
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        self.get_cursor().dictfetchall.return_value = [
            {
                'domain': u'Awesome Publisher',
                'adgroup_id': 1,
                'exchange': u'outbrain',
                'external_id': '12345',
                'billing_cost_nano_sum': 0.0,
                'impressions_sum': 1000,
                'clicks_sum': 0L,
                'ctr': 0.0,
                'external_id': u'celebrity-soldiers.littlethings.com',
             }
        ]
        management.call_command('monitor_blacklist')
