import datetime

from django.test import TestCase
from mock import ANY
from mock import patch

import stats.constants
from redshiftapi import api_breakdowns
from stats.helpers import Goals


class ApiTestCase(TestCase):
    def test_should_query_all(self):
        self.assertTrue(api_breakdowns._should_query_all([]))
        self.assertTrue(api_breakdowns._should_query_all(["publisher_id", "week"]))

        self.assertTrue(api_breakdowns._should_query_all(["account_id"]))
        self.assertFalse(api_breakdowns._should_query_all(["publisher_id"]))
        self.assertFalse(api_breakdowns._should_query_all(["placement_id"]))

        self.assertFalse(api_breakdowns._should_query_all(["publisher_id", "placement_id"]))

        self.assertFalse(api_breakdowns._should_query_all(["source_id", "placement_id"]))

        self.assertFalse(api_breakdowns._should_query_all(["account_id", "ad_group_id"]))
        self.assertFalse(api_breakdowns._should_query_all(["campaign_id", "content_ad_id"]))

        self.assertTrue(api_breakdowns._should_query_all(["source_id", "ad_group_id"]))
        self.assertTrue(api_breakdowns._should_query_all(["campaign_id", "ad_group_id"]))
        self.assertTrue(api_breakdowns._should_query_all(["campaign_id", "source_id"]))

        for field in stats.constants.get_top_level_delivery_dimensions():
            self.assertFalse(api_breakdowns._should_query_all([field]))
            self.assertFalse(api_breakdowns._should_query_all([field, field]))


