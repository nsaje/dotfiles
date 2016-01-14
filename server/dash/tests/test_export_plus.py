from mock import patch
import mock

import datetime
from collections import OrderedDict

from django import test

from dash import export_plus
from dash import models
from dash import constants
import reports.redshift as redshift

from zemauth.models import User


class ExportPlusTestCase(test.TestCase):
    fixtures = ['test_api']

    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)

    def setUp(self):
        self.data = [
            {
                'ad_group': 1,
                'campaign': 1,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'data_cost': 10.10,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12,
                'source': 4
            }, {
                'ad_group': 2,
                'campaign': 2,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 2000.12,
                'data_cost': 23.10,
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 2.03,
                'some_random_metric': 13,
                'source': 3
            }
        ]

        redshift.STATS_DB_NAME = 'default'

        self.mock_generate_rows_stats = [{
            'ad_group': 1,
            'campaign': 1,
            'account': 1,
            'content_ad': 1,
            'date': datetime.date(2014, 7, 1),
            'cost': 1000.12,
            'data_cost': 10.10,
            'cpc': 10.23,
            'clicks': 103,
            'impressions': 100000,
            'ctr': 1.03,
            'some_random_metric': 12,
            'source': 4
        }, {
            'ad_group': 1,
            'campaign': 1,
            'account': 1,
            'content_ad': 2,
            'date': datetime.date(2014, 7, 1),
            'cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
            'source': 3
        }]

    def test_get_csv_content(self):
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('cost', 'Cost'),
            ('data_cost', 'Data Cost'),
            ('clicks', 'Clicks'),
            ('ctr', 'CTR')
        ])

        content = export_plus.get_csv_content(fieldnames, self.data)

        expected_content = '''Date,Cost,Data Cost,Clicks,CTR\r
2014-07-01,1000.12,10.10,103,0.0103\r
2014-07-01,2000.12,23.10,203,0.0203\r
'''
        self.assertEqual(content, expected_content)

    def test_get_csv_content_with_statuses(self):
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('cost', 'Cost'),
            ('data_cost', 'Data Cost'),
            ('clicks', 'Clicks'),
            ('ctr', 'CTR'),
            ('status', 'Status')
        ])
        data = self.data
        data[0]['status'] = 1
        data[1]['status'] = 2
        content = export_plus.get_csv_content(fieldnames, self.data)

        expected_content = '''Date,Cost,Data Cost,Clicks,CTR,Status\r
2014-07-01,1000.12,10.10,103,0.0103,Active\r
2014-07-01,2000.12,23.10,203,0.0203,Inactive\r
'''
        self.assertEqual(content, expected_content)

    @patch('reports.api_contentads.query')
    def test_generate_rows(self, mock_query):
        mock_query.return_value = self.mock_generate_rows_stats

        dimensions = ['ad_group', 'content_ad', 'source']
        start_date = datetime.date(2014, 6, 30)
        end_date = datetime.date(2014, 7, 2)
        user = User.objects.get(id=1)

        sources = models.Source.objects.all()

        ad_group = models.AdGroup.objects.get(pk=1)

        rows = export_plus._generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            'impressions',
            True,
            [],
            source=sources,
            ad_group=ad_group
        )

        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=dimensions,
            order=[],
            conversion_goals=[],
            ignore_diff_rows=True,
            **{
                'source': sources,
                'ad_group': ad_group
            }
        )

        self.assertEqual(rows, [{
            'uploaded': datetime.date(2015, 2, 21),
            'end_date': datetime.date(2014, 7, 2),
            'account': u'test account 1 \u010c\u017e\u0161',
            'content_ad': 1,
            'cost': 1000.12,
            'data_cost': 10.1,
            'ctr': 1.03,
            'campaign': u'test campaign 1 \u010c\u017e\u0161',
            'title': u'Test Article unicode \u010c\u017e\u0161',
            'url': u'http://testurl.com',
            'cpc': 10.23,
            'start_date': datetime.date(2014, 6, 30),
            'source': u'Taboola',
            'ad_group': u'test adgroup 1 \u010c\u017e\u0161',
            'image_url': u'/123456789/200x300.jpg',
            'date': datetime.date(2014, 7, 1),
            'impressions': 100000,
            'clicks': 103,
            'status': 1,
        }, {
            'uploaded': datetime.date(2015, 2, 21),
            'end_date': datetime.date(2014, 7, 2),
            'account': u'test account 1 \u010c\u017e\u0161',
            'content_ad': 2,
            'cost': 2000.12,
            'data_cost': 23.1,
            'ctr': 2.03,
            'campaign': u'test campaign 1 \u010c\u017e\u0161',
            'title': u'Test Article with no content_ad_sources 1',
            'url': u'http://testurl.com',
            'cpc': 20.23,
            'start_date': datetime.date(2014, 6, 30),
            'source': u'Outbrain',
            'ad_group': u'test adgroup 1 \u010c\u017e\u0161',
            'image_url': u'/123456789/200x300.jpg',
            'date': datetime.date(2014, 7, 1),
            'impressions': 200000,
            'clicks': 203,
            'status': 2
        }])

    @patch('reports.api_contentads.query')
    def test_generate_rows_order_by_status(self, mock_query):
        mock_query.return_value = self.mock_generate_rows_stats

        dimensions = ['ad_group', 'content_ad', 'source']
        start_date = datetime.date(2014, 6, 30)
        end_date = datetime.date(2014, 7, 2)
        user = User.objects.get(id=1)

        sources = models.Source.objects.all()

        ad_group = models.AdGroup.objects.get(pk=1)

        rows = export_plus._generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            '-status',
            True,
            [],
            include_statuses=True,
            source=sources,
            ad_group=ad_group
        )

        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=dimensions,
            order=[],
            conversion_goals=[],
            ignore_diff_rows=True,
            **{
                'source': sources,
                'ad_group': ad_group
            }
        )
        self.assertEqual(rows[0].get('status'), constants.AdGroupSourceSettingsState.INACTIVE)
        self.assertEqual(rows[1].get('status'), constants.AdGroupSourceSettingsState.ACTIVE)

    def test_get_report_filename(self):
        self.assertEqual(
            'acc_camp_adg_-_by_content_ad_media_source_report_2014-06-03_2014-06-10',
            export_plus._get_report_filename(
                constants.ScheduledReportGranularity.CONTENT_AD,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc',
                campaign_name='camp',
                ad_group_name='adg',
                by_source=True))

        self.assertEqual(
            'acc_camp_adg_-_by_content_ad_by_day_report_2014-06-03_2014-06-10',
            export_plus._get_report_filename(
                constants.ScheduledReportGranularity.CONTENT_AD,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc',
                campaign_name='camp',
                ad_group_name='adg',
                by_day=True))

        self.assertEqual(
            'acc_camp_-_by_ad_group_report_2014-06-03_2014-06-10',
            export_plus._get_report_filename(
                constants.ScheduledReportGranularity.AD_GROUP,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc',
                campaign_name='camp'))

        self.assertEqual(
            'ZemantaOne_media_source_report_2014-06-03_2014-06-10',
            export_plus._get_report_filename(
                constants.ScheduledReportGranularity.ALL_ACCOUNTS,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                by_source=True))

        self.assertEqual(
            'acc_-_by_campaign_report_2014-06-03_2014-06-10',
            export_plus._get_report_filename(
                constants.ScheduledReportGranularity.CAMPAIGN,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc'))

    @mock.patch('dash.export_plus.AdGroupExport.get_data')
    def test_get_report_contents_ad_group(self, get_data_mock):
        report_contents = export_plus._get_report_contents(
            User.objects.get(pk=1),
            [],
            datetime.date(2014, 6, 3),
            datetime.date(2014, 6, 10),
            'name',
            ['aa', 'bb'],
            ['ad_group', 'date'],
            False,
            True,
            ad_group_id=1)

        get_data_mock.assert_called_with(
            additional_fields=['aa', 'bb'],
            breakdown=['ad_group', 'date'],
            filtered_sources=[],
            ad_group_id=1,
            end_date=datetime.date(2014, 6, 10),
            by_day=True,
            start_date=datetime.date(2014, 6, 3),
            by_source=False,
            user=User.objects.get(pk=1),
            order='name'
        )

    @mock.patch('dash.export_plus.CampaignExport.get_data')
    def test_get_report_contents_campaign(self, get_data_mock):
        report_contents = export_plus._get_report_contents(
            User.objects.get(pk=1),
            [],
            datetime.date(2014, 6, 3),
            datetime.date(2014, 6, 10),
            'cost',
            [],
            ['campaign', 'source'],
            True,
            False,
            campaign_id=1)

        get_data_mock.assert_called_with(
            additional_fields=[],
            breakdown=['campaign', 'source'],
            filtered_sources=[],
            end_date=datetime.date(2014, 6, 10),
            by_day=False, campaign_id=1,
            start_date=datetime.date(2014, 6, 3),
            by_source=True, user=User.objects.get(pk=1),
            order='cost'
        )

    @mock.patch('dash.export_plus._get_report')
    def test_get_report_from_export_report(self, mock_get_report):
        export_report = models.ExportReport.objects.get(id=1)
        contents = export_plus.get_report_from_export_report(
            export_report,
            datetime.date(2014, 6, 3),
            datetime.date(2014, 6, 10))

        mock_get_report.assert_called_with(
            User.objects.get(pk=1),
            datetime.date(2014, 6, 3),
            datetime.date(2014, 6, 10),
            breakdown='account',
            additional_fields=[],
            account=models.Account.objects.get(id=1),
            campaign=None,
            by_day=False,
            filtered_sources=mock.ANY,
            by_source=False,
            ad_group=None,
            granularity=2,
            order=None)
