from django.test import TestCase
from mock import MagicMock
from mock import patch

import backtosql
from redshiftapi import api_inventory


class InventoryTestCase(TestCase):
    @patch("redshiftapi.db.get_stats_cursor")
    @patch("redshiftapi.db.dictfetchall")
    def test_query_summary(self, mock_dictfetchall, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_dictfetchall.return_value = [{"count": 0}]

        api_inventory.query(None, None)
        expected_query = """
SELECT
   sum(bid_reqs) bid_reqs,
   sum(bids) bids,
   sum(redirects) redirects,
   sum(slots) slots,
   sum(total_win_price) total_win_price,
   sum(win_notices) win_notices
FROM mv_inventory
WHERE 1=1
ORDER BY slots DESC NULLS LAST
LIMIT 20000
        """
        expected_params = []
        mock_cursor.execute.assert_called_once_with(backtosql.SQLMatcher(expected_query), expected_params)

    @patch("redshiftapi.db.get_stats_cursor")
    @patch("redshiftapi.db.dictfetchall")
    def test_query_breakdown_filters(self, mock_dictfetchall, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_dictfetchall.return_value = [{"count": 0}]

        api_inventory.query("country", {"device_type": [1, 2], "publisher": ["cnn.com", "bbc.co.uk"]})
        expected_query = """
SELECT
   country as country,
   sum(bid_reqs) bid_reqs,
   sum(bids) bids,
   sum(redirects) redirects,
   sum(slots) slots,
   sum(total_win_price) total_win_price,
   sum(win_notices) win_notices
FROM mv_inventory
WHERE (
   device_type=ANY(%s)
   AND publisher=ANY(%s)
)
GROUP BY 1
ORDER BY slots DESC NULLS LAST
LIMIT 20000
        """
        expected_params = [[1, 2], ["cnn.com", "bbc.co.uk"]]
        mock_cursor.execute.assert_called_once_with(backtosql.SQLMatcher(expected_query), expected_params)
