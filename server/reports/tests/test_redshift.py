import datetime
from mock import patch, Mock

from django.test import TestCase

from reports import redshift


@patch('reports.redshift._get_cursor')
class RedshiftTest(TestCase):
    def setUp(self):
        redshift.STATS_DB_NAME = 'default'

    def test_delete_contentadstats(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        date = datetime.date(2015, 1, 1)
        ad_group_id = 1
        source_id = 2

        redshift.delete_contentadstats(date, ad_group_id, source_id)

        query = 'DELETE FROM contentadstats WHERE TRUNC(datetime) = %s AND adgroup_id = %s AND source_id = %s'
        params = ['2015-01-01', 1, 2]

        mock_cursor.execute.assert_called_with(query, params)

    def test_delete_contentadstats_no_source(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        date = datetime.date(2015, 1, 1)
        ad_group_id = 1

        redshift.delete_contentadstats(date, ad_group_id, None)

        query = 'DELETE FROM contentadstats WHERE TRUNC(datetime) = %s AND adgroup_id = %s'
        params = ['2015-01-01', 1]

        mock_cursor.execute.assert_called_with(query, params)

    def test_insert_contentadstats(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_cursor.mogrify.side_effect = ["('a',1)", "('b',2)"]
        mock_get_cursor.return_value = mock_cursor

        rows = [{'x': 1, 'y': 'a'}, {'x': 2, 'y': 'b'}]

        redshift.insert_contentadstats(rows)

        query = "INSERT INTO contentadstats (y,x) VALUES ('a',1),('b',2)"

        mock_cursor.mogrify.assert_any_call('(%s,%s)', ['a', 1])
        mock_cursor.mogrify.assert_any_call('(%s,%s)', ['b', 2])
        mock_cursor.execute.assert_called_with(query, [])

    @patch('reports.redshift.dictfetchall')
    def test_sum_contentadstats(self, _, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        redshift.sum_contentadstats()

        query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats'
        mock_cursor.execute.assert_called_with(query, [])

    def test_vacuum_contentadstats(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        redshift.vacuum_contentadstats()

        query = 'VACUUM FULL contentadstats'

        mock_cursor.execute.assert_called_with(query, [])
