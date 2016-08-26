import datetime
import mock
from django.test import TestCase

from utils import exc
from utils import test_helper

from zemauth.models import User
from dash import models
from dash.constants import Level

from stats import api_breakdowns


class ApiBreakdownQueryTest(TestCase):
    fixtures = ['test_augmenter.yaml']

    @mock.patch('redshiftapi.api_breakdowns.query')
    def test_query(self, mock_rs_query):
        campaign = models.Campaign.objects.get(id=1)
        mock_rs_query.return_value = [
            {'clicks': 1, 'ad_group_id': 1},
        ]

        user = User.objects.get(pk=1)
        breakdown = ['ad_group_id']
        constraints = {
            'show_archived': True,
            'campaign': models.Campaign.objects.get(pk=1),
            'filtered_sources': models.Source.objects.all(),
            'date__gte': datetime.date(2016, 8, 1),
            'date__lte': datetime.date(2016, 8, 5),
        }
        parents = []
        order = 'name'
        offset = 1
        limit = 1

        result = api_breakdowns.query(Level.ACCOUNTS, user, breakdown, constraints, parents, order, offset, limit)

        mock_rs_query.assert_called_with(
            ['ad_group_id'],
            {
                'account_id': 1,
                'campaign_id': 1,
                'date__gte': datetime.date(2016, 8, 1),
                'date__lte': datetime.date(2016, 8, 5),
                'source_id': test_helper.ListMatcher([1, 2, 3]),
            },
            None,
            test_helper.QuerySetMatcher(models.ConversionGoal.objects.filter(campaign_id=campaign.id)),
            test_helper.QuerySetMatcher(models.ConversionPixel.objects.filter(account_id=campaign.account.id)),
            '-clicks',
            1,
            1
        )

        self.assertEqual(result, [{
            'ad_group_id': 1,
            'ad_group_name': 'test adgroup 1',
            'breakdown_id': '1',
            'breakdown_name': 'test adgroup 1',
            'clicks': 1,
            'parent_breakdown_id': '',
        }])
