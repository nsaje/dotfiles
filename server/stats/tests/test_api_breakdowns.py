import datetime
import mock
from django.test import TestCase

from utils import exc
from utils import test_helper

from zemauth.models import User
from dash import models

from stats import api_breakdowns


class ApiBreakdownTest(TestCase):
    def test_validate_breakdown(self):
        # should succeed, no exception
        api_breakdowns.validate_breakdown(['account_id', 'campaign_id', 'device_type', 'week'])
        api_breakdowns.validate_breakdown(['account_id'])
        api_breakdowns.validate_breakdown([])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Unsupported breakdowns set(['bla'])"):
            api_breakdowns.validate_breakdown(['account_id', 'bla', 'device_type'])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Wrong breakdown order"):
            api_breakdowns.validate_breakdown(['account_id', 'day', 'device_type'])

    def test_validate_constraints(self):
        # should succeed, no exception
        api_breakdowns.validate_constraints({
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'source_id': [1, 2],
            'show_archived': True,
        })

        with self.assertRaises(exc.UnknownFieldBreakdownError):
            api_breakdowns.validate_constraints({
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': [1, 2],  # should be source_id
                'show_archived': True,
            })

    def test_get_supported_order(self):

        self.assertEqual('-media_cost', api_breakdowns.get_supported_order('-cost'))
        self.assertEqual('-clicks', api_breakdowns.get_supported_order('-account_name'))
        self.assertEqual('-clicks', api_breakdowns.get_supported_order('-campaign_name'))
        self.assertEqual('-clicks', api_breakdowns.get_supported_order('-ad_group_name'))
        self.assertEqual('-clicks', api_breakdowns.get_supported_order('-content_ad_title'))


class ApiBreakdownQueryTest(TestCase):
    fixtures = ['test_augmenter.yaml']

    @mock.patch('redshiftapi.api_breakdowns.query')
    def test_query(self, mock_rs_query):

        mock_rs_query.return_value = [
            {'clicks': 1, 'ad_group_id': 1},
        ]

        user = User.objects.get(pk=1)
        breakdown = ['ad_group_id']
        constraints = {
            'show_archived': True,
            'campaign_id': 1,
            'filtered_sources': models.Source.objects.all(),
            'date__gte': datetime.date(2016, 8, 1),
            'date__lte': datetime.date(2016, 8, 5),
        }
        breakdown_page = []
        order = 'name'
        offset = 1
        limit = 1

        result = api_breakdowns.query(user, breakdown, constraints, breakdown_page, order, offset, limit)

        mock_rs_query.assert_called_with(
            ['ad_group_id'],
            {
                'account_id': 1,
                'campaign_id': 1,
                'date__gte': datetime.date(2016, 8, 1),
                'date__lte': datetime.date(2016, 8, 5),
                'source_id': [1, 2, 3],
            },
            None,
            test_helper.QuerySetMatcher(models.ConversionGoal.objects.filter(campaign_id=1)),
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
