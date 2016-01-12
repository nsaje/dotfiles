import mock

from django.core import management
from django.test import TestCase


class MonitorPublisherBlacklistTest(TestCase):

    def setUp(self):
        self.patcher = mock.patch('reports.redshift.get_cursor')
        self.get_cursor = self.patcher.start()

    def test_run_adgroup(self):
        self.get_cursor().dictfetchall.return_value = [
            {
                'domain': u'celebrity-soldiers.littlethings.com',
                'adgroup_id': 1,
                'exchange': u'triplelift',
                'billing_cost_nano_sum': 0.0,
                'impressions_sum': 1000,
                'clicks_sum': 0L,
                'ctr': 0.0,
                'external_id': u'celebrity-soldiers.littlethings.com',
             }
        ]
        management.call_command('monitor_blacklist')

    def test_run_global(self):
        self.get_cursor().dictfetchall.return_value = [
            {
                'domain': u'celebrity-soldiers.littlethings.com',
                'adgroup_id': 1,
                'exchange': u'triplelift',
                'billing_cost_nano_sum': 0.0,
                'impressions_sum': 1000,
                'clicks_sum': 0L,
                'ctr': 0.0,
                'external_id': u'celebrity-soldiers.littlethings.com',
             }
        ]
        management.call_command('monitor_blacklist')

    def test_run_outbrain(self):
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
