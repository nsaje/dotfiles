import backtosql

from django.test import TestCase

from etl import models


class ColumnsTest(TestCase, backtosql.TestSQLMixin):

    def test_conversion_window(self):
        column = models.K1Conversions.get_column('conversion_window')

        self.assertSQLEquals(column.column_as_alias('T'), """\
        CASE \
        WHEN T.conversion_lag <= 24 THEN 24\
        WHEN T.conversion_lag > 24 AND T.conversion_lag <= 168 THEN 168\
        ELSE 720\
        END AS conversion_window""")

    def test_count(self):
        column = models.K1Conversions.get_column('count')

        self.assertSQLEquals(column.column_as_alias('T'), "COUNT(*) AS count")

    def test_json_dict_sum(self):
        column = models.K1PostclickStats.conversions

        self.assertSQLEquals(column.column_as_alias('T'), "json_dict_sum(listagg(T.conversions, ';'), ';') as conversions")
