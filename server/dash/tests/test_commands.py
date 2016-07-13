import datetime
import mock

import dash.constants
import dash.models

from django.core import management
from django.test import TestCase


class MonitorPublisherBlacklistTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.patcher = mock.patch('reports.redshift.get_cursor')
        self.get_cursor = self.patcher.start()

    @mock.patch('influx.gauge')
    def test_run_adgroup(self, influx_gauge_mock):
        dash.models.PublisherBlacklist.objects.create(
            name='bollocks.com',
            ad_group=dash.models.AdGroup.objects.get(pk=1),
            source=dash.models.Source.objects.get(tracking_slug='b1_adiant'),
            status=dash.constants.PublisherStatus.BLACKLISTED,
        )

        self.get_cursor().dictfetchall.return_value = [{
            'domain': u'bollocks.com',
            'adgroup_id': 1,
            'exchange': u'adiant',
            'billing_cost_nano_sum': 0.0,
            'impressions_sum': 1000,
            'clicks_sum': 5L,
            'ctr': 0.0,
            'external_id': u'1234567890',
        }]
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        management.call_command('monitor_blacklist', blacklisted_before=tomorrow.date().isoformat())
        influx_gauge_mock.assert_has_calls(
            [
                mock.call('dash.blacklisted_publisher.stats', 1000, type='impressions'),
                mock.call('dash.blacklisted_publisher.stats', 5, type='clicks'),
            ]
        )

    @mock.patch('influx.gauge')
    def test_run_global(self, influx_gauge_mock):
        dash.models.PublisherBlacklist.objects.create(
            name='bollocks.com',
            everywhere=True,
            source=dash.models.Source.objects.get(tracking_slug='b1_adiant'),
            status=dash.constants.PublisherStatus.BLACKLISTED,
        )

        self.get_cursor().dictfetchall.return_value = [{
            'domain': u'bollocks.com',
            'adgroup_id': 1,
            'exchange': u'adiant',
            'billing_cost_nano_sum': 0.0,
            'impressions_sum': 1000,
            'clicks_sum': 5L,
            'ctr': 0.0,
            'external_id': u'1234567890',
        }]
        management.call_command('monitor_blacklist')

        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        management.call_command('monitor_blacklist', blacklisted_before=tomorrow.date().isoformat())
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        influx_gauge_mock.assert_has_calls(
            [
                mock.call('dash.blacklisted_publisher.stats', 1000, type='global_impressions'),
                mock.call('dash.blacklisted_publisher.stats', 5, type='global_clicks'),
            ]
        )

    @mock.patch('influx.gauge')
    def test_run_outbrain(self, influx_gauge_mock):
        dash.models.PublisherBlacklist.objects.create(
            name='Awesome Publisher',
            account=dash.models.Account.objects.get(pk=1),
            source=dash.models.Source.objects.get(tracking_slug='outbrain'),
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        self.get_cursor().dictfetchall.return_value = [{
            'domain': u'Awesome Publisher',
            'adgroup_id': 1,
            'exchange': u'outbrain',
            'billing_cost_nano_sum': 0.0,
            'impressions_sum': 1000,
            'clicks_sum': 5L,
            'ctr': 0.0,
            'external_id': u'RandomUuid',
        }]
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        management.call_command('monitor_blacklist', blacklisted_before=tomorrow.date().isoformat())
        influx_gauge_mock.assert_has_calls(
            [
                mock.call('dash.blacklisted_publisher.stats', 1000, type='impressions'),
                mock.call('dash.blacklisted_publisher.stats', 5, type='clicks'),
            ]
        )
