from mock import patch
import datetime
import time
import StringIO

import boto.s3
import boto.sqs
from django import test
from django.db.models import Sum
from django.conf import settings

from reports import refresh
from reports import models

import dash.models

from utils import s3helpers
from utils import test_helper


@patch('reports.refresh.put_contentadstats_to_s3')
@patch('reports.refresh.redshift')
class RefreshContentAdStats(test.TestCase):
    fixtures = ['test_api_contentads.yaml']

    def test_refresh_contentadstats(self, mock_redshift, mock_put_contentadstats_to_s3):

        mock_redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        rows = [{
            'conversions': '{"omniture__Transaction 2": 20, "ga__Goal 1": 10}',
            'cost_cc': 150000,
            'pageviews': 1500,
            'content_ad_id': 1,
            'new_visits': 100,
            'clicks': 100,
            'total_time_on_site': 60,
            'bounced_visits': 150,
            'visits': 1000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 1000000,
            'data_cost_cc': 150000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }, {
            'conversions': '{}',
            'cost_cc': 250000,
            'pageviews': 2500,
            'content_ad_id': 2,
            'new_visits': 200,
            'clicks': 200,
            'total_time_on_site': 70,
            'bounced_visits': 250,
            'visits': 2000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 2000000,
            'data_cost_cc': 250000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, test_helper.ListMatcher(rows))
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')

    def test_diff_row(self, mock_redshift, mock_put_contentadstats_to_s3):
        mock_redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        models.ContentAdStats.objects.all().delete()
        models.ContentAdPostclickStats.objects.all().delete()

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        diff_rows = [{
            'conversions': '{}',
            'cost_cc': 400000,
            'pageviews': 4000,
            'account_id': 1,
            'content_ad_id': -1,
            'new_visits': 300,
            'total_time_on_site': 130,
            'campaign_id': 1,
            'visits': 3000,
            'data_cost_cc': 400000,
            'bounced_visits': 400,
            'source_id': 1,
            'date': '2015-02-01',
            'impressions': 3000000,
            'clicks': 300,
            'adgroup_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0,
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, [])
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')
        mock_redshift.insert_contentadstats.assert_called_once_with(diff_rows)

    def test_diff_row_no_ad_group_stats(self, mock_redshift, mock_put_contentadstats_to_s3):
        mock_redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        rows = [{
            'conversions': '{"omniture__Transaction 2": 20, "ga__Goal 1": 10}',
            'cost_cc': 150000,
            'pageviews': 1500,
            'content_ad_id': 1,
            'new_visits': 100,
            'clicks': 100,
            'total_time_on_site': 60,
            'bounced_visits': 150,
            'visits': 1000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 1000000,
            'data_cost_cc': 150000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }, {
            'conversions': '{}',
            'cost_cc': 250000,
            'pageviews': 2500,
            'content_ad_id': 2,
            'new_visits': 200,
            'clicks': 200,
            'total_time_on_site': 70,
            'bounced_visits': 250,
            'visits': 2000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 2000000,
            'data_cost_cc': 250000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, rows)
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')

    def test_refresh_contentadstats_budgets(self, mock_redshift, mock_put_contentadstats_to_s3):

        mock_redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        models.BudgetDailyStatement.objects.create(
            budget_id=1,
            date=date,
            media_spend_nano=400000000000,
            data_spend_nano=400000000000,
            license_fee_nano=80000000000,
        )

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        rows = [{
            'conversions': '{"omniture__Transaction 2": 20, "ga__Goal 1": 10}',
            'cost_cc': 150000,
            'pageviews': 1500,
            'content_ad_id': 1,
            'new_visits': 100,
            'clicks': 100,
            'total_time_on_site': 60,
            'bounced_visits': 150,
            'visits': 1000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 1000000,
            'data_cost_cc': 150000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 15000000000,
            'effective_data_cost_nano': 15000000000,
            'license_fee_nano': 3000000000
        }, {
            'conversions': '{}',
            'cost_cc': 250000,
            'pageviews': 2500,
            'content_ad_id': 2,
            'new_visits': 200,
            'clicks': 200,
            'total_time_on_site': 70,
            'bounced_visits': 250,
            'visits': 2000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 2000000,
            'data_cost_cc': 250000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 25000000000,
            'effective_data_cost_nano': 25000000000,
            'license_fee_nano': 5000000000
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, rows)
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')

    def test_refresh_contentadstats_budgets_diff(self, mock_redshift, mock_put_contentadstats_to_s3):

        mock_redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        models.BudgetDailyStatement.objects.create(
            budget_id=1,
            date=date,
            media_spend_nano=400000000000,
            data_spend_nano=400000000000,
            license_fee_nano=80000000000,
        )

        models.ContentAdStats.objects.all().delete()
        models.ContentAdPostclickStats.objects.all().delete()

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        rows = []
        diff_rows = [{
            'content_ad_id': -1,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'source_id': 1,
            'date': '2015-02-01',
            'impressions': 3000000,
            'clicks': 300,
            'cost_cc': 400000,
            'data_cost_cc': 400000,
            'pageviews': 4000,
            'visits': 3000,
            'new_visits': 300,
            'bounced_visits': 400,
            'total_time_on_site': 130,
            'conversions': '{}',
            'effective_cost_nano': 40000000000,
            'effective_data_cost_nano': 40000000000,
            'license_fee_nano': 8000000000
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, rows)
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')
        mock_redshift.insert_contentadstats.assert_called_once_with(diff_rows)

    def test_refresh_contentadstats_budgets_overspend(self, mock_redshift, mock_put_contentadstats_to_s3):

        mock_redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID = -1
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        # has only 20% of actual spend
        models.BudgetDailyStatement.objects.create(
            budget_id=1,
            date=date,
            media_spend_nano=8000000000,
            data_spend_nano=8000000000,
            license_fee_nano=1600000000,
        )

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        rows = [{
            'conversions': '{"omniture__Transaction 2": 20, "ga__Goal 1": 10}',
            'cost_cc': 150000,
            'pageviews': 1500,
            'content_ad_id': 1,
            'new_visits': 100,
            'clicks': 100,
            'total_time_on_site': 60,
            'bounced_visits': 150,
            'visits': 1000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 1000000,
            'data_cost_cc': 150000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 3000000000,
            'effective_data_cost_nano': 3000000000,
            'license_fee_nano': 600000000
        }, {
            'conversions': '{}',
            'cost_cc': 250000,
            'pageviews': 2500,
            'content_ad_id': 2,
            'new_visits': 200,
            'clicks': 200,
            'total_time_on_site': 70,
            'bounced_visits': 250,
            'visits': 2000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 1),
            'impressions': 2000000,
            'data_cost_cc': 250000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 5000000000,
            'effective_data_cost_nano': 5000000000,
            'license_fee_nano': 1000000000
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, rows)
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')

    def test_refresh_contentadstats_no_source_id(self, mock_redshift, mock_put_contentadstats_to_s3):
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 2)
        campaign = dash.models.Campaign.objects.get(pk=2)

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        rows = [{
            'conversions': '{"omniture__Transaction 2": 30}',
            'cost_cc': 550000,
            'pageviews': 4500,
            'content_ad_id': 3,
            'new_visits': 400,
            'clicks': 500,
            'total_time_on_site': 90,
            'bounced_visits': 450,
            'visits': 4000,
            'source_id': 2,
            'date': datetime.date(2015, 2, 2),
            'impressions': 5000000,
            'data_cost_cc': 550000,
            'adgroup_id': 2,
            'campaign_id': 2,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }, {
            'conversions': '{}',
            'cost_cc': 650000,
            'pageviews': None,
            'content_ad_id': 3,
            'new_visits': None,
            'clicks': 600,
            'total_time_on_site': None,
            'bounced_visits': None,
            'visits': None,
            'source_id': 1,
            'date': datetime.date(2015, 2, 2),
            'impressions': 6000000,
            'data_cost_cc': 650000,
            'adgroup_id': 2,
            'campaign_id': 2,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, rows)
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')

    def test_refresh_contentadstats_missing_contentad_stats(self, mock_redshift, mock_put_contentadstats_to_s3):
        mock_put_contentadstats_to_s3.return_value = 's3_key'

        date = datetime.datetime(2015, 2, 2)
        campaign = dash.models.Campaign.objects.get(pk=3)

        refresh.refresh_contentadstats(date, campaign)

        mock_redshift.delete_contentadstats.assert_called_with(
            date, campaign.id)

        rows = [{
            'conversions': '{}',
            'cost_cc': None,
            'pageviews': 5500,
            'content_ad_id': 4,
            'new_visits': 500,
            'clicks': None,
            'total_time_on_site': 90,
            'bounced_visits': 550,
            'visits': 5000,
            'source_id': 1,
            'date': datetime.date(2015, 2, 2),
            'impressions': None,
            'data_cost_cc': None,
            'adgroup_id': 3,
            'campaign_id': 3,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }]

        mock_put_contentadstats_to_s3.assert_called_once_with(date, campaign, rows)
        mock_redshift.load_contentadstats.assert_called_once_with('s3_key')


class RefreshAdGroupStatsTestCase(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

    def test_refresh_all(self):
        refresh.refresh_adgroup_stats()

        # totals are correct
        article_stats_totals = models.ArticleStats.objects.aggregate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        )
        adgroup_stats_totals = models.AdGroupStats.objects.aggregate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        )
        self.assertEqual(article_stats_totals, adgroup_stats_totals)

        # stats by ad_group are correct
        article_stats_by_adgroup = models.ArticleStats.objects.values(
            'ad_group'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('ad_group')
        adgroup_stats_by_adgroup = models.AdGroupStats.objects.values(
            'ad_group'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('ad_group')
        self.assertEqual(len(article_stats_by_adgroup), len(adgroup_stats_by_adgroup))
        for x, y in zip(article_stats_by_adgroup, adgroup_stats_by_adgroup):
            self.assertEqual(x, y)

        # stats by date are correct
        article_stats_by_date = models.ArticleStats.objects.values(
            'datetime'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('datetime')
        adgroup_stats_by_date = models.AdGroupStats.objects.values(
            'datetime'
        ).annotate(
            clicks=Sum('clicks'),
            impressions=Sum('impressions'),
            cost_cc=Sum('cost_cc')
        ).order_by('datetime')
        self.assertEqual(len(article_stats_by_date), len(adgroup_stats_by_date))
        for x, y in zip(article_stats_by_date, adgroup_stats_by_date):
            self.assertEqual(x, y)

    def test_refresh_subset(self):
        refresh.refresh_adgroup_stats()

        astat = models.ArticleStats.objects.get(pk=1)
        astat.impressions += 1
        astat.clicks += 1
        astat.cost_cc += 1
        astat.save()

        astat_other = models.ArticleStats.objects.get(pk=7)
        self.assertTrue(astat_other.ad_group.id != astat.ad_group.id)

        # not yet refreshed, there are some differences
        imps_article_stats = models.ArticleStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        imps_adgroup_stats = models.AdGroupStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        self.assertEqual(imps_adgroup_stats + 1, imps_article_stats)

        # refresh for a single ad group
        refresh.refresh_adgroup_stats(ad_group=astat.ad_group)

        # now there are no differences anymore
        imps_article_stats = models.ArticleStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        imps_adgroup_stats = models.AdGroupStats.objects \
              .filter(ad_group=astat.ad_group) \
              .aggregate(impressions=Sum('impressions'))['impressions']
        self.assertEqual(imps_adgroup_stats, imps_article_stats)

    def test_cannot_refresh_invalid_constraints(self):
        with self.assertRaises(AssertionError):
            refresh.refresh_adgroup_stats(invalid_field='invalid value')


class ContentAdStatsDataChangeTestCase(test.TestCase):

    fixtures = ['test_reports_base.yaml']

    @patch('utils.sqs_helper.write_message_json')
    @test.override_settings(CAMPAIGN_CHANGE_QUEUE='test')
    def test_notify_contentadstats_change(self, mock_sqs_write_message):
        date = datetime.date(2015, 12, 1)
        refresh.notify_contentadstats_change(date, 1)
        mock_sqs_write_message.assert_called_once_with(settings.CAMPAIGN_CHANGE_QUEUE,
                                                       {'date': date.isoformat(), 'campaign_id': 1})

    @patch('reports.refresh.notify_daily_statements_change')
    @patch('reports.daily_statements.reprocess_daily_statements')
    @patch('reports.refresh.refresh_contentadstats')
    @patch('utils.sqs_helper.get_all_messages')
    @patch('utils.sqs_helper.delete_messages')
    @test.override_settings(CAMPAIGN_CHANGE_QUEUE='test')
    def test_refresh_changed_contentadstats(self, mock_delete_messages, mock_get_all_messages,
                                            mock_refresh_contentadstats, mock_reprocess, mock_notify):
        campaign_id = 1

        message1 = boto.sqs.message.Message(body='{"date": "2015-12-01", "campaign_id": 1}')
        message2 = boto.sqs.message.Message(body='{"date": "2016-01-01", "campaign_id": 1}')
        mock_get_all_messages.return_value = [message1, message2]
        mock_reprocess.return_value = [
            datetime.date(2015, 12, 1),
            datetime.date(2015, 12, 2),
            datetime.date(2015, 12, 3),
            datetime.date(2015, 12, 4),
            datetime.date(2015, 12, 5),
        ]

        refresh.refresh_changed_contentadstats()

        campaign = dash.models.Campaign.objects.get(id=campaign_id)
        mock_reprocess.assert_called_once_with(datetime.date(2015, 12, 1), campaign)

        mock_delete_messages.assert_called_once_with(settings.CAMPAIGN_CHANGE_QUEUE, [message1, message2])

    @patch('reports.refresh.notify_daily_statements_change')
    @patch('reports.daily_statements.reprocess_daily_statements')
    @patch('reports.refresh.refresh_contentadstats')
    @patch('utils.sqs_helper.get_all_messages')
    @patch('utils.sqs_helper.delete_messages')
    @test.override_settings(CAMPAIGN_CHANGE_QUEUE='test')
    def test_refresh_changed_contentadstats_duplicate(self, mock_delete_messages, mock_get_all_messages,
                                                      mock_refresh_contentadstats, mock_reprocess, mock_notify):
        campaign_id = 1
        message1 = boto.sqs.message.Message(body='{"date": "2015-12-01", "campaign_id": 1}')
        message2 = boto.sqs.message.Message(body='{"date": "2015-12-01", "campaign_id": 1}')
        mock_get_all_messages.return_value = [message1, message2]
        mock_reprocess.return_value = [
            datetime.date(2015, 12, 1),
            datetime.date(2015, 12, 2),
            datetime.date(2015, 12, 3),
            datetime.date(2015, 12, 4),
            datetime.date(2015, 12, 5),
        ]

        refresh.refresh_changed_contentadstats()

        campaign = dash.models.Campaign.objects.get(id=campaign_id)
        mock_reprocess.assert_called_once_with(datetime.date(2015, 12, 1), campaign)
        mock_delete_messages.assert_called_once_with(settings.CAMPAIGN_CHANGE_QUEUE, [message1, message2])


class RefreshB1PublisherDataTestCase(test.TestCase):

    fixtures = ['test_api_contentads.yaml']

    @patch.object(s3helpers.S3Helper, 'list')
    def test_get_latest_b1_pub_data_s3_key(self, s3_helper_list_mock):
        s3_helper_list_mock.return_value = [
            boto.s3.key.Key(name='publishers/2016-01-01-2016-01-01--1451296802070761934'),
            boto.s3.key.Key(name='publishers/2016-01-01-2016-01-01--1451282401204254907')
        ]

        ret = refresh._get_latest_b1_pub_data_s3_key(datetime.date(2016, 1, 1))

        s3_helper_list_mock.assert_called_once_with('publishers/2016-01-01-2016-01-01')
        self.assertEqual('publishers/2016-01-01-2016-01-01--1451296802070761934', ret)

    @patch.object(s3helpers.S3Helper, 'get')
    @patch('reports.refresh._get_latest_b1_pub_data_s3_key')
    def test_get_latest_b1_pub_data(self, mock_get_s3_key, mock_s3_get):
        raw_b1_data = '2016-01-01,1,adiant,adiant.com,10,1000,20000000,1000000\n'\
                      '2016-01-01,1,adsnative,adsnative.com,5,800,800000,200000'
        mock_get_s3_key.return_value = 'some_key'
        mock_s3_get.return_value = StringIO.StringIO(raw_b1_data)

        data = refresh._get_latest_b1_pub_data(datetime.date(2016, 1, 1))
        expected = [
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adiant',
                'domain': 'adiant.com',
                'clicks': 10,
                'impressions': 1000,
                'cost_micro': 20000000,
                'data_cost_micro': 1000000
            },
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adsnative',
                'domain': 'adsnative.com',
                'clicks': 5,
                'impressions': 800,
                'cost_micro': 800000,
                'data_cost_micro': 200000
            }
        ]

        self.assertEqual(expected, data)

    @patch('reports.daily_statements.get_effective_spend_pcts')
    def test_augment_b1_pub_data_with_budgets(self, mock_effective_spend_pcts):
        mock_effective_spend_pcts.return_value = (0.5, 0.1)
        publisher_data = [
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adiant',
                'domain': 'adiant.com',
                'clicks': 10,
                'impressions': 1000,
                'cost_micro': 20000000,
                'data_cost_micro': 1000000
            },
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adsnative',
                'domain': 'adsnative.com',
                'clicks': 5,
                'impressions': 800,
                'cost_micro': 800000,
                'data_cost_micro': 200000
            }
        ]

        refresh._augment_b1_pub_data_with_budgets(publisher_data)
        expected = [
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adiant',
                'domain': 'adiant.com',
                'clicks': 10,
                'impressions': 1000,
                'cost_micro': 20000000,
                'data_cost_micro': 1000000,
                'effective_cost_nano': 10000000000,
                'effective_data_cost_nano': 500000000,
                'license_fee_nano': 1050000000,
            },
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adsnative',
                'domain': 'adsnative.com',
                'clicks': 5,
                'impressions': 800,
                'cost_micro': 800000,
                'data_cost_micro': 200000,
                'effective_cost_nano': 400000000,
                'effective_data_cost_nano': 100000000,
                'license_fee_nano': 50000000,
            }
        ]

        self.assertEqual(publisher_data, expected)

    @patch('reports.refresh.time')
    @patch('reports.refresh._get_latest_b1_pub_data')
    @patch('reports.refresh._augment_b1_pub_data_with_budgets')
    @patch('utils.s3helpers.S3Helper')
    def test_process_b1_publisher_stats(self, mock_s3_helper, mock_augment, mock_get_latest, mock_time):
        mock_time.time.return_value = time.mktime(datetime.datetime(2016, 1, 1).timetuple())
        mock_get_latest.return_value = [
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adiant',
                'domain': 'adiant.com',
                'clicks': 10,
                'impressions': 1000,
                'cost_micro': 20000000,
                'data_cost_micro': 1000000,
                'effective_cost_nano': 10000000000,
                'effective_data_cost_nano': 500000000,
                'license_fee_nano': 1050000000,
            },
            {
                'date': datetime.date(2016, 1, 1),
                'ad_group_id': 1,
                'exchange': 'adsnative',
                'domain': 'adsnative.com',
                'clicks': 5,
                'impressions': 800,
                'cost_micro': 800000,
                'data_cost_micro': 200000,
                'effective_cost_nano': 400000000,
                'effective_data_cost_nano': 100000000,
                'license_fee_nano': 50000000,
            }
        ]

        refresh.process_b1_publishers_stats(datetime.date(2016, 1, 1))

        expected_key = 'b1_publishers_load/2016/1/1/1451606400000.json'
        expected_json = '{"domain": "adiant.com", "ad_group_id": 1, "exchange": "adiant", "date": "2016-01-01", '\
                        '"impressions": 1000, "license_fee_nano": 1050000000, "data_cost_micro": 1000000, '\
                        '"effective_cost_nano": 10000000000, "cost_micro": 20000000, '\
                        '"effective_data_cost_nano": 500000000, "clicks": 10}\n{"domain": "adsnative.com", '\
                        '"ad_group_id": 1, "exchange": "adsnative", "date": "2016-01-01", "impressions": 800, '\
                        '"license_fee_nano": 50000000, "data_cost_micro": 200000, "effective_cost_nano": 400000000, '\
                        '"cost_micro": 800000, "effective_data_cost_nano": 100000000, "clicks": 5}'
        mock_s3_helper.return_value.put.assert_called_once_with(expected_key, expected_json)

    @patch('reports.redshift.delete_publishers')
    @patch('reports.redshift.load_b1_publishers')
    @patch('reports.refresh.process_b1_publishers_stats')
    def test_refresh_b1_publishers_data(self, mock_process_stats, mock_load_pubs, mock_delete_pubs):
        mock_process_stats.return_value = 's3_key'

        date = datetime.date(2016, 1, 1)
        refresh.refresh_b1_publishers_data(date)

        mock_delete_pubs.assert_called_once_with(date)
        mock_load_pubs.assert_called_once_with('s3_key')


