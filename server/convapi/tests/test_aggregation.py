import datetime

from django.test import TestCase
from mock import patch, MagicMock

import convapi.parse
import convapi.models
import convapi.aggregate
import convapi.views
import reports.api
import reports.models
from reports import redshift


class GAReportsAggregationTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

    def setUp(self):
        self.report_log = convapi.models.GAReportLog()
        self.csvreport = convapi.parse.CsvReport(open('convapi/fixtures/ga_report_20140901.csv').read(), self.report_log)
        self.csvreport_errors = convapi.parse.CsvReport(open('convapi/fixtures/errors_ga_report_20140901.csv').read(), self.report_log)
        self.report_date = datetime.date(2014, 9, 1)
        self.remail = convapi.aggregate.ReportEmail(
            sender='some sender',
            recipient='some recipient',
            subject='some subject',
            text='some text',
            date='some date',
            report=self.csvreport,
            report_log=self.report_log
        )

        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)
        redshift.STATS_DB_NAME = 'default'

    def test_is_ad_group_specified(self):
        self.assertEqual((False, ['/lasko?_z1_a&_z1_msid=yahoo.com&_z1_kid=beer']),
                         self.csvreport_errors.is_ad_group_specified())

    def test_is_media_source_specified(self):
        self.assertEqual((False, ['/lasko?_z1_adgid=1&_z1_msid=', '/lasko?_z1_adgid=1&_z1_msid=', '/union?_z1_adgid=1&_z1_msid=']),
                         self.csvreport_errors.is_media_source_specified())

    def test_too_many_errors(self):
        self.assertFalse(convapi.views.too_many_errors(['error-url.com', 'error-url1.com']))
        self.assertTrue(convapi.views.too_many_errors(['error-url.com', 'error-url1.com1', 'error-url2.com']))

    def test_ad_group_specified_errors(self):
        self.assertEqual(['/lasko?_z1_a&_z1_msid=yahoo.com&_z1_kid=beer'],
                         convapi.views.ad_group_specified_errors(self.csvreport_errors))

    def test_media_source_specified_errors(self):
        self.assertEqual(['/lasko?_z1_adgid=1&_z1_msid=', '/lasko?_z1_adgid=1&_z1_msid=', '/union?_z1_adgid=1&_z1_msid='],
                         convapi.views.media_source_specified_errors(self.csvreport_errors))

    @patch('reports.refresh.notify_contentadstats_change', MagicMock())
    def test_report_aggregation(self):
        self.assertEqual(reports.models.ArticleStats.objects.filter(datetime=self.report_date).count(), 1)

        self.assertEqual((True, []), self.csvreport.is_ad_group_specified())
        self.assertEqual((True, []), self.csvreport.is_media_source_specified())
        self.assertEqual(self.remail.report.get_date(), self.report_date)
        self.assertEqual(len(self.remail.report.get_entries()), 7)
        self.assertEqual(self.remail.report.get_fieldnames(), [
                'Landing Page', 'Device Category', 'Sessions', '% New Sessions', 'New Users',
                'Bounce Rate', 'Pages / Session', 'Avg. Session Duration',
                'Buy Beer (Goal 1 Conversion Rate)', 'Buy Beer (Goal 1 Completions)',
                'Buy Beer (Goal 1 Value)', 'Get Drunk (Goal 2 Conversion Rate)',
                'Get Drunk (Goal 2 Completions)', 'Get Drunk (Goal 2 Value)'
            ])
        self.assertEqual(sum(int(entry['Sessions'].replace(',', '')) for entry in self.remail.report.get_entries()), 520)

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
        self.assertEqual(result['pv_per_visit'], 2.2)
        self.assertEqual(result['bounce_rate'], 50.0)
        self.assertEqual(round(result['percent_new_users'], 4), 74.8077)
        self.assertEqual(result['pageviews'], 1144)
        self.assertEqual(round(result['avg_tos'], 4), 40.6154)

        result_by_source = reports.api.query(self.report_date, self.report_date, ['source'], ad_group=1)
        self.assertEqual(len(result_by_source), 3)


