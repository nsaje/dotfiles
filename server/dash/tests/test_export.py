from mock import patch

import datetime
from collections import OrderedDict

from django import test
import xlrd

from dash import export
from dash import models
import reports.redshift as redshift

from utils.test_helper import QuerySetMatcher

from zemauth.models import User


class ExportTestCase(test.TestCase):
    fixtures=['test_api']

    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)

    def setUp(self):
        self.data = [
            {
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'data_cost': 11.12,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12
            },
            {
                'date': datetime.date(2014, 7, 1),
                'cost': 1034.12,
                'data_cost': 13.44,
                'clicks': 133,
                'impressions': 100308,
                'ctr': 1.04,
                'some_random_metric': 14
            }
        ]

        redshift.STATS_DB_NAME = 'default'

    def test_get_csv_content(self):
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('cost', 'Cost'),
            ('data_cost', 'Data Cost'),
            ('clicks', 'Clicks'),
            ('ctr', 'CTR')
        ])

        content = export.get_csv_content(fieldnames, self.data)

        expected_content = 'Date,Cost,Data Cost,Clicks,CTR\r\n2014-07-01,1000.12,11.12,103,1.03\r\n2014-07-01,1034.12,13.44,133,1.04\r\n'

        self.assertEqual(content, expected_content)

    def test_get_excel_content(self):
        columns = [
            {'key': 'date', 'name': 'Date', 'format': 'date'},
            {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
            {'key': 'data_cost', 'name': 'Data Cost', 'format': 'currency'},
            {'key': 'clicks', 'name': 'Clicks'},
            {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
        ]

        content = export.get_excel_content([('Test Report', columns, self.data)])

        workbook = xlrd.open_workbook(file_contents=content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Test Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Cost', 'Data Cost', 'Clicks', 'CTR'])
        self._assert_row(worksheet, 1, [41821.0, 1000.12, 11.12, 103, 0.0103])

    @patch('dash.export.reports.api.query')
    def test_generate_rows(self, mock_query):
        mock_stats = [{
            'date': datetime.date(2015, 2, 1),
            'cpc': '0.0200',
            'clicks': 1500,
            'source': 1
        }]

        mock_query.return_value = mock_stats

        dimensions = ['date', 'article']
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        user = User.objects.get(pk=1)

        source = models.Source(id=1)

        rows = export.generate_rows(dimensions, start_date, end_date, user, source=source)

        mock_query.assert_called_with(
            start_date,
            end_date,
            dimensions,
            ['date'],
            ignore_diff_rows=False,
            source=source
        )

        self.assertEqual(rows, mock_stats)

    @patch('dash.export.reports.api.query')
    def test_generate_redshift_rows(self, mock_query):
        mock_stats = [{
            'date': datetime.date(2015, 2, 1),
            'cpc': '0.0200',
            'clicks': 1500,
            'source': 1
        }]

        mock_query.return_value = mock_stats

        dimensions = ['date', 'article']
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        user = User.objects.get(pk=2)

        source = models.Source(id=1)

        rows = export.generate_rows(dimensions, start_date, end_date, user, source=source)

        mock_query.assert_called_with(
            start_date,
            end_date,
            dimensions,
            ['date'],
            ignore_diff_rows=False,
            source=source
        )

        self.assertEqual(rows, mock_stats)

    @patch('dash.export.reports.api_contentads.query')
    def test_generate_rows_content_ad(self, mock_query):
        mock_stats = [{
            'date': datetime.date(2015, 2, 1),
            'cpc': '0.0200',
            'clicks': 1500,
            'source': 1,
            'content_ad': 1,
            'ad_group': 1
        }]

        mock_query.return_value = mock_stats

        dimensions = ['date', 'ad_group', 'content_ad']
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)
        user = User.objects.get(id=1)

        sources = models.Source.objects.all()
        sources_matcher = QuerySetMatcher(sources)

        campaign = models.Campaign.objects.get(pk=1)

        rows = export.generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            ignore_diff_rows=True,
            source=sources,
            campaign=campaign
        )

        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=dimensions,
            order=[],
            conversion_goals=[],
            ignore_diff_rows=True,
            **{
                'source': sources_matcher,
                'campaign': campaign
            }
        )

        self.assertEqual(rows, [{
            'ad_group': 1,
            'clicks': 1500,
            'content_ad': 1,
            'cpc': '0.0200',
            'date': datetime.date(2015, 2, 1),
            'image_url': u'/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg',
            'source': 1,
            'title': u'Test Article unicode \u010c\u017e\u0161',
            'uploaded': datetime.date(2015, 2, 21),
            'url': u'http://testurl.com'
        }])
