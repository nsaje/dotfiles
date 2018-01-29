import datetime
import mock

from django.test import TestCase

from redshiftapi import queries
from redshiftapi import db
from redshiftapi import api_quickstats


class QuickstatsTest(TestCase):

    @mock.patch.object(db, 'execute_query', autospec=True)
    @mock.patch.object(queries, 'prepare_query_all_base', autospec=True, return_value=(None, None))
    def test_query_campaign(self, mock_prepare_query_all_base, _):
        date_from = datetime.date.today() - datetime.timedelta(days=7)
        date_to = datetime.date.today()
        api_quickstats.query_campaign(608, date_from, date_to)
        expected_constraints = {
            'campaign_id': 608,
            'date__gte': date_from,
            'date__lte': date_to,
        }
        mock_prepare_query_all_base.assert_called_with(
            breakdown=[],
            constraints=expected_constraints,
            parents=None,
            use_publishers_view=False
        )

    @mock.patch.object(db, 'execute_query', autospec=True)
    @mock.patch.object(queries, 'prepare_query_all_base', autospec=True, return_value=(None, None))
    def test_query_adgroup(self, mock_prepare_query_all_base, _):
        date_from = datetime.date.today() - datetime.timedelta(days=7)
        date_to = datetime.date.today()
        api_quickstats.query_adgroup(2040, date_from, date_to, source_id=3)
        expected_constraints = {
            'ad_group_id': 2040,
            'date__gte': date_from,
            'date__lte': date_to,
            'source_id': 3,
        }
        mock_prepare_query_all_base.assert_called_with(
            breakdown=[],
            constraints=expected_constraints,
            parents=None,
            use_publishers_view=False
        )
