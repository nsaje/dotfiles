import datetime

from django.test import TestCase
from mock import MagicMock
from mock import patch

import backtosql
from dash import models
from redshiftapi import api_audiences


class AudiencesTestCase(TestCase):
    @patch("redshiftapi.db.get_stats_cursor")
    @patch("redshiftapi.db.dictfetchall")
    def test_get_audience_sample_size(self, mock_dictfetchall, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_dictfetchall.return_value = [{"count": 0}]

        rules = [models.AudienceRule(type=1, value="a,b"), models.AudienceRule(type=2, value="c")]
        api_audiences.get_audience_sample_size(1, "slug1", 10, rules)

        expected_query = (
            "SELECT COUNT(DISTINCT(zuid)) FROM pixie_sample WHERE account_id = %s AND slug = %s AND timestamp > %s "
            "AND (referer ILIKE %s + '%%' OR referer ILIKE %s + '%%' OR referer ILIKE '%%' + %s + '%%')"
        )
        time = datetime.datetime.now().date() - datetime.timedelta(days=10)
        expected_params = [1, "slug1", time.isoformat(), "a", "b", "c"]
        mock_cursor.execute.assert_called_once_with(backtosql.SQLMatcher(expected_query), expected_params)
