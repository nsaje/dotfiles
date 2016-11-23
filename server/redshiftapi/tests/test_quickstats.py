import datetime
import mock

from django.test import TestCase

from redshiftapi import queries
from redshiftapi import db
from redshiftapi import quickstats


class QuickstatsTest(TestCase):

    @mock.patch.object(db, 'execute_query', autospec=True)
    @mock.patch.object(queries, 'prepare_query_all_base', autospec=True, return_value=(None, None))
    def test_query_campaign(self, mock_prepare_query_all_base, _):
        date_from = datetime.date.today() - datetime.timedelta(days=7)
        date_to = datetime.date.today()
        quickstats.query_campaign(608, date_from, date_to)
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