class QueryTestCase(TestCase):
    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=True)
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_all_base(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "clicks": 1},
            {"campaign_id": 1, "clicks": 2},
            {"campaign_id": 2, "clicks": 3},
            {"campaign_id": 2, "clicks": 4},
        ]

        rows = api_breakdowns.query(
            ["campaign_id"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            None,
            Goals(None, None, None, None, None),
            "-clicks",
            1,
            1,
            False,
        )

        # commented lines indicate the whole result set
        self.assertCountEqual(
            rows,
            [
                # {'campaign_id': 2, 'clicks': 4},
                {"campaign_id": 2, "clicks": 3},
                # {'campaign_id': 1, 'clicks': 2},
                # {'campaign_id': 1, 'clicks': 1},
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=True)
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_all_depth_2(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "ad_group_id": 1, "clicks": 1},
            {"campaign_id": 1, "ad_group_id": 2, "clicks": 2},
            {"campaign_id": 2, "ad_group_id": 3, "clicks": 3},
            {"campaign_id": 2, "ad_group_id": 4, "clicks": 4},
        ]

        rows = api_breakdowns.query(
            ["campaign_id", "ad_group_id"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            [{"campaign_id": 1}, {"campaign_id": 2}],
            Goals(None, None, None, None, None),
            "-clicks",
            1,
            1,
            False,
        )

        # commented lines indicate the whole result set
        self.assertCountEqual(
            rows,
            [
                # {'campaign_id': 2, 'ad_group_id': 4, 'clicks': 4},  # offset
                {"campaign_id": 2, "ad_group_id": 3, "clicks": 3},
                # {'campaign_id': 1, 'ad_group_id': 2, 'clicks': 2},
                {"campaign_id": 1, "ad_group_id": 1, "clicks": 1},
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=True)
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_all_depth_3(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "ad_group_id": 1, "dma": 501, "clicks": 1},
            {"campaign_id": 1, "ad_group_id": 1, "dma": 502, "clicks": 2},
            {"campaign_id": 1, "ad_group_id": 2, "dma": 501, "clicks": 3},
            {"campaign_id": 1, "ad_group_id": 2, "dma": 502, "clicks": 4},
            {"campaign_id": 2, "ad_group_id": 3, "dma": 501, "clicks": 5},
            {"campaign_id": 2, "ad_group_id": 3, "dma": 502, "clicks": 6},
            {"campaign_id": 2, "ad_group_id": 4, "dma": 501, "clicks": 7},
            {"campaign_id": 2, "ad_group_id": 4, "dma": 502, "clicks": 8},
        ]

        rows = api_breakdowns.query(
            ["campaign_id", "ad_group_id", "dma"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            [
                {"campaign_id": 1, "ad_group_id": 1},
                {"campaign_id": 1, "ad_group_id": 2},
                {"campaign_id": 2, "ad_group_id": 3},
                {"campaign_id": 2, "ad_group_id": 4},
            ],
            Goals(None, None, None, None, None),
            "clicks",
            1,
            1,
            False,
        )

        # commented lines indicate the whole result set
        self.assertCountEqual(
            rows,
            [
                # {'campaign_id': 1, 'ad_group_id': 1, 'dma': 501, 'clicks': 1},
                {"campaign_id": 1, "ad_group_id": 1, "dma": 502, "clicks": 2},
                # {'campaign_id': 1, 'ad_group_id': 2, 'dma': 501, 'clicks': 3,},
                {"campaign_id": 1, "ad_group_id": 2, "dma": 502, "clicks": 4},
                # {'campaign_id': 2, 'ad_group_id': 3, 'dma': 501, 'clicks': 5},
                {"campaign_id": 2, "ad_group_id": 3, "dma": 502, "clicks": 6},
                # {'campaign_id': 2, 'ad_group_id': 4, 'dma': 501, 'clicks': 7},
                {"campaign_id": 2, "ad_group_id": 4, "dma": 502, "clicks": 8},
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=False)
    @patch("redshiftapi.db.execute_query")
    def test_query_joint_base(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "clicks": 1},
            {"campaign_id": 1, "clicks": 2},
            {"campaign_id": 2, "clicks": 3},
            {"campaign_id": 2, "clicks": 4},
        ]

        rows = api_breakdowns.query(
            ["campaign_id"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            None,
            Goals(None, None, None, None, None),
            "-clicks",
            1,
            1,
            False,
        )

        # offset and limit are applied directly to sql queries and so they don't
        # have an effect to the returned result here
        self.assertCountEqual(
            rows,
            [
                {"campaign_id": 2, "clicks": 4},
                {"campaign_id": 2, "clicks": 3},
                {"campaign_id": 1, "clicks": 2},
                {"campaign_id": 1, "clicks": 1},
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=False)
    @patch("redshiftapi.db.execute_query")
    def test_query_joint_levels(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "ad_group_id": 1, "dma": 501, "clicks": 1},
            {"campaign_id": 1, "ad_group_id": 1, "dma": 502, "clicks": 2},
            {"campaign_id": 1, "ad_group_id": 2, "dma": 501, "clicks": 3},
            {"campaign_id": 1, "ad_group_id": 2, "dma": 502, "clicks": 4},
            {"campaign_id": 2, "ad_group_id": 3, "dma": 501, "clicks": 5},
            {"campaign_id": 2, "ad_group_id": 3, "dma": 502, "clicks": 6},
            {"campaign_id": 2, "ad_group_id": 4, "dma": 501, "clicks": 7},
            {"campaign_id": 2, "ad_group_id": 4, "dma": 502, "clicks": 8},
        ]

        rows = api_breakdowns.query(
            ["campaign_id", "ad_group_id", "dma"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            [
                {"campaign_id": 1, "ad_group_id": 1},
                {"campaign_id": 1, "ad_group_id": 2},
                {"campaign_id": 2, "ad_group_id": 3},
                {"campaign_id": 2, "ad_group_id": 4},
            ],
            Goals(None, None, None, None, None),
            "clicks",
            1,
            1,
            False,
        )

        # offset and limit are applied directly to sql queries and so they don't
        # have an effect to the returned result here
        self.assertCountEqual(
            rows,
            [
                {"campaign_id": 1, "ad_group_id": 1, "dma": 501, "clicks": 1},
                {"campaign_id": 1, "ad_group_id": 1, "dma": 502, "clicks": 2},
                {"campaign_id": 1, "ad_group_id": 2, "dma": 501, "clicks": 3},
                {"campaign_id": 1, "ad_group_id": 2, "dma": 502, "clicks": 4},
                {"campaign_id": 2, "ad_group_id": 3, "dma": 501, "clicks": 5},
                {"campaign_id": 2, "ad_group_id": 3, "dma": 502, "clicks": 6},
                {"campaign_id": 2, "ad_group_id": 4, "dma": 501, "clicks": 7},
                {"campaign_id": 2, "ad_group_id": 4, "dma": 502, "clicks": 8},
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=False)
    @patch("redshiftapi.db.execute_query")
    def test_remove_postclicks(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "ad_group_id": 1, "dma": 501, "clicks": 1, "new_users": 1},
            {"campaign_id": 1, "ad_group_id": 1, "dma": 502, "clicks": 2, "new_users": 1},
            {"campaign_id": 1, "ad_group_id": 2, "dma": 501, "clicks": 3, "new_users": 1},
            {"campaign_id": 1, "ad_group_id": 2, "dma": 502, "clicks": 4, "new_users": 1},
            {"campaign_id": 2, "ad_group_id": 3, "dma": 501, "clicks": 5, "new_users": 1},
            {"campaign_id": 2, "ad_group_id": 3, "dma": 502, "clicks": 6, "new_users": 1},
            {"campaign_id": 2, "ad_group_id": 4, "dma": 501, "clicks": 7, "new_users": 1},
            {"campaign_id": 2, "ad_group_id": 4, "dma": 502, "clicks": 8, "new_users": 1},
        ]

        rows = api_breakdowns.query(
            ["campaign_id", "ad_group_id", "dma"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            [
                {"campaign_id": 1, "ad_group_id": 1},
                {"campaign_id": 1, "ad_group_id": 2},
                {"campaign_id": 2, "ad_group_id": 3},
                {"campaign_id": 2, "ad_group_id": 4},
            ],
            Goals(None, None, None, None, None),
            "clicks",
            0,
            10,
            False,
        )

        self.assertCountEqual(
            rows,
            [
                {"campaign_id": 1, "ad_group_id": 1, "dma": 501, "clicks": 1, "new_users": None},  # noqa
                {"campaign_id": 1, "ad_group_id": 1, "dma": 502, "clicks": 2, "new_users": None},  # noqa
                {"campaign_id": 1, "ad_group_id": 2, "dma": 501, "clicks": 3, "new_users": None},  # noqa
                {"campaign_id": 1, "ad_group_id": 2, "dma": 502, "clicks": 4, "new_users": None},  # noqa
                {"campaign_id": 2, "ad_group_id": 3, "dma": 501, "clicks": 5, "new_users": None},  # noqa
                {"campaign_id": 2, "ad_group_id": 3, "dma": 502, "clicks": 6, "new_users": None},  # noqa
                {"campaign_id": 2, "ad_group_id": 4, "dma": 501, "clicks": 7, "new_users": None},  # noqa
                {"campaign_id": 2, "ad_group_id": 4, "dma": 502, "clicks": 8, "new_users": None},  # noqa
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=False)
    @patch("redshiftapi.db.execute_query")
    def test_postprocess_time(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "day": datetime.date(2016, 10, 1), "clicks": 1},
            {"campaign_id": 1, "day": datetime.date(2016, 10, 3), "clicks": 3},
        ]

        rows = api_breakdowns.query(
            ["campaign_id", "day"],
            {
                "date__gte": datetime.date(2016, 9, 30),
                "date__lte": datetime.date(2016, 10, 10),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            [{"campaign_id": 1}],
            Goals(None, None, None, None, None),
            "-clicks",
            0,
            5,
            False,
        )

        self.assertEqual(
            rows,
            [
                {"campaign_id": 1, "day": datetime.date(2016, 10, 3), "clicks": 3},  # noqa
                {"campaign_id": 1, "day": datetime.date(2016, 10, 1), "clicks": 1},  # noqa
                {"campaign_id": 1, "day": datetime.date(2016, 9, 30)},
                {"campaign_id": 1, "day": datetime.date(2016, 10, 2)},
                {"campaign_id": 1, "day": datetime.date(2016, 10, 4)},
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=False)
    @patch("redshiftapi.db.execute_query")
    def test_postprocess_time_offset(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "day": datetime.date(2016, 10, 1), "clicks": 1},
            {"campaign_id": 1, "day": datetime.date(2016, 10, 3), "clicks": 3},
        ]

        rows = api_breakdowns.query(
            ["campaign_id", "day"],
            {
                "date__gte": datetime.date(2016, 9, 30),
                "date__lte": datetime.date(2016, 10, 10),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            [{"campaign_id": 1}],
            Goals(None, None, None, None, None),
            "-clicks",
            1,
            3,
            False,
        )

        self.assertEqual(
            rows,
            [
                {"campaign_id": 1, "day": datetime.date(2016, 10, 3), "clicks": 3},  # noqa
                {"campaign_id": 1, "day": datetime.date(2016, 10, 1), "clicks": 1},  # noqa
                {"campaign_id": 1, "day": datetime.date(2016, 10, 2)},
            ],
        )


class QueryStatsForRowsTestCase(TestCase):
    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=True)
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_all_base(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "clicks": 1},
            {"campaign_id": 2, "clicks": 2},
            {"campaign_id": 4, "clicks": 4},
        ]

        rows = api_breakdowns.query_stats_for_rows(
            [{"campaign_id": 1}, {"campaign_id": 2}, {"campaign_id": 3}],
            ["campaign_id"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            Goals(None, None, None, None, None),
            False,
        )

        self.assertCountEqual(rows, [{"campaign_id": 1, "clicks": 1}, {"campaign_id": 2, "clicks": 2}])

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=True)
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_all_depth_2(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "ad_group_id": 1, "clicks": 1},
            {"campaign_id": 1, "ad_group_id": 2, "clicks": 2},
            {"campaign_id": 2, "ad_group_id": 3, "clicks": 3},
            {"campaign_id": 2, "ad_group_id": 4, "clicks": 4},
            {"campaign_id": 3, "ad_group_id": 5, "clicks": 5},
        ]

        rows = api_breakdowns.query_stats_for_rows(
            [
                {"campaign_id": 1, "ad_group_id": 1},
                {"campaign_id": 2, "ad_group_id": 3},
                {"campaign_id": 2, "ad_group_id": 4},
                {"campaign_id": 4, "ad_group_id": 6},
            ],
            ["campaign_id", "ad_group_id"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            Goals(None, None, None, None, None),
            False,
        )

        self.assertCountEqual(
            rows,
            [
                {"campaign_id": 1, "ad_group_id": 1, "clicks": 1},
                {"campaign_id": 2, "ad_group_id": 3, "clicks": 3},
                {"campaign_id": 2, "ad_group_id": 4, "clicks": 4},
            ],
        )

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=False)
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_only_relevant_depth_1(self, mock_query, _):
        mock_query.return_value = [{"campaign_id": 1, "clicks": 1}, {"campaign_id": 2, "clicks": 2}]

        rows = api_breakdowns.query_stats_for_rows(
            [{"campaign_id": 1}, {"campaign_id": 2}, {"campaign_id": 3}],
            ["campaign_id"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            Goals(None, None, None, None, None),
            False,
        )

        self.assertCountEqual(rows, [{"campaign_id": 1, "clicks": 1}, {"campaign_id": 2, "clicks": 2}])

    @patch("redshiftapi.api_breakdowns._should_query_all", return_value=True)
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_only_relevant_depth_2(self, mock_query, _):
        mock_query.return_value = [
            {"campaign_id": 1, "ad_group_id": 1, "clicks": 1},
            {"campaign_id": 2, "ad_group_id": 3, "clicks": 3},
            {"campaign_id": 2, "ad_group_id": 4, "clicks": 4},
        ]

        rows = api_breakdowns.query_stats_for_rows(
            [
                {"campaign_id": 1, "ad_group_id": 1},
                {"campaign_id": 2, "ad_group_id": 3},
                {"campaign_id": 2, "ad_group_id": 4},
                {"campaign_id": 4, "ad_group_id": 6},
            ],
            ["campaign_id", "ad_group_id"],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            Goals(None, None, None, None, None),
            False,
        )

        self.assertCountEqual(
            rows,
            [
                {"campaign_id": 1, "ad_group_id": 1, "clicks": 1},
                {"campaign_id": 2, "ad_group_id": 3, "clicks": 3},
                {"campaign_id": 2, "ad_group_id": 4, "clicks": 4},
            ],
        )


class QueryTotalsTestCase(TestCase):
    @patch("redshiftapi.api_breakdowns._query_all")
    def test_query_totals(self, mock_query):
        mock_query.return_value = [{"clicks": 4}]

        rows = api_breakdowns.query_totals(
            [],
            {
                "date__lte": datetime.date(2016, 10, 1),
                "date__gte": datetime.date(2016, 9, 1),
                "account_id": 1,
                "campaign_id": [1, 2, 3],
                "ad_group_id": [1, 2, 3, 4, 5],
            },
            Goals(None, None, None, None, None),
            False,
        )

        self.assertCountEqual(rows, [{"clicks": 4}])


class QueryCountsTestCase(TestCase):
    @patch("redshiftapi.db.execute_query")
    def test_query_counts(self, mock_query):
        mock_query.return_value = [{"account_id": 1, "count": 3}, {"account_id": 2, "count": 7}]

        rows = api_breakdowns.query_counts(
            ["account_id", "country"],
            {"date__gte": datetime.date(2016, 9, 30), "date__lte": datetime.date(2016, 10, 10)},
            [{"account_id": 1}, {"account_id": 2}],
            False,
        )

        mock_query.assert_called_once_with(
            ANY,
            [datetime.date(2016, 9, 30), datetime.date(2016, 10, 10), [1, 2]],
            "account_id__country__counts_base",
            temp_tables=set(),
        )

        self.assertEqual(rows, [{"account_id": 1, "count": 3}, {"account_id": 2, "count": 7}])
