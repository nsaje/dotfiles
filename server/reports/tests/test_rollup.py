import datetime

from django import test
from mock import patch

from dash import models as dashmodels
from reports import api
from reports import refresh


class RollupTestCase(test.TestCase):
    fixtures = ['test_reports_rollup.yaml', 'test_article_stats_rollup.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

        self.start_date = datetime.date(2014,8,1)
        self.end_date = datetime.date(2014, 8, 3)
        refresh.refresh_adgroup_stats()

    def test_by_adgroup_for_campaign(self):
        rows = api.query(self.start_date, self.end_date, breakdown=['ad_group'], order=['clicks'], campaign=1)

        self.assertEqual(len(rows), 3)

        self.assertEqual(rows[0]['clicks'], 32)
        self.assertEqual(rows[0]['impressions'], 3034)
        self.assertEqual(rows[0]['cost'], 1.4728)
        self.assertEqual(int(rows[0]['ctr'] * 10000)/10000.0, 1.0547)

        self.assertEqual(rows[1]['clicks'], 80)
        self.assertEqual(rows[1]['impressions'], 5570)
        self.assertEqual(rows[1]['cost'], 2.8346)
        self.assertEqual(int(rows[1]['ctr'] * 10000)/10000.0, 1.4362)
        self.assertEqual(rows[1]['cpc'], 0.0354)

        self.assertEqual(rows[2]['clicks'], 106)
        self.assertEqual(rows[2]['impressions'], 6829)
        self.assertEqual(rows[2]['cost'], 3.0292)
        self.assertEqual(int(rows[2]['ctr'] * 10000)/10000.0, 1.5522)
        self.assertEqual(rows[2]['cpc'], 0.0286)

    def test_by_source_for_campaign(self):
        rows = api.query(self.start_date, self.end_date, breakdown=['source'], order=['clicks'], campaign=2)

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[0]['clicks'], 36)
        self.assertEqual(rows[0]['impressions'], 2235)
        self.assertEqual(rows[0]['cost'], 1.5103)
        self.assertEqual(int(rows[0]['ctr'] * 10000)/10000.0, 1.6107)
        self.assertEqual(rows[0]['cpc'], 0.042)

        self.assertEqual(rows[1]['clicks'], 57)
        self.assertEqual(rows[1]['impressions'], 3726)
        self.assertEqual(rows[1]['cost'], 2.2844)
        self.assertEqual(int(rows[1]['ctr'] * 10000)/10000.0, 1.5297)
        self.assertEqual(rows[1]['cpc'], 0.0401)

    def test_by_campaign_for_account(self):
        rows = api.query(self.start_date, self.end_date, breakdown=['campaign'], order=['clicks'], account=1)

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[0]['clicks'], 93)
        self.assertEqual(rows[0]['impressions'], 5961)
        self.assertEqual(rows[0]['cost'], 3.7947)

        self.assertEqual(rows[1]['clicks'], 218)
        self.assertEqual(rows[1]['impressions'], 15433)
        self.assertEqual(rows[1]['cost'], 7.3366)

    def test_by_source_for_account(self):
        rows = api.query(self.start_date, self.end_date, breakdown=['source'], order=['clicks'], account=1)

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[0]['clicks'], 155)
        self.assertEqual(rows[0]['impressions'], 9993)
        self.assertEqual(rows[0]['cost'], 4.8329)

    def test_by_account_for_all(self):
        rows = api.query(self.start_date, self.end_date, breakdown=['account'], order=['clicks'])

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[1]['clicks'], 311)
        self.assertEqual(rows[1]['impressions'], 21394)
        self.assertEqual(rows[1]['cost'], 11.1313)

    def test_by_source_for_all(self):
        rows = api.query(self.start_date, self.end_date, breakdown=['source'], order=['clicks'])

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[1]['clicks'], 175)
        self.assertEqual(rows[1]['impressions'], 11400)
        self.assertEqual(rows[1]['cost'], 5.6237)

    def test_by_day_for_all(self):
        rows = api.query(self.start_date, self.end_date, breakdown=['date'], order=['date'])

        self.assertEqual(len(rows), 3)

        self.assertEqual(rows[0]['clicks'], 107)
        self.assertEqual(rows[0]['impressions'], 7261)
        self.assertEqual(rows[0]['cost'], 4.0096)

