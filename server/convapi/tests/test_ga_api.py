from datetime import date

import mock
from django.test import TestCase

from convapi.ga_api import GAApiReport
from dash.models import GAAnalyticsAccount


class TestGAApiReport(TestCase):
    @mock.patch.object(GAApiReport, '_get_ga_profiles')
    @mock.patch.object(GAApiReport, '_get_ga_goals')
    @mock.patch.object(GAApiReport, '_download_stats_from_ga')
    def test_download(self, _download_stats_from_ga_mock, _get_ga_goals_mock, _get_ga_profiles_mock):
        _get_ga_profiles_mock.return_value = self._create_ga_profiles_mock()
        _get_ga_goals_mock.return_value = self._create_ga_goals_mock()
        _download_stats_from_ga_mock.side_effect = self._download_stats_from_ga_side_effect
        start_date = date(2015, 12, 7)
        ga_reports = GAApiReport(None, start_date)
        ga_account = GAAnalyticsAccount()
        ga_account.ga_account_id = '1234567'
        ga_account.ga_web_property_id = 'UA-1234567-12'
        ga_reports.download(ga_account)
        self.assertTrue(len(ga_reports.entries) == 2)
        expected_key = ('2015-12-07', 42001, 'b1_pubmatic')
        self.assertTrue(expected_key in ga_reports.entries)
        expected_key2 = ('2015-12-07', 42002, 'b1_pubmatic')
        self.assertTrue(expected_key2 in ga_reports.entries)
        self.assertEqual(
            '["/driving/voltbolt/?_z1_adgid=830&_z1_caid=42001&_z1_msid=b1_pubmatic&_z1_disga=zemgagood&_z1_pub=www.test.com", "(not set)", "2", "1", "100.0", "1", "10.0"]',
            ga_reports.entries[expected_key].raw_row)

        entry = ga_reports.entries[expected_key]
        self.assertEqual(4, entry.visits)
        self.assertEqual(1.0, entry.bounce_rate)
        self.assertEqual(2, entry.pageviews)
        self.assertEqual(2, entry.new_visits)
        self.assertEqual(4, entry.bounced_visits)
        self.assertEqual(20, entry.total_time_on_site)

        self.assertEqual({'E-zin subscription': 4}, entry.goals)

        entry2 = ga_reports.entries[expected_key2]
        self.assertEqual(1, entry2.visits)
        self.assertEqual(1.0, entry2.bounce_rate)
        self.assertEqual(1, entry2.pageviews)
        self.assertEqual(1, entry2.new_visits)
        self.assertEqual(1, entry2.bounced_visits)
        self.assertEqual(10, entry2.total_time_on_site)

        self.assertEqual({'E-zin subscription': 1}, entry2.goals)

    def _create_ga_profiles_mock(self):
        return {'items': [{'id': '100021248', 'accountId': '2175716', 'webPropertyId': 'UA-2175716-35'}],
                'itemsPerPage': 1000, 'startIndex': 1, 'totalResults': 1}

    def _create_ga_goals_mock(self):
        return {'items': [{'id': '1', 'name': 'E-zin subscription', 'accountId': '2175716', 'value': 0.0}],
                'itemsPerPage': 1000, 'startIndex': 1, 'totalResults': 1}

    def _download_stats_from_ga_side_effect(self, start_date, profile_id, metrics, start_index):
        if metrics == 'ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite':
            return {'rows': [
                ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42001&_z1_msid=b1_pubmatic&_z1_disga=zemgagood&_z1_pub=www.test.com', '(not set)', '2', '1', '100.0', '1', '10.0'],
                ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42001&_z1_msid=b1_pubmatic&_z1_disga=zemgagood&_z1_pub=www.foo.com', '(not set)', '2', '1', '100.0', '1', '10.0'],
                ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42002&_z1_msid=b1_pubmatic&_z1_disga=zemgagood&_z1_pub=www.foo.com', '(not set)', '1', '1', '100.0', '1', '10.0']
                ], 'itemsPerPage': 1000, 'totalResults': 3}
        elif metrics == 'ga:goal1Completions':
            return {'rows': [
                ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42001&_z1_msid=b1_pubmatic&_z1_disga=zemgagood&_z1_pub=www.test.com', '(not set)', '2'],
                ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42001&_z1_msid=b1_pubmatic&_z1_disga=zemgagood&_z1_pub=www.foo.com', '(not set)', '2'],
                ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42002&_z1_msid=b1_pubmatic&_z1_disga=zemgagood&_z1_pub=www.foo.com', '(not set)', '1'],
                ], 'itemsPerPage': 1000, 'totalResults': 3}
        else:
            raise Exception('Undefined GA metrics: ' + metrics)
