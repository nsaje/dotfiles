from django.test import TestCase

from utils import exc

from stats import api_breakdowns


class ApiBreakdownTest(TestCase):
    def test_validate_breakdown(self):

        # should succeed, no exception
        api_breakdowns.validate_breakdown(['account', 'campaign', 'device', 'week'])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Breakdown requires at least 1 dimension"):
            api_breakdowns.validate_breakdown([])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Unsupported breakdowns set(['bla'])"):
            api_breakdowns.validate_breakdown(['account', 'bla', 'device'])

        with self.assertRaisesMessage(exc.InvalidBreakdownError, "Wrong breakdown order"):
            api_breakdowns.validate_breakdown(['account', 'day', 'device'])
