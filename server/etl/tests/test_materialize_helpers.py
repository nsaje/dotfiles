import backtosql
import datetime
import mock

from django.test import TestCase

from etl import materialize_helpers


class MaterializeTest(TestCase, backtosql.TestSQLMixin):

    @mock.patch('etl.materialize_helpers.get_write_stats_cursor')
    def test_generate(self, mock_cursor):
        mat = materialize_helpers.Materialize()

        mat.table_name = mock.MagicMock()
        mat.table_name.return_value = 'mv_bla'

        mat.prepare_delete_query = mock.MagicMock()
        mat.prepare_delete_query.return_value = "foo", 33
        mat.prepare_insert_query = mock.MagicMock()
        mat.prepare_insert_query.return_value = "bar", 44

        mat.generate(1, 2, foobar=5)

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call("foo", 33),
            mock.call("bar", 44),
        ])

        mat.prepare_insert_query.assert_called_with(1, 2, foobar=5)

    def test_prepare_delete_query(self):

        date_from = datetime.date(2016, 5, 10)
        date_to = datetime.date(2016, 5, 13)

        mat = materialize_helpers.Materialize()

        mat.table_name = mock.MagicMock()
        mat.table_name.return_value = 'mv_bla'

        sql, params = mat.prepare_delete_query(date_from, date_to)

        self.assertSQLEquals(sql, """
            DELETE
            FROM mv_bla
            WHERE date BETWEEN %(date_from)s AND %(date_to)s;
        """)
        self.assertDictEqual(params, {
            'date_from': date_from,
            'date_to': date_to,
        })


class MaterializeViaCSVTest(TestCase):

    @mock.patch('etl.materialize_helpers.get_write_stats_cursor')
    def test_generate(self, mock_cursor):
        mat = materialize_helpers.MaterializeViaCSV()

        mat.table_name = mock.MagicMock()
        mat.table_name.return_value = 'mv_bla'

        mat.generate_csvs = mock.MagicMock()
        mat.generate_csvs.return_value = [
            'asd', 'bsd', 'csd',
        ]

        mat.prepare_delete_query = mock.MagicMock()
        mat.prepare_delete_query.return_value = "foo", 33
        mat.prepare_insert_query = mock.MagicMock()
        mat.prepare_insert_query.return_value = "bar", 44

        date_from, date_to = datetime.date(2016, 5, 10), datetime.date(2016, 5, 13)
        factors = {
            date_from: 1,
            datetime.date(2016, 5, 11): 2,
            datetime.date(2016, 5, 12): 3,
        }

        mat.generate(date_from, date_to, factors=factors, foobar=456)

        mat.prepare_insert_query.assert_has_calls([
            mock.call("asd", foobar=456, factors=factors),
            mock.call("bsd", foobar=456, factors=factors),
            mock.call("csd", foobar=456, factors=factors),
        ])

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call("foo", 33),
            mock.call("bar", 44),
            mock.call("bar", 44),
            mock.call("bar", 44),
        ])

    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate_daily_csv(self, mock_s3):
        mat = materialize_helpers.MaterializeViaCSV()

        mat.table_name = mock.MagicMock()
        mat.table_name.return_value = 'mv_bla'

        mat.generate_rows = mock.MagicMock()
        mat.generate_rows.return_value = iter([
            ['asd', 'qwe', 5],
            ['foo', 'bar', 2],
        ])

        date = datetime.date(2016, 5, 10)

        expected_path = 'materialized_views/mv_bla/2016/05/10/view.csv'

        path = mat.generate_csvs(mock.MagicMock(), date, date)

        mock_s3().put.assert_called_with(
            expected_path,
            """asd\tqwe\t5\r\nfoo\tbar\t2\r\n""")

        self.assertEquals([expected_path], path)
