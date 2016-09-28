import datetime
from mock import patch, Mock, call, MagicMock

from django.test import TestCase, override_settings

from dash import models
from reports import redshift
from reports.db_raw_helpers import MyCursor


@patch('reports.redshift.get_cursor')
class RedshiftTest(TestCase):
    def setUp(self):
        redshift.STATS_DB_NAME = 'default'

    def test_delete_contentadstats(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = MyCursor(mock_cursor)

        date = datetime.date(2015, 1, 1)
        campaign_id = 1

        redshift.delete_contentadstats(date, campaign_id)

        query = 'DELETE FROM contentadstats WHERE date = %s AND campaign_id = %s AND content_ad_id != %s'
        params = ['2015-01-01', 1, -1]
        mock_cursor.execute.assert_called_with(query, params)

    def test_insert_contentadstats(self, mock_cursor):
        rows = [{'x': 1, 'y': 'a'}, {'x': 2, 'y': 'b'}, {'y': 'asd', 'x': 313}]

        redshift.insert_contentadstats(rows)

        query = "INSERT INTO contentadstats (y,x) VALUES (%s,%s),(%s,%s),(%s,%s)"

        mock_cursor().execute.assert_called_with(query, ['a', 1, 'b', 2, 'asd', 313])

    @override_settings(AWS_ACCESS_KEY_ID='access_key')
    @override_settings(AWS_SECRET_ACCESS_KEY='secret_access_key')
    @override_settings(S3_BUCKET_STATS='test-bucket-stats')
    def test_load_contentadstats(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = MyCursor(mock_cursor)

        redshift.load_contentadstats('test/s3/key.json')

        query = 'COPY contentadstats FROM %s CREDENTIALS %s FORMAT JSON \'auto\' MAXERROR 0'
        params = ['s3://test-bucket-stats/test/s3/key.json',
                  'aws_access_key_id=access_key;aws_secret_access_key=secret_access_key']

        mock_cursor.execute.assert_called_once_with(query, params)

    def test_sum_contentadstats(self, mock_cursor):
        redshift.sum_contentadstats()

        query = 'SELECT SUM(impressions) as impressions, SUM(visits) as visits FROM contentadstats WHERE content_ad_id != %s'
        params = [redshift.REDSHIFT_ADGROUP_CONTENTAD_DIFF_ID]

        mock_cursor().execute.assert_called_with(query, params)

    def test_vacuum_contentadstats(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = MyCursor(mock_cursor)

        redshift.vacuum_contentadstats()

        query = 'VACUUM FULL contentadstats'

        mock_cursor.execute.assert_called_with(query, [])

    def test_insert_touchpoint_conversions(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = mock_cursor

        rows = [{'x': 1, 'y': 'a'}, {'x': 2, 'y': 'b'}, {'y': 'asd', 'x': 313}]

        redshift.insert_touchpoint_conversions(rows)

        query = "INSERT INTO touchpointconversions (y,x) VALUES (%s,%s),(%s,%s),(%s,%s)"

        mock_cursor.execute.assert_called_with(query, ['a', 1, 'b', 2, 'asd', 313])

    def test_delete_touchpoint_conversions(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = MyCursor(mock_cursor)

        date = datetime.date(2015, 1, 1)
        account_id = 1
        slug = 'testslug'
        redshift.delete_touchpoint_conversions(date, account_id, slug)

        query = 'DELETE FROM touchpointconversions WHERE date = %s AND account_id = %s AND slug = %s'
        params = ['2015-01-01', account_id, slug]

        mock_cursor.execute.assert_called_with(query, params)

    def test_delete_publishers(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = MyCursor(mock_cursor)

        date = datetime.date(2015, 1, 1)
        redshift.delete_publishers(date)

        query = 'DELETE FROM publishers_1 WHERE date = %s'
        params = ['2015-01-01']
        mock_cursor.execute.assert_called_with(query, params)

    @override_settings(AWS_ACCESS_KEY_ID='access_key')
    @override_settings(AWS_SECRET_ACCESS_KEY='secret_access_key')
    @override_settings(S3_BUCKET_STATS='test-bucket-stats')
    def test_load_publishers(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = MyCursor(mock_cursor)

        s3_key = 'publishers/2015-01-01-2015-01-31--123456789/part-00000'
        redshift.load_publishers(s3_key)

        query = "COPY publishers_1 FROM %s CREDENTIALS %s FORMAT JSON 'auto' MAXERROR 0"
        params = ['s3://test-bucket-stats/' + s3_key,
                  'aws_access_key_id=access_key;aws_secret_access_key=secret_access_key']
        mock_cursor.execute.assert_called_with(query, params)

    def test_vacuum_touchpoint_conversions(self, mock_get_cursor):
        mock_cursor = Mock()
        mock_get_cursor.return_value = MyCursor(mock_cursor)

        redshift.vacuum_touchpoint_conversions()

        query = 'VACUUM FULL touchpointconversions'

        mock_cursor.execute.assert_called_with(query, [])

    def test_get_audience_sample_size(self, mock_get_cursor):
        mock_cursor = MagicMock()
        mock_cursor.dictfetchall.return_value = [{'count': 0}]
        mock_get_cursor.return_value = mock_cursor

        rules = [
            models.AudienceRule(type=1, value='a,b'),
            models.AudienceRule(type=2, value='c'),
            models.AudienceRule(type=3, value='d,e'),
        ]
        redshift.get_audience_sample_size(1, 'slug1', 10, rules)

        expected_query = 'SELECT COUNT(DISTINCT(zuid)) FROM pixie_sample WHERE account_id = %s AND slug = %s AND timestamp > %s ' \
                         'AND (referer LIKE %s OR referer LIKE %s OR referer LIKE %s OR referer NOT LIKE %s OR referer NOT LIKE %s)'
        time = datetime.datetime.now().date() - datetime.timedelta(days=10)
        expected_params = [1, 'slug1', time.isoformat(), 'a%', 'b%', '%c%', 'd%', 'e%']
        mock_cursor.execute.assert_called_once_with(expected_query, expected_params)


class TestModel(redshift.RSModel):
    FIELDS = [dict(sql='date',            app='date',        out=lambda v: v),
              dict(sql='adgroup_id',      app='ad_group',    out=lambda v: v),
              dict(sql='exchange',        app='exchange',    out=lambda v: v),
              ]


class RedshiftTestRSModel(TestCase):

    def test_delete(self):
        mock_cursor = Mock()

        date = datetime.date(2015, 1, 2)
        TestModel().execute_delete(mock_cursor, {'date__eq': date, 'ad_group__eq': 4, 'exchange__eq': 'abc'})

        query = 'DELETE FROM "test_table" WHERE (adgroup_id=%s AND date=%s AND exchange=%s)'
        params = [4, datetime.date(2015, 1, 2), 'abc']

        mock_cursor.execute.assert_called_with(query, params)

    def test_multi_insert_general(self):
        mock_cursor = Mock()

        # since this function is _sql, no additional field name checks are done
        redshift.RSModel().execute_multi_insert_sql(mock_cursor, ['field1', 'field2'], (('a', 'b'), ('c', 'd'), ('e', 'f')))

        query = 'INSERT INTO test_table (field1,field2) VALUES (%s,%s),(%s,%s),(%s,%s)'
        params = ['a', 'b', 'c', 'd', 'e', 'f']
        mock_cursor.execute.assert_called_with(query, params)

    def test_multi_insert_general_max2(self):
        mock_cursor = Mock()

        # since this function is _sql, no additional field name checks are done
        redshift.RSModel().execute_multi_insert_sql(mock_cursor, ['field1', 'field2'], (('a', 'b'), ('c', 'd'), ('e', 'f')), max_at_a_time=2)

        mock_cursor.execute.assert_has_calls([
            call('INSERT INTO test_table (field1,field2) VALUES (%s,%s),(%s,%s)', ['a', 'b', 'c', 'd']),
            call('INSERT INTO test_table (field1,field2) VALUES (%s,%s)', ['e', 'f'])
        ])

    def test_constraints_to_tuples_str(self):
        constraint_str, params = redshift.RSQ(**{"exchange": ["ab", "cd"], "date": datetime.date(2015, 1, 2)}).expand(TestModel())
        self.assertEqual(constraint_str, "(date=%s AND exchange IN (%s,%s))")
        self.assertEqual(params, [datetime.date(2015, 1, 2), 'ab', 'cd'])


class RedshiftRSQTestCase(TestCase):

    def test_dict_only(self):
        constraints = {'date__lte': datetime.date(2015, 9, 30), 'ad_group': 1}
        constraint_str, params = redshift.RSQ(**constraints).expand(TestModel())
        self.assertEqual(constraint_str, '(adgroup_id=%s AND "date"<=%s)')
        self.assertEqual(params, [1, datetime.date(2015, 9, 30)])

    def test_and(self):
        constraint_str, params = (redshift.RSQ(ad_group=1) & redshift.RSQ(date__lte=datetime.date(2015, 9, 30))).expand(TestModel())
        self.assertEqual(constraint_str, '((adgroup_id=%s) AND ("date"<=%s))')
        self.assertEqual(params, [1, datetime.date(2015, 9, 30)])

    def test_or(self):
        constraint_str, params = (redshift.RSQ(ad_group=1) | redshift.RSQ(date__lte=datetime.date(2015, 9, 30))).expand(TestModel())
        self.assertEqual(constraint_str, '((adgroup_id=%s) OR ("date"<=%s))')
        self.assertEqual(params, [1, datetime.date(2015, 9, 30)])

    def test_negation(self):
        constraint_str, params = (~redshift.RSQ(ad_group=1)).expand(TestModel())
        self.assertEqual(constraint_str, 'NOT (adgroup_id=%s)')
        self.assertEqual(params, [1])

    def test_dict_with_rsq(self):
        constraint_str, params = redshift.RSQ(redshift.RSQ(date=datetime.date(2015, 9, 30)) | redshift.RSQ(ad_group=1), exchange='adiant').expand(TestModel())
        self.assertEqual(constraint_str, '(((date=%s) OR (adgroup_id=%s)) AND exchange=%s)')
        self.assertEqual(params, [datetime.date(2015, 9, 30), 1, 'adiant'])
