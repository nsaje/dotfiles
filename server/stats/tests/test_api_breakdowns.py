import datetime
from django.test import TestCase

from utils import exc

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
