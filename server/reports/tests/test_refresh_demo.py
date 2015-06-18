import datetime

from django import test

import reports.refresh
import reports.demo
import reports.update
import reports.api
import reports.api_contentads
import dash.models

class RefreshContentAdDemoTestCase(test.TestCase):
    fixtures = ['test_api_contentads']
    def setUp(self):
        dash.models.DemoAdGroupRealAdGroup.objects.create(
            demo_ad_group_id=3,
            real_ad_group_id=1,
            multiplication_factor=10,
        )
        dash.models.DemoAdGroupRealAdGroup.objects.create(
            demo_ad_group_id=4,
            real_ad_group_id=2,
            multiplication_factor=10,
        )
        reports.refresh.refresh_adgroup_stats()
        reports.refresh.refresh_adgroup_conversion_stats()
        self.start_date = datetime.date(2015, 2, 1)
        self.end_date = datetime.date(2015, 2, 2)

        self.demo_ad_groups = dash.models.AdGroup.demo_objects.all()
        self.real_ad_groups = dash.models.AdGroup.objects.exclude(pk__in=self.demo_ad_groups)

    def test_refresh_demo(self):
        demo_data_before_refresh = reports.api_contentads.query(
            start_date=self.start_date,
            end_date=self.end_date,
            breakdown=['content_ad'],
            ad_group=self.demo_ad_groups
        )
        self.assertTrue(all(d['clicks'] is None for d in demo_data_before_refresh))
        self.assertTrue(all(d['impressions'] is None for d in demo_data_before_refresh))

        self._demo_batch_stats()
        # repeat because we get source and ad maps differently after first iteration
        self._demo_batch_stats() 

    def _demo_batch_stats(self):
        reports.demo.refresh_demo_data(self.start_date, self.end_date)
        for d2r in dash.models.DemoAdGroupRealAdGroup.objects.all():
            demo_data = reports.api_contentads.query(
                start_date=self.start_date,
                end_date=self.end_date,
                breakdown=['content_ad'],
                ad_group=d2r.demo_ad_group,
            )
            real_data = reports.api_contentads.query(
                self.start_date,
                self.end_date,
                ad_group=d2r.real_ad_group,
                breakdown=['content_ad'],
            )
            # Let us hope that distributive property also applies in ONE
            self.assertEqual(
                sum(ad['impressions'] for ad in demo_data),
                sum(ad['impressions'] for ad in real_data) * d2r.multiplication_factor,
            )
            self.assertEqual(
                sum(ad['clicks'] for ad in demo_data),
                sum(ad['clicks'] for ad in real_data) * d2r.multiplication_factor,
            )
        

        
class RefreshDemoTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml', 'test_demo.yaml']

    def setUp(self):
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
