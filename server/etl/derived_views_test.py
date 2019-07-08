import collections
import io

from django.test import TestCase

import backtosql

from . import derived_views


class GenerateTableTestCase(TestCase):
    def setUp(self):
        self.stream = io.StringIO(
            """
        CREATE TABLE test (
            -- kw::dimensions
            date date not null encode delta,
            source_id int2 encode zstd,

            -- kw::aggregates
            impressions integer encode zstd,
            clicks integer encode zstd

            -- kw::dimensions
            type int2 encode zstd
            -- kw::end
        )
        sortkey(date)
        """
        )

    def test_generate_table_definition(self):
        table_definition = derived_views.generate_table_definition(
            "test2", self.stream, ["date", "type"], ["date"], "date"
        )
        backtosql.assert_sql_equals(
            table_definition,
            """
        CREATE TABLE IF NOT EXISTS test2 (
            date date not null encode delta,

            impressions integer encode zstd,
            clicks integer encode zstd,

            type int2 encode zstd
        ) diststyle key distkey(date) sortkey(date)
        """,
        )

    def test_generate_table_overrides(self):
        table_definition = derived_views.generate_table_definition(
            "test2", self.stream, ["date"], ["date"], "date", breakdown_overrides={"date": "date date not null"}
        )
        backtosql.assert_sql_equals(
            table_definition,
            """
        CREATE TABLE IF NOT EXISTS test2 (
            date date not null,

            impressions integer encode zstd,
            clicks integer encode zstd
        ) diststyle key distkey(date) sortkey(date)
        """,
        )

    def test_parse_table_definition(self):
        column_definitions = derived_views.parse_table_definition(self.stream)

        self.assertEqual(
            column_definitions,
            collections.OrderedDict(
                [
                    ("date", derived_views.ColumnDefinition("date date not null encode delta", True)),
                    ("source_id", derived_views.ColumnDefinition("source_id int2 encode zstd", True)),
                    ("impressions", derived_views.ColumnDefinition("impressions integer encode zstd", False)),
                    ("clicks", derived_views.ColumnDefinition("clicks integer encode zstd", False)),
                    ("type", derived_views.ColumnDefinition("type int2 encode zstd", True)),
                ]
            ),
        )
