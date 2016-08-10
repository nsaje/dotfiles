from mock import patch
import mock
from decimal import Decimal

import datetime
from collections import OrderedDict

from django import test
from django.contrib.auth import models as authmodels

from dash import export
from dash import models
from dash import constants
import reports.redshift as redshift
import reports.models as rm
from utils import test_helper

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
                'media_cost': 1000.12,
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
                'media_cost': 2000.12,
                'data_cost': 23.10,
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 2.03,
                'some_random_metric': 13,
                'source': 3
            }, {
                'ad_group': 3,
                'campaign': 3,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'media_cost': 3000.12,
                'data_cost': 33.10,
                'cpc': 30.23,
                'clicks': 303,
                'impressions': 300000,
                'ctr': 3.03,
                'some_random_metric': 14,
                'source': 3,
                'archived': True
            }
        ]

        redshift.STATS_DB_NAME = 'default'

        self.mock_generate_rows_stats = [{
            'ad_group': 1,
            'campaign': 1,
            'account': 1,
            'content_ad': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 1000.12,
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
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
            'source': 3
        }, {
            'ad_group': 1,
            'campaign': 1,
            'account': 1,
            'content_ad': 3,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 3000.12,
            'data_cost': 33.10,
            'cpc': 30.23,
            'clicks': 303,
            'impressions': 300000,
            'ctr': 3.03,
            'some_random_metric': 14,
            'source': 3
        }]

    def test_get_csv_content(self):
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('media_cost', 'Media Cost'),
            ('data_cost', 'Data Cost'),
            ('clicks', 'Clicks'),
            ('ctr', 'CTR'),
        ])

        content = export.get_csv_content(fieldnames, self.data)

        expected_content = '''Date,Media Cost,Data Cost,Clicks,CTR\r
2014-07-01,1000.12,10.10,103,0.0103\r
2014-07-01,2000.12,23.10,203,0.0203\r
2014-07-01,3000.12,33.10,303,0.0303\r
'''
        expected_content = test_helper.format_csv_content(expected_content)
        self.assertEqual(content, expected_content)

    def test_get_csv_content_with_statuses(self):
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('media_cost', 'Media Cost'),
            ('data_cost', 'Data Cost'),
            ('clicks', 'Clicks'),
            ('ctr', 'CTR'),
            ('status', 'Status')
        ])
        data = self.data
        data[0]['status'] = 1
        data[1]['status'] = 2
        data[2]['status'] = 2
        content = export.get_csv_content(fieldnames, self.data)

        expected_content = '''Date,Media Cost,Data Cost,Clicks,CTR,Status\r
2014-07-01,1000.12,10.10,103,0.0103,Active\r
2014-07-01,2000.12,23.10,203,0.0203,Inactive\r
2014-07-01,3000.12,33.10,303,0.0303,Archived\r
'''
        expected_content = test_helper.format_csv_content(expected_content)
        self.assertEqual(content, expected_content)

    @patch('dash.export._add_missing_stats')
    @patch('reports.api_contentads.query')
    def test_generate_rows(self, mock_query, mock_missing_stats):
        mock_query.return_value = self.mock_generate_rows_stats

        dimensions = ['ad_group', 'content_ad', 'source']
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

        self.assertEqual(1, mock_missing_stats.call_count)

        expectedRows = [{
            'account_id': 1,
            'campaign_id': 1,
            'ad_group_id': 1,
            'content_ad_id': 1,
            'uploaded': datetime.date(2015, 2, 21),
            'end_date': datetime.date(2014, 7, 2),
            'account': u'test account 1 \u010c\u017e\u0161',
            'content_ad': 1,
            'media_cost': 1000.12,
            'data_cost': 10.1,
            'ctr': 1.03,
            'campaign': u'test campaign 1 \u010c\u017e\u0161',
            'title': u'Test Article unicode \u010c\u017e\u0161',
            'url': u'http://testurl.com',
            'label': '',
            'cpc': 10.23,
            'start_date': datetime.date(2014, 6, 30),
            'source': u'Taboola',
            'ad_group': u'test adgroup 1 \u010c\u017e\u0161',
            'image_url': u'/123456789.jpg?w=200&h=300&fit=crop&crop=center&fm=jpg',
            'image_hash': u'987654321',
            'date': datetime.date(2014, 7, 1),
            'impressions': 100000,
            'clicks': 103,
            'status': 1,
            'archived': False
        }, {
            'account_id': 1,
            'campaign_id': 1,
            'ad_group_id': 1,
            'content_ad_id': 2,
            'uploaded': datetime.date(2015, 2, 21),
            'end_date': datetime.date(2014, 7, 2),
            'account': u'test account 1 \u010c\u017e\u0161',
            'content_ad': 2,
            'media_cost': 2000.12,
            'data_cost': 23.1,
            'ctr': 2.03,
            'campaign': u'test campaign 1 \u010c\u017e\u0161',
            'title': u'Test Article with no content_ad_sources 1',
            'url': u'http://testurl.com',
            'label': '',
            'cpc': 20.23,
            'start_date': datetime.date(2014, 6, 30),
            'source': u'Outbrain',
            'ad_group': u'test adgroup 1 \u010c\u017e\u0161',
            'image_url': u'/123456789.jpg?w=200&h=300&fit=crop&crop=center&fm=jpg',
            'image_hash': u'987654321',
            'date': datetime.date(2014, 7, 1),
            'impressions': 200000,
            'clicks': 203,
            'status': 2,
            'archived': False
        }, {
            'account_id': 1,
            'campaign_id': 1,
            'ad_group_id': 1,
            'content_ad_id': 3,
            'uploaded': datetime.date(2015, 2, 23),
            'end_date': datetime.date(2014, 7, 2),
            'account': u'test account 1 \u010c\u017e\u0161',
            'content_ad': 3,
            'media_cost': 3000.12,
            'data_cost': 33.1,
            'ctr': 3.03,
            'campaign': u'test campaign 1 \u010c\u017e\u0161',
            'title': u'Test Article with no content_ad_sources 2',
            'url': u'http://testurl.com',
            'label': '',
            'cpc': 30.23,
            'start_date': datetime.date(2014, 6, 30),
            'source': u'Outbrain',
            'ad_group': u'test adgroup 1 \u010c\u017e\u0161',
            'image_url': u'/123456789.jpg?w=200&h=300&fit=crop&crop=center&fm=jpg',
            'image_hash': u'987654321',
            'date': datetime.date(2014, 7, 1),
            'impressions': 300000,
            'clicks': 303,
            'status': 2,
            'archived': True
        }]
        self.assertEqual(rows, expectedRows)

    @patch('dash.export._add_missing_stats')
    @patch('reports.api_contentads.query')
    def test_generate_rows_flat_fees(self, mock_query, mock_missing_stats):
        mock_query.return_value = [{
            'account': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 1000.12,
            'data_cost': 10.10,
            'cpc': 10.23,
            'clicks': 103,
            'impressions': 100000,
            'license_fee': 1.0,
            'ctr': 1.03,
            'some_random_metric': 12,
        }, {
            'account': 2,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'license_fee': 1.0,
            'ctr': 2.03,
            'some_random_metric': 13,
        }]

        dimensions = ['account']
        start_date = datetime.date(2014, 6, 30)
        end_date = datetime.date(2014, 7, 2)
        user = User.objects.get(id=1)

        accounts = models.Account.objects.all()

        credit = models.CreditLineItem.objects.create(
            account_id=1,
            amount=1000,
            license_fee=Decimal('0.1000'),
            status=1,
            flat_fee_cc=1000000,
            start_date=datetime.date(2014, 6, 1),
            end_date=datetime.date(2014, 7, 31),
            flat_fee_start_date=datetime.date(2014, 6, 1),
            flat_fee_end_date=datetime.date(2014, 7, 31),
        )
        budget = models.BudgetLineItem.objects.create(
            campaign_id=1,
            amount=900,
            credit=credit,
            start_date=datetime.date(2014, 6, 1),
            end_date=datetime.date(2014, 7, 31),
        )
        rm.BudgetDailyStatement.objects.create(
            date=start_date,
            budget=budget,
            license_fee_nano=1 * 10**9,
            media_spend_nano=100 * 10**9,
            data_spend_nano=0,
            margin_nano=0,
        )

        rows = export._generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            'impressions',
            True,
            [],
            include_budgets=True,
            include_flat_fees=True,
            account=accounts
        )
        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=dimensions,
            order=[],
            conversion_goals=[],
            ignore_diff_rows=True,
            account=accounts,
        )

        self.assertEqual(1, mock_missing_stats.call_count)

        self.assertEqual(rows, [
            {'account_id': 1,
             'account': u'test account 1 \u010c\u017e\u0161',
             'clicks': 103,
             'media_cost': 1000.12,
             'cpc': 10.23,
             'ctr': 1.03,
             'data_cost': 10.1,
             'date': datetime.date(2014, 7, 1),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 100000,
             'start_date': datetime.date(2014, 6, 30),
             'license_fee': 1.0,
             'total_fee': Decimal('101.0000'),
             'flat_fee': Decimal('100.0000'),
             'status': 2,
             },
            {'account_id': 2,
             'account': u'test account 2',
             'clicks': 203,
             'media_cost': 2000.12,
             'cpc': 20.23,
             'ctr': 2.03,
             'data_cost': 23.1,
             'date': datetime.date(2014, 7, 1),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 200000,
             'start_date': datetime.date(2014, 6, 30),
             'license_fee': 1.0,
             'total_fee': 0,
             'flat_fee': 0,
             'status': 2,
             }
        ])

    @patch('dash.export._add_missing_stats')
    @patch('reports.api_contentads.query')
    @patch('dash.export._prefetch_projections')
    def test_generate_rows_budget(self, mock_proj, mock_query, mock_missing_stats):
        class Projection:

            def __init__(self):
                pass

            def row(self, i, *args):
                return {
                    1: 111,
                    2: 222,
                }[i]

        mock_proj.return_value = (
            Projection(),
            Projection(),
        )
        mock_query.return_value = [{
            'campaign': 1,
            'account': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 1000.12,
            'data_cost': 10.10,
            'cpc': 10.23,
            'clicks': 103,
            'impressions': 100000,
            'ctr': 1.03,
            'some_random_metric': 12,
        }, {
            'campaign': 1,
            'account': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
        }, {
            'campaign': 2,
            'account': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
        }]

        dimensions = ['campaign']
        start_date = datetime.date(2014, 6, 30)
        end_date = datetime.date(2014, 7, 2)
        user = User.objects.get(id=1)

        campaign1 = models.Campaign.objects.get(pk=1)
        campaign2 = models.Campaign.objects.get(pk=2)

        rows = export._generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            'impressions',
            True,
            [],
            include_projections=True,
            include_budgets=True,
        )
        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=dimensions,
            order=[],
            conversion_goals=[],
            ignore_diff_rows=True,
        )
        self.assertEqual(1, mock_missing_stats.call_count)
        self.maxDiff = None
        self.assertEqual(rows, [
            {'account_id': 1,
             'campaign_id': 1,
             'account': u'test account 1 \u010c\u017e\u0161',
             'campaign': campaign1,
             'clicks': 203,
             'media_cost': 2000.12,
             'cpc': 20.23,
             'ctr': 2.03,
             'data_cost': 23.1,
             'date': datetime.date(2014, 7, 1),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 200000,
             'start_date': datetime.date(2014, 6, 30),
             'status': 2,
             'allocated_budgets': 111,
             'spend_projection': 111,
             'license_fee_projection': 111,
             'pacing': 111,
             },
            {'account_id': 1,
             'campaign_id': 2,
             'account': u'test account 1 \u010c\u017e\u0161',
             'campaign': campaign2,
             'clicks': 203,
             'media_cost': 2000.12,
             'cpc': 20.23,
             'ctr': 2.03,
             'data_cost': 23.1,
             'date': datetime.date(2014, 7, 1),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 200000,
             'start_date': datetime.date(2014, 6, 30),
             'status': 2,
             'allocated_budgets': 222,
             'spend_projection': 222,
             'license_fee_projection': 222,
             'pacing': 222,
             }
        ])

    @patch('dash.export._add_missing_stats')
    @patch('reports.api_contentads.query')
    @patch('dash.export._prefetch_projections')
    def test_generate_rows_budget_breakdown_by_date(self, mock_proj, mock_query, mock_missing_stats):
        class Projection:

            def __init__(self):
                pass

            def row(self, i, *args):
                return {
                    1: 111,
                    2: 222,
                }[i]

        mock_proj.return_value = (
            Projection(),
            Projection(),
        )
        mock_query.return_value = [{
            'campaign': 1,
            'account': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 1000.12,
            'data_cost': 10.10,
            'cpc': 10.23,
            'clicks': 103,
            'impressions': 100000,
            'ctr': 1.03,
            'some_random_metric': 12,
        }, {
            'campaign': 1,
            'account': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
        }, {
            'campaign': 2,
            'account': 1,
            'date': datetime.date(2014, 7, 1),
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
        },
            {
            'campaign': 1,
            'account': 1,
            'date': datetime.date(2014, 7, 2),
            'media_cost': 1000.12,
            'data_cost': 10.10,
            'cpc': 10.23,
            'clicks': 103,
            'impressions': 100000,
            'ctr': 1.03,
            'some_random_metric': 12,
        }, {
            'campaign': 1,
            'account': 1,
            'date': datetime.date(2014, 7, 2),
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
        }, {
            'campaign': 2,
            'account': 1,
            'date': datetime.date(2014, 7, 2),
            'media_cost': 2000.12,
            'data_cost': 23.10,
            'cpc': 20.23,
            'clicks': 203,
            'impressions': 200000,
            'ctr': 2.03,
            'some_random_metric': 13,
        }]

        dimensions = ['campaign', 'date']
        start_date = datetime.date(2014, 6, 30)
        end_date = datetime.date(2014, 7, 2)
        user = User.objects.get(id=1)

        campaign1 = models.Campaign.objects.get(pk=1)
        campaign2 = models.Campaign.objects.get(pk=2)

        rows = export._generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            'impressions',
            True,
            [],
            include_projections=True,
            include_budgets=True,
        )
        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=dimensions,
            order=[],
            conversion_goals=[],
            ignore_diff_rows=True,
        )

        self.assertEqual(1, mock_missing_stats.call_count)

        self.assertEqual(rows, [
            {'account_id': 1,
             'campaign_id': 1,
             'account': u'test account 1 \u010c\u017e\u0161',
             'campaign': campaign1,
             'clicks': 203,
             'media_cost': 2000.12,
             'cpc': 20.23,
             'ctr': 2.03,
             'data_cost': 23.1,
             'date': datetime.date(2014, 7, 1),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 200000,
             'start_date': datetime.date(2014, 6, 30),
             'status': 2,
             'allocated_budgets': 111,
             'spend_projection': 111,
             'license_fee_projection': 111,
             'pacing': 111,
             },
            {'account_id': 1,
             'campaign_id': 2,
             'account': u'test account 1 \u010c\u017e\u0161',
             'campaign': campaign2,
             'clicks': 203,
             'media_cost': 2000.12,
             'cpc': 20.23,
             'ctr': 2.03,
             'data_cost': 23.1,
             'date': datetime.date(2014, 7, 1),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 200000,
             'start_date': datetime.date(2014, 6, 30),
             'status': 2,
             'allocated_budgets': 222,
             'spend_projection': 222,
             'license_fee_projection': 222,
             'pacing': 222,
             },
            {'account_id': 1,
             'campaign_id': 1,
             'account': u'test account 1 \u010c\u017e\u0161',
             'campaign': campaign1,
             'clicks': 203,
             'media_cost': 2000.12,
             'cpc': 20.23,
             'ctr': 2.03,
             'data_cost': 23.1,
             'date': datetime.date(2014, 7, 2),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 200000,
             'start_date': datetime.date(2014, 6, 30),
             'status': 2,
             'allocated_budgets': Decimal(0),
             'spend_projection': Decimal(0),
             'license_fee_projection': Decimal(0),
             'pacing': Decimal(0),
             },
            {'account_id': 1,
             'campaign_id': 2,
             'account': u'test account 1 \u010c\u017e\u0161',
             'campaign': campaign2,
             'clicks': 203,
             'media_cost': 2000.12,
             'cpc': 20.23,
             'ctr': 2.03,
             'data_cost': 23.1,
             'date': datetime.date(2014, 7, 2),
             'end_date': datetime.date(2014, 7, 2),
             'impressions': 200000,
             'start_date': datetime.date(2014, 6, 30),
             'status': 2,
             'allocated_budgets': Decimal(0),
             'spend_projection': Decimal(0),
             'license_fee_projection': Decimal(0),
             'pacing': Decimal(0),
             }
        ])

    @patch('dash.export._add_missing_stats')
    @patch('reports.api_contentads.query')
    def test_generate_rows_order_by_status(self, mock_query, mock_missing_stats):
        mock_query.return_value = self.mock_generate_rows_stats

        dimensions = ['ad_group', 'content_ad', 'source']
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
            '-status',
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
        self.assertEqual(1, mock_missing_stats.call_count)
        self.assertEqual(rows[0].get('status'), constants.ExportStatus.INACTIVE)
        self.assertEqual(rows[1].get('status'), constants.ExportStatus.INACTIVE)
        self.assertEqual(rows[2].get('status'), constants.ExportStatus.ACTIVE)

    def test_get_report_filename(self):
        self.assertEqual(
            'acc_camp_adg_-_by_content_ad_media_source_report_2014-06-03_2014-06-10',
            export._get_report_filename(
                constants.ScheduledReportGranularity.CONTENT_AD,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc',
                campaign_name='camp',
                ad_group_name='adg',
                by_source=True))

        self.assertEqual(
            'acc_camp_adg_-_by_content_ad_by_day_report_2014-06-03_2014-06-10',
            export._get_report_filename(
                constants.ScheduledReportGranularity.CONTENT_AD,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc',
                campaign_name='camp',
                ad_group_name='adg',
                by_day=True))

        self.assertEqual(
            'acc_camp_-_by_ad_group_report_2014-06-03_2014-06-10',
            export._get_report_filename(
                constants.ScheduledReportGranularity.AD_GROUP,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc',
                campaign_name='camp'))

        self.assertEqual(
            'ZemantaOne_media_source_report_2014-06-03_2014-06-10',
            export._get_report_filename(
                constants.ScheduledReportGranularity.ALL_ACCOUNTS,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                by_source=True))

        self.assertEqual(
            'acc_-_by_campaign_report_2014-06-03_2014-06-10',
            export._get_report_filename(
                constants.ScheduledReportGranularity.CAMPAIGN,
                datetime.date(2014, 6, 3),
                datetime.date(2014, 6, 10),
                account_name='acc'))

    @mock.patch('dash.export.AdGroupAdsExport.get_data')
    def test_get_report_contents_ad_group(self, get_data_mock):
        report_contents = export._get_report_contents(
            User.objects.get(pk=1),
            [],
            None,
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
            include_model_ids=False,
            user=User.objects.get(pk=1),
            order='name'
        )

    @mock.patch('dash.export.CampaignExport.get_data')
    def test_get_report_contents_campaign(self, get_data_mock):
        report_contents = export._get_report_contents(
            User.objects.get(pk=1),
            [],
            None,
            datetime.date(2014, 6, 3),
            datetime.date(2014, 6, 10),
            'media_cost',
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
            include_model_ids=False,
            order='media_cost'
        )

    @mock.patch('dash.export._get_report')
    def test_get_report_from_export_report(self, mock_get_report):
        export_report = models.ExportReport.objects.get(id=1)
        contents = export.get_report_from_export_report(
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
            include_model_ids=False,
            ad_group=None,
            granularity=2,
            order=None)

    def test_add_missing_stats(self):
        stats = list(self.mock_generate_rows_stats)
        export._add_missing_stats(stats, [], None, None, None, None)
        self.assertEqual(self.mock_generate_rows_stats, stats)

    def test_add_missing_stats_content_ad(self):
        stats = list(self.mock_generate_rows_stats)
        data = {obj.id: obj for obj in models.ContentAd.objects.all()}
        sources = {obj.ad_group_id: [1, 2] for obj in data.itervalues()}
        export._add_missing_stats(stats, ['content_ad', 'date', 'source'], data, sources,
                                  datetime.date(2014, 7, 1), datetime.date(2014, 7, 5))
        self.assertEqual(43, len(stats))
        self.assertEqual({
            'account': 1,
            'ad_group': 2,
            'campaign': 2,
            'content_ad': 5,
            'date': datetime.date(2014, 7, 4),
            'source': 2
        }, stats[len(stats) - 1])

    def test_add_missing_stats_ad_group(self):
        stats = list(self.mock_generate_rows_stats)
        data = {obj.id: obj for obj in models.AdGroup.objects.all()}
        sources = {id: [1, 2] for id in data}
        export._add_missing_stats(stats, ['ad_group', 'date', 'source'], data, sources,
                                  datetime.date(2014, 7, 1), datetime.date(2014, 7, 5))
        self.assertEqual(83, len(stats))
        self.assertEqual({
            'account': 1,
            'ad_group': 10,
            'campaign': 1,
            'date': datetime.date(2014, 7, 4),
            'source': 2
        }, stats[len(stats) - 1])

    def test_add_missing_stats_campaign(self):
        stats = list(self.mock_generate_rows_stats)
        data = {obj.id: obj for obj in models.Campaign.objects.all()}
        sources = {id: [1, 2] for id in data}
        export._add_missing_stats(stats, ['campaign', 'date', 'source'], data, sources,
                                  datetime.date(2014, 7, 1), datetime.date(2014, 7, 5))
        self.assertEqual(51, len(stats))
        self.assertEqual({
            'account': 4,
            'campaign': 6,
            'date': datetime.date(2014, 7, 4),
            'source': 2
        }, stats[len(stats) - 1])

    def test_add_missing_stats_account(self):
        stats = list(self.mock_generate_rows_stats)
        data = {obj.id: obj for obj in models.Account.objects.all()}
        sources = {id: [1, 2] for id in data}
        export._add_missing_stats(stats, ['account', 'date', 'source'], data, sources,
                                  datetime.date(2014, 7, 1), datetime.date(2014, 7, 5))
        self.assertEqual(35, len(stats))
        self.assertEqual({
            'account': 4,
            'date': datetime.date(2014, 7, 4),
            'source': 2
        }, stats[len(stats) - 1])


class FilterAllowedFieldsTestCase(test.TestCase):
    fixtures = ['test_api']

    def test_filter_margin(self):
        user = User.objects.get(id=2)

        allowed = export.filter_allowed_fields(user, ['margin', 'agency_total'])
        self.assertEqual([], allowed)

        user.user_permissions.add(authmodels.Permission.objects.get(codename='can_view_agency_margin'))
        user = User.objects.get(id=2)

        allowed = export.filter_allowed_fields(user, ['margin', 'agency_total'])
        self.assertEqual(['margin', 'agency_total'], allowed)
