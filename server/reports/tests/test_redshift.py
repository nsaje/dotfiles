import datetime
from mock import patch, ANY

from django.test import TestCase

from reports import redshift


@patch('reports.redshift._execute')
class RedshiftTest(TestCase):
    def setUp(self):
        redshift.STATS_DB_NAME = 'default'

    def test_delete_contentadstats(self, mock_execute):
        date = datetime.date(2015, 1, 1)
        ad_group_id = 1
        source_id = 2

        redshift.delete_contentadstats(date, ad_group_id, source_id)

        query = 'DELETE FROM contentadstats WHERE TRUNC(datetime) = %s AND adgroup_id = %s AND source_id = %s'
        params = ['2015-01-01', 1, 2]

        mock_execute.assert_called_with(ANY, query, params)

    def test_delete_contentadstats_no_source(self, mock_execute):
        date = datetime.date(2015, 1, 1)
        ad_group_id = 1

        redshift.delete_contentadstats(date, ad_group_id, None)

        query = 'DELETE FROM contentadstats WHERE TRUNC(datetime) = %s AND adgroup_id = %s'
        params = ['2015-01-01', 1]

        mock_execute.assert_called_with(ANY, query, params)

    def test_insert_contentadstats(self, mock_execute):
        rows = [{'x': 1, 'y': 'a'}, {'x': 2, 'y': 'b'}]

        redshift.insert_contentadstats(rows)

        query = "INSERT INTO contentadstats (y,x) VALUES ('a',1),('b',2)"

        mock_execute.assert_called_with(ANY, query, [])
