import backtosql
import io

from django.test import TestCase

from . import derived_views


class GenerateTableTestCase(TestCase):
    def setUp(self):
        self.stream = io.StringIO("""
        CREATE TABLE test (
            -- kw::dimensions
            date date not null encode delta,
            source_id int2 encode zstd,

            -- kw::aggregates
            impressions integer encode zstd,
            clicks integer encode zstd
            -- kw::end
        )
        sortkey(date)
        """)

    def test_generate_table_definition(self):
        table_definition = derived_views.generate_table_definition(
            'test2', self.stream, ['date'], ['date'], 'date')
        backtosql.assert_sql_equals(table_definition, """
        CREATE TABLE IF NOT EXISTS test2 (
            date date not null encode delta,

            impressions integer encode zstd,
            clicks integer encode zstd
        ) diststyle key distkey(date) sortkey(date)
        """)

    def test_generate_table_overrides(self):
        table_definition = derived_views.generate_table_definition(
            'test2', self.stream, ['date'], ['date'], 'date', breakdown_overrides={
                'date': 'date date not null',
            })
        backtosql.assert_sql_equals(table_definition, """
        CREATE TABLE IF NOT EXISTS test2 (
            date date not null,

            impressions integer encode zstd,
            clicks integer encode zstd
        ) diststyle key distkey(date) sortkey(date)
        """)

    def test_parse_table_definition(self):
        dimensions, aggregates = derived_views.parse_table_definition(self.stream)

        self.assertEqual(dimensions, {
            'date': 'date date not null encode delta',
            'source_id': 'source_id int2 encode zstd',
        })

        self.assertEqual(aggregates, [
            'impressions integer encode zstd',
            'clicks integer encode zstd',
        ])
