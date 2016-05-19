import backtosql
from django.test import TestCase

from redshiftapi import models


class RSModelTest(TestCase):

    def setUp(self):
        self.model = models.RSContentAdStats

    def test_columns(self):
        columns = self.model.get_columns()
        self.assertEquals(len(columns), 29)

        columns = self.model.select_columns(group=models.BREAKDOWN)
        self.assertEquals(len(columns), 9)

    def test_get_breakdown(self):
        self.assertEquals(
            self.model.get_breakdown(['account_id', 'campaign_id']),
            [self.model.get_column('account_id'), self.model.get_column('campaign_id')]
        )

        # query for unknown column
        with self.assertRaises(backtosql.BackToSQLException):
            self.model.get_breakdown(['bla', 'campaign_id'])

    def test_get_aggregates(self):
        self.assertItemsEqual([x.alias for x in self.model.get_aggregates()],
                              ['clicks', 'impressions', 'cost', 'data_cost',
                               'media_cost', 'e_media_cost', 'e_data_cost',
                               'license_fee', 'billing_cost', 'total_cost',
                               'ctr', 'cpc', 'visits', 'click_discrepancy',
                               'pageviews', 'new_visits', 'percent_new_users',
                               'bounce_rate', 'pv_per_visit', 'avg_tos'])