class GAReportsAggregationKeywordTest(TestCase):

    fixtures = ['test_ga_aggregation.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)


    def test_report_init(self):
        report_log = convapi.models.GAReportLog()

        csv_file = open('convapi/fixtures/ga_report_keyword_20140901.csv').read()
        csvreport = convapi.parse.CsvReport(csv_file, report_log)

        self.assertEqual(csvreport.first_col, convapi.parse.KEYWORD_COL_NAME)

        self.assertEqual((True, []), csvreport.is_ad_group_specified())
        self.assertEqual((True, []), csvreport.is_media_source_specified())

    def test_report_init_error(self):
        report_log = convapi.models.GAReportLog()

        csv_file = open('convapi/fixtures/errors_ga_report_keyword_20140901.csv').read()
        csvreport = convapi.parse.CsvReport(csv_file, report_log)

        self.assertEqual(csvreport.first_col, convapi.parse.KEYWORD_COL_NAME)

        self.assertEqual((False, ['z1yahoo.com1z']), csvreport.is_ad_group_specified())
        self.assertEqual((False, ['z111z']), csvreport.is_media_source_specified())

    @patch('reports.refresh.notify_contentadstats_change', MagicMock())
    def test_report_aggregation(self):
        report_log = convapi.models.GAReportLog()

        csv_file = open('convapi/fixtures/ga_report_keyword_full_20140901.csv').read()
        csvreport = convapi.parse.CsvReport(csv_file, report_log)

        report_date = datetime.date(2014, 9, 1)
        remail = convapi.aggregate.ReportEmail(
            sender='some sender',
            recipient='some recipient',
            subject='some subject',
            text='some text',
            date='some date',
            report=csvreport,
            report_log=report_log
        )

        self.assertEqual(reports.models.ArticleStats.objects.filter(datetime=report_date).count(), 1)

        self.assertEqual((True, []), csvreport.is_ad_group_specified())
        self.assertEqual((True, []), csvreport.is_media_source_specified())
        self.assertEqual(remail.report.get_date(), report_date)
        self.assertEqual(len(remail.report.get_entries()), 7)
        self.assertEqual(remail.report.get_fieldnames(), [
                'Keyword', 'Device Category', 'Sessions', '% New Sessions', 'New Users',
                'Bounce Rate', 'Pages / Session', 'Avg. Session Duration',
                'Buy Beer (Goal 1 Conversion Rate)', 'Buy Beer (Goal 1 Completions)',
                'Buy Beer (Goal 1 Value)', 'Get Drunk (Goal 2 Conversion Rate)',
                'Get Drunk (Goal 2 Completions)', 'Get Drunk (Goal 2 Value)'
            ])
        self.assertEqual(sum(int(entry['Sessions'].replace(',', '')) for entry in remail.report.get_entries()), 520)

        remail.save_raw()

        self.assertEqual(convapi.models.RawPostclickStats.objects.count(), 7)
        self.assertEqual(convapi.models.RawGoalConversionStats.objects.count(), 14)
        self.assertEqual(convapi.models.RawGoalConversionStats.objects.filter(goal_name='Buy Beer (Goal 1)').count(), 7)
        self.assertEqual(convapi.models.RawGoalConversionStats.objects.filter(goal_name='Get Drunk (Goal 2)').count(), 7)
        self.assertEqual(convapi.models.RawPostclickStats.objects.filter(device_type='mobile').count(), 2)

        remail.aggregate()

        self.assertTrue(reports.models.ArticleStats.objects.count() >= 3)
        self.assertTrue(reports.models.ArticleStats.objects.count() <= 4)
        self.assertTrue(reports.models.GoalConversionStats.objects.count() == 6 or
                        reports.models.GoalConversionStats.objects.count() == 8)

        result = reports.api.query(report_date, report_date, ad_group=1)

        self.assertEqual(result['visits'], 520)
        self.assertEqual(result['clicks'], 21)
        self.assertTrue('goals' in result)
        self.assertEqual(result['goals']['Buy Beer (Goal 1)']['conversions'], 54)
        self.assertEqual(result['pv_per_visit'], 2.2)
        self.assertEqual(result['bounce_rate'], 50.0)
        self.assertEqual(round(result['percent_new_users'], 4), 74.8077)
        self.assertEqual(result['pageviews'], 1144)
        self.assertEqual(round(result['avg_tos'], 4), 40.6154)

        result_by_source = reports.api.query(report_date, report_date, ['source'], ad_group=1)
        self.assertEqual(len(result_by_source), 3)
