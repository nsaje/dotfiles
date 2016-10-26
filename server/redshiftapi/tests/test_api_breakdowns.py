from django.test import TestCase

from redshiftapi import api_breakdowns


class ApiTest(TestCase):

    def test_should_query_all(self):

        self.assertTrue(api_breakdowns.should_query_all([]))
        self.assertTrue(api_breakdowns.should_query_all(['publisher_id', 'week']))

        self.assertTrue(api_breakdowns.should_query_all(['account_id']))
        self.assertFalse(api_breakdowns.should_query_all(['publisher_id']))

        self.assertFalse(api_breakdowns.should_query_all(['account_id', 'ad_group_id']))
        self.assertFalse(api_breakdowns.should_query_all(['source_id', 'ad_group_id']))
