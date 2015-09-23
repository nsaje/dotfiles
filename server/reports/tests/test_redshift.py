import datetime
from mock import patch, Mock, call

from django.test import TestCase

from reports import redshift


@patch('reports.redshift.MyCursor')
class RedshiftTest(TestCase):
    def setUp(self):
        redshift.STATS_DB_NAME = 'default'

    def test_delete_contentadstats(self, mock_cursor):
        date = datetime.date(2015, 1, 1)
        ad_group_id = 1
        source_id = 2

        redshift.delete_contentadstats(date, ad_group_id, source_id)

        query = 'DELETE FROM contentadstats WHERE date = %s AND adgroup_id = %s AND source_id = %s'
        params = ['2015-01-01', 1, 2]

        mock_cursor().execute.assert_called_with(query, params)

    def test_delete_contentadstats_no_source(self, mock_cursor):
        date = datetime.date(2015, 1, 1)
        ad_group_id = 1

        redshift.delete_contentadstats(date, ad_group_id, None)

        query = 'DELETE FROM contentadstats WHERE date = %s AND adgroup_id = %s'
        params = ['2015-01-01', 1]

        mock_cursor().execute.assert_called_with(query, params)

    def test_insert_contentadstats(self, mock_cursor):
        mock_cursor().mogrify.side_effect = ["('a',1)", "('b',2)"]

        rows = [{'x': 1, 'y': 'a'}, {'x': 2, 'y': 'b'}]

        redshift.insert_contentadstats(rows)

        query = "INSERT INTO contentadstats (y,x) VALUES ('a',1),('b',2)"

        mock_cursor().mogrify.assert_any_call('(%s,%s)', ['a', 1])
        mock_cursor().mogrify.assert_any_call('(%s,%s)', ['b', 2])
        mock_cursor().execute.assert_called_with(query, [])

    def test_sum_contentadstats(self, mock_cursor):
        redshift.sum_contentadstats()

        query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats'
        mock_cursor().execute.assert_called_with(query, [])

    def test_get_pixels_last_verified_dt(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock()
        mock_cursor.fetchall.return_value = []
        mock_get_cursor.return_value = mock_cursor

        redshift.get_pixels_last_verified_dt()

        query = 'SELECT account_id, slug, max(conversion_timestamp) FROM touchpointconversions '\
                'GROUP BY slug, account_id'
        mock_cursor.execute.assert_called_with(query, [])

    def test_get_pixels_last_verified_dt_account_id(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock()
        mock_cursor.fetchall.return_value = []
        mock_get_cursor.return_value = mock_cursor

        account_id = 1
        redshift.get_pixels_last_verified_dt(account_id=account_id)

        query = 'SELECT account_id, slug, max(conversion_timestamp) FROM touchpointconversions '\
                'WHERE account_id = %s GROUP BY slug, account_id'
        mock_cursor.execute.assert_called_with(query, [account_id])

    def test_vacuum_contentadstats(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        redshift.vacuum_contentadstats()

        query = 'VACUUM FULL contentadstats'

        mock_cursor.execute.assert_called_with(query, [])

    def test_insert_touchpoint_conversions(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_cursor.mogrify.side_effect = ["('a',1)", "('b',2)"]
        mock_get_cursor.return_value = mock_cursor

        rows = [{'x': 1, 'y': 'a'}, {'x': 2, 'y': 'b'}]

        redshift.insert_touchpoint_conversions(rows)

        query = "INSERT INTO touchpointconversions (y,x) VALUES ('a',1),('b',2)"

        mock_cursor.mogrify.assert_any_call('(%s,%s)', ['a', 1])
        mock_cursor.mogrify.assert_any_call('(%s,%s)', ['b', 2])
        mock_cursor.execute.assert_called_with(query, [])

    def test_delete_touchpoint_conversions(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        date = datetime.date(2015, 1, 1)
        redshift.delete_touchpoint_conversions(date)

        query = 'DELETE FROM touchpointconversions WHERE date = %s'
        params = ['2015-01-01']

        mock_cursor.execute.assert_called_with(query, params)

    def test_vacuum_touchpoint_conversions(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        redshift.vacuum_touchpoint_conversions()

        query = 'VACUUM FULL touchpointconversions'

        mock_cursor.execute.assert_called_with(query, [])


class TestModel(redshift.RSModel):
    FIELDS = [dict(sql='date',            app='date',        out=lambda v: v),
              dict(sql='adgroup_id',      app='ad_group',    out=lambda v: v),
              dict(sql='exchange',        app='exchange',    out=lambda v: v),
              ]


class RedshiftTestRSModel(TestCase):

    def test_delete(self):
        mock_cursor = Mock()

        date = datetime.date(2015, 1, 2)
        ad_group_id = 1
        source_id = 2
        TestModel().execute_delete(mock_cursor, {'date__eq': date, 'ad_group__eq': 4, 'exchange__eq': 'abc'})

        query = 'DELETE FROM "test_table" WHERE adgroup_id=%s AND date=%s AND exchange=%s'
        params =  [4, datetime.date(2015, 1, 2), 'abc']
        
        mock_cursor.execute.assert_called_with(query, params)

    def test_multi_insert_general(self):
        mock_cursor = Mock()

        date = datetime.date(2015, 1, 2)
        ad_group_id = 1
        source_id = 2

        # since this function is _sql, no additional field name checks are done
        redshift.RSModel().execute_multi_insert_sql(mock_cursor, ['field1', 'field2'], (('a', 'b'), ('c', 'd'), ('e', 'f')))

        query = 'INSERT INTO test_table (field1,field2) VALUES (%s,%s),(%s,%s),(%s,%s)'
        params = ['a', 'b', 'c', 'd', 'e', 'f']
        mock_cursor.execute.assert_called_with(query, params)

    def test_multi_insert_general_max2(self):
        mock_cursor = Mock()

        date = datetime.date(2015, 1, 2)
        ad_group_id = 1
        source_id = 2
        
        # since this function is _sql, no additional field name checks are done
        redshift.RSModel().execute_multi_insert_sql(mock_cursor, ['field1', 'field2'], (('a', 'b'), ('c', 'd'), ('e', 'f')), max_at_a_time=2)

        mock_cursor.execute.assert_has_calls([
                                                call('INSERT INTO test_table (field1,field2) VALUES (%s,%s),(%s,%s)', ['a', 'b', 'c', 'd']),
                                                call('INSERT INTO test_table (field1,field2) VALUES (%s,%s)', ['e', 'f'])
                                            ])

    def test_constraints_to_tuples_str(self):
        constraint_str, params = TestModel().constraints_to_str({"exchange": ["ab", "cd"], "date": datetime.date(2015, 1,2)}) 
        self.assertEqual(constraint_str, "date=%s AND exchange IN (%s,%s)")
        self.assertEqual(params, [datetime.date(2015, 1, 2), 'ab', 'cd'])