class PutContentAdStatsToS3TestCase(test.TestCase):

    fixtures = ['test_api_contentads.yaml']

    @patch('utils.s3helpers.S3Helper')
    @patch('reports.refresh.time')
    def test_put_contentadstats_to_s3(self, mock_time, mock_s3helper):
        mock_time.time.return_value = time.mktime(datetime.datetime(2016, 1, 1).timetuple())
        campaign = dash.models.Campaign.objects.get(id=1)
        date = datetime.date(2015, 2, 1)

        test_rows = [{
            'conversions': '{"omniture__transaction 2": 20, "ga__goal 1": 10}',
            'cost_cc': 150000,
            'pageviews': 1500,
            'content_ad_id': 1,
            'new_visits': 100,
            'clicks': 100,
            'total_time_on_site': 60,
            'bounced_visits': 150,
            'visits': 1000,
            'source_id': 1,
            'date': date,
            'impressions': 1000000,
            'data_cost_cc': 150000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }, {
            'conversions': '{}',
            'cost_cc': 250000,
            'pageviews': 2500,
            'content_ad_id': 2,
            'new_visits': 200,
            'clicks': 200,
            'total_time_on_site': 70,
            'bounced_visits': 250,
            'visits': 2000,
            'source_id': 1,
            'date': date,
            'impressions': 2000000,
            'data_cost_cc': 250000,
            'adgroup_id': 1,
            'campaign_id': 1,
            'account_id': 1,
            'effective_cost_nano': 0,
            'effective_data_cost_nano': 0,
            'license_fee_nano': 0
        }]

        refresh.put_contentadstats_to_s3(date, campaign, test_rows)

        expected_key = 'contentadstats_load/2015/2/1/1/1451606400000.json'
        expected_json =\
            '{"conversions": "{\\"omniture__transaction 2\\": 20, \\"ga__goal 1\\": 10}", "license_fee_nano": 0, '\
            '"cost_cc": 150000, "pageviews": 1500, "account_id": 1, "content_ad_id": 1, "new_visits": 100, '\
            '"effective_cost_nano": 0, "total_time_on_site": 60, "bounced_visits": 150, "visits": 1000, '\
            '"data_cost_cc": 150000, "date": "2015-02-01", "effective_data_cost_nano": 0, "source_id": 1, '\
            '"impressions": 1000000, "clicks": 100, "adgroup_id": 1, "campaign_id": 1}\n{"conversions": "{}", '\
            '"license_fee_nano": 0, "cost_cc": 250000, "pageviews": 2500, "account_id": 1, "content_ad_id": 2, '\
            '"new_visits": 200, "effective_cost_nano": 0, "total_time_on_site": 70, "bounced_visits": 250, '\
            '"visits": 2000, "data_cost_cc": 250000, "date": "2015-02-01", "effective_data_cost_nano": 0, '\
            '"source_id": 1, "impressions": 2000000, "clicks": 200, "adgroup_id": 1, "campaign_id": 1}'

        mock_s3helper.return_value.put.assert_called_once_with(expected_key, expected_json)
