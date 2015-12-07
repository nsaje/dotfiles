import datetime
import mock

from django import test
from mock import patch

import reports.refresh
import reports.demo
import reports.update
import reports.api
import reports.api_contentads
import dash.models


class RefreshDemoTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml', 'test_demo.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

        reports.refresh.refresh_adgroup_stats()
        reports.refresh.refresh_adgroup_conversion_stats()
        self.start_date = datetime.date(2014, 6, 4)
        self.end_date = datetime.date(2014, 6, 6)
        self.demo_ad_groups = dash.models.AdGroup.demo_objects.all()
        self.real_ad_groups = dash.models.AdGroup.objects.exclude(pk__in=self.demo_ad_groups)

    def test_refresh_demo(self):
        demo_data_before_refresh = reports.api.query(
            start_date=self.start_date,
            end_date=self.end_date,
            breakdown=['ad_group'],
            order=['-clicks'],
            ad_group=self.demo_ad_groups
        )
        self.assertTrue(all(d['clicks'] is None for d in demo_data_before_refresh))
        self.assertTrue(all(d['impressions'] is None for d in demo_data_before_refresh))

        reports.demo.refresh_demo_data(self.start_date, self.end_date)

        demo_data_after_refresh = reports.api.query(
            start_date=self.start_date,
            end_date=self.end_date,
            breakdown=['ad_group'],
            order=['-clicks'],
            ad_group=self.demo_ad_groups
        )
        for row in demo_data_after_refresh:
            demo_ad_group_id = row['ad_group']
            real_ad_group_id = dash.models.DemoAdGroupRealAdGroup.objects.get(demo_ad_group=demo_ad_group_id).real_ad_group.id
            multiplication_factor = dash.models.DemoAdGroupRealAdGroup.objects.get(demo_ad_group=demo_ad_group_id).multiplication_factor
            real_data = reports.api.query(self.start_date, self.end_date, ad_group=real_ad_group_id)
            self.assertEqual(row['clicks'], real_data['clicks'] * multiplication_factor)
            self.assertEqual(row['impressions'], real_data['impressions'] * multiplication_factor)
