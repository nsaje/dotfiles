from mock import patch

import datetime
from collections import OrderedDict

from django import test

from dash import export
from dash import models
import reports.redshift as redshift

from zemauth.models import User


class ExportTestCase(test.TestCase):
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
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 2.03,
                'some_random_metric': 13,
                'source': 3
            }
        ]

        redshift.STATS_DB_NAME = 'default'

    def test_get_csv_content(self):
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('cost', 'Cost'),
            ('clicks', 'Clicks'),
            ('ctr', 'CTR')
        ])

        content = export.get_csv_content(fieldnames, self.data)

        expected_content = 'Date,Cost,Clicks,CTR\r\n2014-07-01,1000.12,103,1.03\r\n2014-07-01,2000.12,203,2.03\r\n'

        self.assertEqual(content, expected_content)

    @patch('dash.export.reports.api_contentads.query')
    def test_generate_rows(self, mock_query):
        mock_stats = [{
            'ad_group': 1,
            'campaign': 1,
            'account': 1,
            'content_ad': 1,
            'date': datetime.date(2014, 7, 1),
            'cost': 1000.12,
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
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
            'source': 3
        }]

        mock_query.return_value = mock_stats

        dimensions = ['ad_group', 'content_ad']
        start_date = datetime.date(2014, 6, 30)
        end_date = datetime.date(2014, 7, 2)
        user = User.objects.get(id=1)

        sources = models.Source.objects.all()

        ad_group = models.AdGroup.objects.get(pk=1)

        rows = export._generate_rows(
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
            'clicks': 103
        }, {
            'uploaded': datetime.date(2015, 2, 21),
            'end_date': datetime.date(2014, 7, 2),
            'account': u'test account 1 \u010c\u017e\u0161',
            'content_ad': 2,
            'cost': 2000.12,
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
            'clicks': 203
        }])
