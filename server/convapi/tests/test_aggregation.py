import datetime

from django.test import TestCase

import convapi.parse
import convapi.models
import reports.api
import reports.models


class GAReportsAggregationTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

    def setUp(self):
        self.csvreport = convapi.parse.CsvReport(open('convapi/fixtures/ga_report_20140901.csv').read())
        self.report_date = datetime.date(2014, 9, 1)
        self.remail = convapi.models.ReportEmail(
            sender='some sender',
            recipient='some recipient',
            subject='some subject',
            text='some text',
            date='some date',
            report=self.csvreport
        )

    def test_report_aggregation(self):
        self.assertEqual(reports.models.ArticleStats.objects.filter(datetime=self.report_date).count(), 1)

        self.assertTrue(self.remail.is_ad_group_consistent())
        self.assertTrue(self.remail.is_media_source_specified())
        self.assertEqual(self.remail.report.get_date(), self.report_date)
        self.assertEqual(len(self.remail.report.get_entries()), 7)
        self.assertEqual(self.remail.report.get_fieldnames(), [
                'Landing Page', 'Device Category', 'Sessions', '% New Sessions', 'New Users',
                'Bounce Rate', 'Pages / Session', 'Avg. Session Duration',
                'Buy Beer (Goal 1 Conversion Rate)', 'Buy Beer (Goal 1 Completions)',
                'Buy Beer (Goal 1 Value)', 'Get Drunk (Goal 2 Conversion Rate)', 
                'Get Drunk (Goal 2 Completions)', 'Get Drunk (Goal 2 Value)'
            ])
        self.assertEqual(sum(int(entry['Sessions']) for entry in self.remail.report.get_entries()), 520)

        self.remail.save_raw()

        self.assertEqual(convapi.models.RawPostclickStats.objects.count(), 7)
        self.assertEqual(convapi.models.RawGoalConversionStats.objects.count(), 14)
        self.assertEqual(convapi.models.RawGoalConversionStats.objects.filter(goal_name='Buy Beer (Goal 1)').count(), 7)
        self.assertEqual(convapi.models.RawGoalConversionStats.objects.filter(goal_name='Get Drunk (Goal 2)').count(), 7)
        self.assertEqual(convapi.models.RawPostclickStats.objects.filter(device_type='mobile').count(), 2)

        self.remail.aggregate()

        self.assertEqual(reports.models.ArticleStats.objects.count(), 4)
        self.assertEqual(reports.models.GoalConversionStats.objects.count(), 8)

        result = reports.api.query(self.report_date, self.report_date, ad_group=1)

        self.assertEqual(result['visits'], 520)
        self.assertEqual(result['clicks'], 21)
        self.assertTrue('goals' in result)
        self.assertEqual(result['goals']['Buy Beer (Goal 1)']['conversions'], 54)

        result_by_source = reports.api.query(self.report_date, self.report_date, ['source'], ad_group=1)
        self.assertEqual(len(result_by_source), 3)
