import datetime
from django.test import TestCase

import dash.models

from stats import api_reports


class ApiReportsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_get_filename(self):
        self.assertEqual(api_reports.get_filename(['publisher_id'], {
            'date__gte': datetime.date(2016, 10, 10),
            'date__lte': datetime.date(2016, 10, 20),
            'allowed_accounts': dash.models.Account.objects.filter(pk__in=[1]),
            'allowed_campaigns': dash.models.Campaign.objects.filter(pk__in=[1]),
            'allowed_ad_groups': dash.models.AdGroup.objects.filter(pk__in=[1, 2]),
        }), 'test-account-1_test-campaign-1_by_publisher_report_2016-10-10_2016-10-20')

        self.assertEqual(api_reports.get_filename(['publisher_id', 'day'], {
            'date__gte': datetime.date(2016, 10, 10),
            'date__lte': datetime.date(2016, 10, 20),
            'allowed_accounts': dash.models.Account.objects.filter(pk__in=[1]),
            'allowed_campaigns': dash.models.Campaign.objects.filter(pk__in=[1]),
            'allowed_ad_groups': dash.models.AdGroup.objects.filter(pk__in=[1]),
        }), 'test-account-1_test-campaign-1_test-adgroup-1_by_publisher_by_day_report_2016-10-10_2016-10-20')

        self.assertEqual(api_reports.get_filename(['publisher_id', 'week'], {
            'date__gte': datetime.date(2016, 10, 10),
            'date__lte': datetime.date(2016, 10, 20),
            'allowed_accounts': dash.models.Account.objects.filter(pk__in=[1]),
            'allowed_campaigns': dash.models.Campaign.objects.none(),
            'allowed_ad_groups': dash.models.AdGroup.objects.none(),
        }), 'test-account-1_by_publisher_by_week_report_2016-10-10_2016-10-20')
