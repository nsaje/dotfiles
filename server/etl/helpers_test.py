import datetime

from django.test import TestCase

import backtosql
from etl import helpers


class HelpersTest(TestCase, backtosql.TestSQLMixin):
    def test_get_local_date_context(self):
        context = helpers.get_local_date_context(datetime.date(2016, 5, 1))

        self.assertDictEqual(
            context,
            {
                "date": "2016-05-01",
                "tzdate_from": "2016-05-01",
                "tzhour_from": 4,
                "tzdate_to": "2016-05-02",
                "tzhour_to": 4,
            },
        )

    def test_get_local_multiday_date_context_one_day(self):
        context = helpers.get_local_multiday_date_context(datetime.date(2016, 5, 1), datetime.date(2016, 5, 1))

        self.assertDictEqual(
            context,
            {
                "date_from": "2016-05-01",
                "date_to": "2016-05-01",
                "tzdate_from": "2016-05-01",
                "tzhour_from": 4,
                "tzdate_to": "2016-05-02",
                "tzhour_to": 4,
                "date_ranges": [
                    {
                        "date": "2016-05-01",
                        "tzdate_from": "2016-05-01",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-05-02",
                        "tzhour_to": 4,
                    }
                ],
            },
        )

    def test_get_local_multiday_date_context(self):
        context = helpers.get_local_multiday_date_context(datetime.date(2016, 5, 1), datetime.date(2016, 5, 3))

        self.assertDictEqual(
            context,
            {
                "date_from": "2016-05-01",
                "date_to": "2016-05-03",
                "tzdate_from": "2016-05-01",
                "tzhour_from": 4,
                "tzdate_to": "2016-05-04",
                "tzhour_to": 4,
                "date_ranges": [
                    {
                        "date": "2016-05-01",
                        "tzdate_from": "2016-05-01",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-05-02",
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-05-02",
                        "tzdate_from": "2016-05-02",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-05-03",
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-05-03",
                        "tzdate_from": "2016-05-03",
                        "tzhour_from": 4,
                        "tzdate_to": "2016-05-04",
                        "tzhour_to": 4,
                    },
                ],
            },
        )

    def test_get_local_date_query(self):
        query = helpers.get_local_date_query(datetime.date(2016, 5, 1))

        self.assertSQLEquals(
            query,
            """\
        date >= '2016-05-01' and date <= '2016-05-02' and (
        (date = '2016-05-01' and hour is null) or (
            hour is not null and (
                (date = '2016-05-01' and hour >= 4) or
                (date = '2016-05-02' and hour < 4)
            )
        ))""",
        )

    def test_calculate_effective_cost(self):
        factors = (0.2, 0.1, 0.15)

        effective_cost, effective_data_cost, license_fee, margin = helpers.calculate_effective_cost(250, 300, factors)

        self.assertEqual(effective_cost, 50.0)
        self.assertEqual(effective_data_cost, 60.0)
        self.assertEqual(license_fee, 11.0)
        self.assertEqual(margin, 18.15)

    def test_extract_source_slug(self):
        self.assertEqual(helpers.extract_source_slug("b1_outbrain"), "outbrain")
        self.assertEqual(helpers.extract_source_slug("outbrain"), "outbrain")

    def test_extract_postclick_source(self):
        self.assertEqual(helpers.extract_postclick_source("gaapi"), "gaapi")
        self.assertEqual(helpers.extract_postclick_source("ga_mail"), "ga_mail")
        self.assertEqual(helpers.extract_postclick_source("omniture"), "omniture")
        self.assertEqual(helpers.extract_postclick_source("lol"), "other")

    def test_get_highest_priority_postclick_source(self):
        self.assertEqual(helpers.get_highest_priority_postclick_source({"gaapi": 1, "ga_mail": 2}), 1)
        self.assertEqual(helpers.get_highest_priority_postclick_source({"ga_mail": 2}), 2)
        self.assertEqual(helpers.get_highest_priority_postclick_source({"ga_mail": 2, "omniture": 3, "other": 4}), 2)
        self.assertEqual(helpers.get_highest_priority_postclick_source({"omniture": 3, "other": 4}), 3)
        self.assertEqual(helpers.get_highest_priority_postclick_source({"other": 4}), 4)

    def test_prepare_create_timescale_hypertable(self):
        query = helpers.prepare_create_timescale_hypertable("test_table")

        self.assertSQLEquals(
            query, "SELECT create_hypertable('test_table', 'date', chunk_time_interval => INTERVAL '1 day');"
        )

    def prepare_drop_timescale_hypertable_chunks(self):
        query = helpers.prepare_drop_timescale_hypertable_chunks("test_table", 17)

        self.assertSQLEquals(query, "SELECT drop_chunks(INTERVAL '17 days', 'test_table');")
