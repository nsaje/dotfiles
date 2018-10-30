import datetime

from django.test import TestCase

import dash.campaign_goals
import dash.constants
import dash.models
import stats.constants
from redshiftapi import postprocess


class PostprocessTest(TestCase):
    def test_get_representative_dates_days(self):
        constraints = {"date__gte": datetime.date(2016, 2, 2), "date__lte": datetime.date(2016, 2, 5)}

        dates = postprocess._get_representative_dates(stats.constants.TimeDimension.DAY, constraints)
        self.assertCountEqual(
            dates,
            [
                datetime.date(2016, 2, 2),
                datetime.date(2016, 2, 3),
                datetime.date(2016, 2, 4),
                datetime.date(2016, 2, 5),
            ],
        )

        constraints = {"date__gte": datetime.date(2016, 2, 2), "date__lt": datetime.date(2016, 2, 5)}

        dates = postprocess._get_representative_dates(stats.constants.TimeDimension.DAY, constraints)
        self.assertCountEqual(dates, [datetime.date(2016, 2, 2), datetime.date(2016, 2, 3), datetime.date(2016, 2, 4)])

    def test_get_representative_dates_weeks(self):
        constraints = {"date__gte": datetime.date(2016, 2, 2), "date__lte": datetime.date(2016, 2, 29)}

        dates = postprocess._get_representative_dates(stats.constants.TimeDimension.WEEK, constraints)
        self.assertCountEqual(
            dates,
            [
                datetime.date(2016, 2, 1),
                datetime.date(2016, 2, 8),
                datetime.date(2016, 2, 15),
                datetime.date(2016, 2, 22),
                datetime.date(2016, 2, 29),
            ],
        )

        constraints = {"date__gte": datetime.date(2016, 2, 2), "date__lt": datetime.date(2016, 2, 29)}

        dates = postprocess._get_representative_dates(stats.constants.TimeDimension.WEEK, constraints)
        self.assertCountEqual(
            dates,
            [
                datetime.date(2016, 2, 1),
                datetime.date(2016, 2, 8),
                datetime.date(2016, 2, 15),
                datetime.date(2016, 2, 22),
            ],
        )

    def test_get_representative_dates_months(self):
        constraints = {"date__gte": datetime.date(2016, 2, 2), "date__lte": datetime.date(2016, 4, 1)}

        dates = postprocess._get_representative_dates(stats.constants.TimeDimension.MONTH, constraints)
        self.assertCountEqual(dates, [datetime.date(2016, 2, 1), datetime.date(2016, 3, 1), datetime.date(2016, 4, 1)])

        constraints = {"date__gte": datetime.date(2016, 2, 2), "date__lt": datetime.date(2016, 4, 1)}

        dates = postprocess._get_representative_dates(stats.constants.TimeDimension.MONTH, constraints)
        self.assertCountEqual(dates, [datetime.date(2016, 2, 1), datetime.date(2016, 3, 1)])

    def test_postprocess_time_dimension(self):
        rows = []
        postprocess._fill_in_missing_rows_time_dimension(
            stats.constants.TimeDimension.DAY,
            rows,
            ["ad_group_id", "day"],
            {"date__gte": datetime.date(2016, 7, 1), "date__lte": datetime.date(2016, 7, 5)},
            [{"ad_group_id": 1}],
        )

        self.assertCountEqual(
            rows,
            [
                {"ad_group_id": 1, "day": datetime.date(2016, 7, 1)},
                {"ad_group_id": 1, "day": datetime.date(2016, 7, 2)},
                {"ad_group_id": 1, "day": datetime.date(2016, 7, 3)},
                {"ad_group_id": 1, "day": datetime.date(2016, 7, 4)},
                {"ad_group_id": 1, "day": datetime.date(2016, 7, 5)},
            ],
        )


class PostprocessGoalsTest(TestCase):
    fixtures = ["test_augmenter.yaml"]

    def setUp(self):
        self.maxDiff = None

    def test_apply_conversion_goal_columns(self):
        rows = [
            {
                "campaign_id": 1,
                "ad_group_id": 1,
                "clicks": 1,
                "e_media_cost": 10,
                "local_e_media_cost": 20,
                "media_cost": 10,
                "local_media_cost": 20,
                "etfm_cost": 10,
                "local_etfm_cost": 20,
                "et_cost": 10,
                "local_et_cost": 20,
            },
            {
                "campaign_id": 1,
                "ad_group_id": 2,
                "clicks": 1,
                "e_media_cost": 20,
                "local_e_media_cost": 40,
                "media_cost": 20,
                "local_media_cost": 40,
                "etfm_cost": 20,
                "local_etfm_cost": 40,
                "et_cost": 20,
                "local_et_cost": 40,
            },
        ]

        postprocess.apply_conversion_goal_columns(
            ["campaign_id", "ad_group_id"],
            rows,
            dash.models.ConversionGoal.objects.filter(campaign_id=1),
            [
                {"campaign_id": 1, "ad_group_id": 1, "slug": "ga__1", "count": 11},  # not the right type
                {"campaign_id": 1, "ad_group_id": 1, "slug": "ga__2", "count": 22},
                {"campaign_id": 1, "ad_group_id": 2, "slug": "ga__2", "count": 33},
                {"campaign_id": 1, "ad_group_id": 2, "slug": "ga__3", "count": 44},
            ],
        )

        self.assertEqual(
            rows,
            [
                {
                    "conversion_goal_2": 22,
                    "avg_cost_per_conversion_goal_2": 10.0 / 22,
                    "local_avg_cost_per_conversion_goal_2": 20.0 / 22,
                    "avg_et_cost_per_conversion_goal_2": 10.0 / 22,
                    "local_avg_et_cost_per_conversion_goal_2": 20.0 / 22,
                    "avg_etfm_cost_per_conversion_goal_2": 10.0 / 22,
                    "local_avg_etfm_cost_per_conversion_goal_2": 20.0 / 22,
                    "conversion_goal_3": None,
                    "avg_cost_per_conversion_goal_3": None,
                    "local_avg_cost_per_conversion_goal_3": None,
                    "avg_et_cost_per_conversion_goal_3": None,
                    "local_avg_et_cost_per_conversion_goal_3": None,
                    "avg_etfm_cost_per_conversion_goal_3": None,
                    "local_avg_etfm_cost_per_conversion_goal_3": None,
                    "conversion_goal_4": None,
                    "avg_cost_per_conversion_goal_4": None,
                    "local_avg_cost_per_conversion_goal_4": None,
                    "avg_et_cost_per_conversion_goal_4": None,
                    "local_avg_et_cost_per_conversion_goal_4": None,
                    "avg_etfm_cost_per_conversion_goal_4": None,
                    "local_avg_etfm_cost_per_conversion_goal_4": None,
                    "conversion_goal_5": None,
                    "avg_cost_per_conversion_goal_5": None,
                    "local_avg_cost_per_conversion_goal_5": None,
                    "avg_et_cost_per_conversion_goal_5": None,
                    "local_avg_et_cost_per_conversion_goal_5": None,
                    "avg_etfm_cost_per_conversion_goal_5": None,
                    "local_avg_etfm_cost_per_conversion_goal_5": None,
                    "campaign_id": 1,
                    "ad_group_id": 1,
                    "clicks": 1,
                    "e_media_cost": 10,
                    "local_e_media_cost": 20,
                    "et_cost": 10,
                    "local_et_cost": 20,
                    "etfm_cost": 10,
                    "local_etfm_cost": 20,
                    "media_cost": 10,
                    "local_media_cost": 20,
                },
                {
                    "conversion_goal_2": 33,
                    "avg_cost_per_conversion_goal_2": 20.0 / 33,
                    "local_avg_cost_per_conversion_goal_2": 40.0 / 33,
                    "avg_et_cost_per_conversion_goal_2": 20.0 / 33,
                    "local_avg_et_cost_per_conversion_goal_2": 40.0 / 33,
                    "avg_etfm_cost_per_conversion_goal_2": 20.0 / 33,
                    "local_avg_etfm_cost_per_conversion_goal_2": 40.0 / 33,
                    "conversion_goal_3": 44,
                    "avg_cost_per_conversion_goal_3": 20.0 / 44,
                    "local_avg_cost_per_conversion_goal_3": 40.0 / 44,
                    "avg_et_cost_per_conversion_goal_3": 20.0 / 44,
                    "local_avg_et_cost_per_conversion_goal_3": 40.0 / 44,
                    "avg_etfm_cost_per_conversion_goal_3": 20.0 / 44,
                    "local_avg_etfm_cost_per_conversion_goal_3": 40.0 / 44,
                    "conversion_goal_4": None,
                    "avg_cost_per_conversion_goal_4": None,
                    "local_avg_cost_per_conversion_goal_4": None,
                    "avg_et_cost_per_conversion_goal_4": None,
                    "local_avg_et_cost_per_conversion_goal_4": None,
                    "avg_etfm_cost_per_conversion_goal_4": None,
                    "local_avg_etfm_cost_per_conversion_goal_4": None,
                    "conversion_goal_5": None,
                    "avg_cost_per_conversion_goal_5": None,
                    "local_avg_cost_per_conversion_goal_5": None,
                    "avg_et_cost_per_conversion_goal_5": None,
                    "local_avg_et_cost_per_conversion_goal_5": None,
                    "avg_etfm_cost_per_conversion_goal_5": None,
                    "local_avg_etfm_cost_per_conversion_goal_5": None,
                    "campaign_id": 1,
                    "ad_group_id": 2,
                    "clicks": 1,
                    "e_media_cost": 20,
                    "local_e_media_cost": 40,
                    "etfm_cost": 20,
                    "local_etfm_cost": 40,
                    "et_cost": 20,
                    "local_et_cost": 40,
                    "media_cost": 20,
                    "local_media_cost": 40,
                },
            ],
        )

    def test_apply_conversion_goal_columns_totals(self):
        rows = [
            {
                "clicks": 1,
                "e_media_cost": 10,
                "local_e_media_cost": 20,
                "media_cost": 10,
                "local_media_cost": 20,
                "etfm_cost": 10,
                "local_etfm_cost": 20,
                "et_cost": 10,
                "local_et_cost": 20,
            }
        ]

        postprocess.apply_conversion_goal_columns(
            [],
            rows,
            dash.models.ConversionGoal.objects.filter(campaign_id=1),
            [
                {"slug": "ga__1", "count": 11},  # not the right type
                {"slug": "ga__2", "count": 22},
                {"slug": "ga__3", "count": 44},
            ],
        )

        self.assertEqual(
            rows,
            [
                {
                    "conversion_goal_2": 22,
                    "avg_cost_per_conversion_goal_2": 10.0 / 22,
                    "local_avg_cost_per_conversion_goal_2": 20.0 / 22,
                    "avg_et_cost_per_conversion_goal_2": 10.0 / 22,
                    "local_avg_et_cost_per_conversion_goal_2": 20.0 / 22,
                    "avg_etfm_cost_per_conversion_goal_2": 10.0 / 22,
                    "local_avg_etfm_cost_per_conversion_goal_2": 20.0 / 22,
                    "conversion_goal_3": 44,
                    "avg_cost_per_conversion_goal_3": 10.0 / 44,
                    "local_avg_cost_per_conversion_goal_3": 20.0 / 44,
                    "avg_et_cost_per_conversion_goal_3": 10.0 / 44,
                    "local_avg_et_cost_per_conversion_goal_3": 20.0 / 44,
                    "avg_etfm_cost_per_conversion_goal_3": 10.0 / 44,
                    "local_avg_etfm_cost_per_conversion_goal_3": 20.0 / 44,
                    "conversion_goal_4": None,
                    "avg_cost_per_conversion_goal_4": None,
                    "local_avg_cost_per_conversion_goal_4": None,
                    "avg_et_cost_per_conversion_goal_4": None,
                    "local_avg_et_cost_per_conversion_goal_4": None,
                    "avg_etfm_cost_per_conversion_goal_4": None,
                    "local_avg_etfm_cost_per_conversion_goal_4": None,
                    "conversion_goal_5": None,
                    "avg_cost_per_conversion_goal_5": None,
                    "local_avg_cost_per_conversion_goal_5": None,
                    "avg_et_cost_per_conversion_goal_5": None,
                    "local_avg_et_cost_per_conversion_goal_5": None,
                    "avg_etfm_cost_per_conversion_goal_5": None,
                    "local_avg_etfm_cost_per_conversion_goal_5": None,
                    "clicks": 1,
                    "e_media_cost": 10,
                    "local_e_media_cost": 20,
                    "media_cost": 10,
                    "local_media_cost": 20,
                    "et_cost": 10,
                    "local_et_cost": 20,
                    "etfm_cost": 10,
                    "local_etfm_cost": 20,
                }
            ],
        )

    def test_apply_apply_pixel_columns(self):
        rows = [
            {
                "campaign_id": 1,
                "ad_group_id": 1,
                "clicks": 1,
                "e_media_cost": 10,
                "local_e_media_cost": 20,
                "media_cost": 10,
                "local_media_cost": 20,
                "etfm_cost": 10,
                "local_etfm_cost": 20,
                "et_cost": 10,
                "local_et_cost": 20,
            },
            {
                "campaign_id": 1,
                "ad_group_id": 2,
                "clicks": 1,
                "e_media_cost": 20,
                "local_e_media_cost": 40,
                "media_cost": 20,
                "local_media_cost": 40,
                "etfm_cost": 20,
                "local_etfm_cost": 40,
                "et_cost": 20,
                "local_et_cost": 40,
            },
        ]

        postprocess.apply_pixel_columns(
            ["campaign_id", "ad_group_id"],
            rows,
            dash.models.ConversionPixel.objects.filter(account_id=1),
            [
                {
                    "campaign_id": 1,
                    "ad_group_id": 1,
                    "slug": "bla",
                    "window": 24,
                    "count": 11,
                    "conversion_value": 100.0,
                },  # does not exist
                {
                    "campaign_id": 1,
                    "ad_group_id": 1,
                    "slug": "test",
                    "window": 24,
                    "count": 22,
                    "conversion_value": 200.0,
                },
                {
                    "campaign_id": 1,
                    "ad_group_id": 2,
                    "slug": "test",
                    "window": 168,
                    "count": 33,
                    "conversion_value": 300.0,
                },
                {
                    "campaign_id": 1,
                    "ad_group_id": 2,
                    "slug": "test",
                    "window": 2160,
                    "count": 44,
                    "conversion_value": 400.0,
                },
            ],
        )

        self.assertEqual(
            rows,
            [
                {
                    "pixel_1_24": 22,
                    "avg_cost_per_pixel_1_24": 10.0 / 22,
                    "local_avg_cost_per_pixel_1_24": 20.0 / 22,
                    "avg_et_cost_per_pixel_1_24": 10.0 / 22,
                    "local_avg_et_cost_per_pixel_1_24": 20.0 / 22,
                    "avg_etfm_cost_per_pixel_1_24": 10.0 / 22,
                    "local_avg_etfm_cost_per_pixel_1_24": 20.0 / 22,
                    "roas_pixel_1_24": 200.0 - 20,
                    "etfm_roas_pixel_1_24": 200.0 - 20,
                    "pixel_1_168": 22,
                    "avg_cost_per_pixel_1_168": 10.0 / 22,
                    "local_avg_cost_per_pixel_1_168": 20.0 / 22,
                    "avg_et_cost_per_pixel_1_168": 10.0 / 22,
                    "local_avg_et_cost_per_pixel_1_168": 20.0 / 22,
                    "avg_etfm_cost_per_pixel_1_168": 10.0 / 22,
                    "local_avg_etfm_cost_per_pixel_1_168": 20.0 / 22,
                    "roas_pixel_1_168": 200.0 - 20,
                    "etfm_roas_pixel_1_168": 200.0 - 20,
                    "pixel_1_720": 22,
                    "avg_cost_per_pixel_1_720": 10.0 / 22,
                    "local_avg_cost_per_pixel_1_720": 20.0 / 22,
                    "avg_et_cost_per_pixel_1_720": 10.0 / 22,
                    "local_avg_et_cost_per_pixel_1_720": 20.0 / 22,
                    "avg_etfm_cost_per_pixel_1_720": 10.0 / 22,
                    "local_avg_etfm_cost_per_pixel_1_720": 20.0 / 22,
                    "roas_pixel_1_720": 200.0 - 20,
                    "etfm_roas_pixel_1_720": 200.0 - 20,
                    "pixel_1_2160": 22,
                    "avg_cost_per_pixel_1_2160": 10.0 / 22,
                    "local_avg_cost_per_pixel_1_2160": 20.0 / 22,
                    "avg_et_cost_per_pixel_1_2160": 10.0 / 22,
                    "local_avg_et_cost_per_pixel_1_2160": 20.0 / 22,
                    "avg_etfm_cost_per_pixel_1_2160": 10.0 / 22,
                    "local_avg_etfm_cost_per_pixel_1_2160": 20.0 / 22,
                    "roas_pixel_1_2160": 200.0 - 20,
                    "etfm_roas_pixel_1_2160": 200.0 - 20,
                    "ad_group_id": 1,
                    "campaign_id": 1,
                    "e_media_cost": 10,
                    "local_e_media_cost": 20,
                    "et_cost": 10,
                    "local_et_cost": 20,
                    "etfm_cost": 10,
                    "local_etfm_cost": 20,
                    "media_cost": 10,
                    "local_media_cost": 20,
                    "clicks": 1,
                },
                {
                    "pixel_1_24": 0,
                    "avg_cost_per_pixel_1_24": None,
                    "local_avg_cost_per_pixel_1_24": None,
                    "avg_et_cost_per_pixel_1_24": None,
                    "local_avg_et_cost_per_pixel_1_24": None,
                    "avg_etfm_cost_per_pixel_1_24": None,
                    "local_avg_etfm_cost_per_pixel_1_24": None,
                    "roas_pixel_1_24": -40,
                    "etfm_roas_pixel_1_24": -40,
                    "pixel_1_168": 33,
                    "avg_cost_per_pixel_1_168": 20.0 / 33,
                    "local_avg_cost_per_pixel_1_168": 40.0 / 33,
                    "avg_et_cost_per_pixel_1_168": 20.0 / 33,
                    "local_avg_et_cost_per_pixel_1_168": 40.0 / 33,
                    "avg_etfm_cost_per_pixel_1_168": 20.0 / 33,
                    "local_avg_etfm_cost_per_pixel_1_168": 40.0 / 33,
                    "roas_pixel_1_168": 300.0 - 40,
                    "etfm_roas_pixel_1_168": 300.0 - 40,
                    "pixel_1_720": 33,
                    "avg_cost_per_pixel_1_720": 20.0 / 33,
                    "local_avg_cost_per_pixel_1_720": 40.0 / 33,
                    "avg_et_cost_per_pixel_1_720": 20.0 / 33,
                    "local_avg_et_cost_per_pixel_1_720": 40.0 / 33,
                    "avg_etfm_cost_per_pixel_1_720": 20.0 / 33,
                    "local_avg_etfm_cost_per_pixel_1_720": 40.0 / 33,
                    "roas_pixel_1_720": 300.0 - 40,
                    "etfm_roas_pixel_1_720": 300.0 - 40,
                    "pixel_1_2160": 77,
                    "avg_cost_per_pixel_1_2160": 20.0 / 77,
                    "local_avg_cost_per_pixel_1_2160": 40.0 / 77,
                    "avg_et_cost_per_pixel_1_2160": 20.0 / 77,
                    "local_avg_et_cost_per_pixel_1_2160": 40.0 / 77,
                    "avg_etfm_cost_per_pixel_1_2160": 20.0 / 77,
                    "local_avg_etfm_cost_per_pixel_1_2160": 40.0 / 77,
                    "roas_pixel_1_2160": 700.0 - 40,
                    "etfm_roas_pixel_1_2160": 700.0 - 40,
                    "ad_group_id": 2,
                    "campaign_id": 1,
                    "e_media_cost": 20,
                    "local_e_media_cost": 40,
                    "et_cost": 20,
                    "local_et_cost": 40,
                    "etfm_cost": 20,
                    "local_etfm_cost": 40,
                    "media_cost": 20,
                    "local_media_cost": 40,
                    "clicks": 1,
                },
            ],
        )

    def test_apply_apply_pixel_columns_totals(self):
        rows = [
            {
                "clicks": 1,
                "e_media_cost": 10,
                "local_e_media_cost": 20,
                "media_cost": 10,
                "local_media_cost": 20,
                "etfm_cost": 10,
                "local_etfm_cost": 20,
                "et_cost": 10,
                "local_et_cost": 20,
            }
        ]

        postprocess.apply_pixel_columns(
            [],
            rows,
            dash.models.ConversionPixel.objects.filter(account_id=1),
            [
                {"slug": "bla", "window": 24, "count": 11, "conversion_value": 100.0},  # does not exist
                {"slug": "test", "window": 24, "count": 22, "conversion_value": 200.0},
                {"slug": "test", "window": 168, "count": 33, "conversion_value": 300.0},
                {"slug": "test", "window": 2160, "count": 44, "conversion_value": 400.0},
            ],
        )

        self.assertEqual(
            rows,
            [
                {
                    "pixel_1_24": 22,
                    "avg_cost_per_pixel_1_24": 10.0 / 22,
                    "local_avg_cost_per_pixel_1_24": 20.0 / 22,
                    "avg_et_cost_per_pixel_1_24": 10.0 / 22,
                    "local_avg_et_cost_per_pixel_1_24": 20.0 / 22,
                    "avg_etfm_cost_per_pixel_1_24": 10.0 / 22,
                    "local_avg_etfm_cost_per_pixel_1_24": 20.0 / 22,
                    "roas_pixel_1_24": 200.0 - 20,
                    "etfm_roas_pixel_1_24": 200.0 - 20,
                    "pixel_1_168": 55,
                    "avg_cost_per_pixel_1_168": 10.0 / 55,
                    "local_avg_cost_per_pixel_1_168": 20.0 / 55,
                    "avg_et_cost_per_pixel_1_168": 10.0 / 55,
                    "local_avg_et_cost_per_pixel_1_168": 20.0 / 55,
                    "avg_etfm_cost_per_pixel_1_168": 10.0 / 55,
                    "local_avg_etfm_cost_per_pixel_1_168": 20.0 / 55,
                    "roas_pixel_1_168": 500.0 - 20,
                    "etfm_roas_pixel_1_168": 500.0 - 20,
                    "pixel_1_720": 55,
                    "avg_cost_per_pixel_1_720": 10.0 / 55,
                    "local_avg_cost_per_pixel_1_720": 20.0 / 55,
                    "avg_et_cost_per_pixel_1_720": 10.0 / 55,
                    "local_avg_et_cost_per_pixel_1_720": 20.0 / 55,
                    "avg_etfm_cost_per_pixel_1_720": 10.0 / 55,
                    "local_avg_etfm_cost_per_pixel_1_720": 20.0 / 55,
                    "roas_pixel_1_720": 500.0 - 20,
                    "etfm_roas_pixel_1_720": 500.0 - 20,
                    "pixel_1_2160": 99,
                    "avg_cost_per_pixel_1_2160": 10.0 / 99,
                    "local_avg_cost_per_pixel_1_2160": 20.0 / 99,
                    "avg_et_cost_per_pixel_1_2160": 10.0 / 99,
                    "local_avg_et_cost_per_pixel_1_2160": 20.0 / 99,
                    "avg_etfm_cost_per_pixel_1_2160": 10.0 / 99,
                    "local_avg_etfm_cost_per_pixel_1_2160": 20.0 / 99,
                    "roas_pixel_1_2160": 900.0 - 20,
                    "etfm_roas_pixel_1_2160": 900.0 - 20,
                    "e_media_cost": 10,
                    "local_e_media_cost": 20,
                    "media_cost": 10,
                    "local_media_cost": 20,
                    "etfm_cost": 10,
                    "local_etfm_cost": 20,
                    "et_cost": 10,
                    "local_et_cost": 20,
                    "clicks": 1,
                }
            ],
        )

    def test_apply_performance_columns(self):
        rows = [
            {
                "campaign_id": 1,
                "ad_group_id": 1,
                "clicks": 1,
                "cpc": 0.45,
                "cpm": 1.45,
                "e_media_cost": 10,
                "media_cost": 10,
                "etfm_cost": 10,
                "conversion_goal_2": 22,
                "avg_cost_per_conversion_goal_2": 10.0 / 22,
                "conversion_goal_3": None,
                "avg_cost_per_conversion_goal_3": None,
                "conversion_goal_4": None,
                "avg_cost_per_conversion_goal_4": None,
                "conversion_goal_5": None,
                "avg_cost_per_conversion_goal_5": None,
                "pixel_1_24": 22,
                "avg_cost_per_pixel_1_24": 10.0 / 22,
                "pixel_1_168": 22,
                "avg_cost_per_pixel_1_168": 10.0 / 22,
                "pixel_1_720": 22,
                "avg_cost_per_pixel_1_720": 10.0 / 22,
                "pixel_1_2160": 22,
                "avg_cost_per_pixel_1_2160": 10.0 / 22,
            },
            {
                "campaign_id": 1,
                "ad_group_id": 2,
                "clicks": 1,
                "cpc": 0.56,
                "cpm": 1.56,
                "e_media_cost": 20,
                "media_cost": 20,
                "etfm_cost": 20,
                "conversion_goal_2": 33,
                "avg_cost_per_conversion_goal_2": 20.0 / 33,
                "conversion_goal_3": 44,
                "avg_cost_per_conversion_goal_3": 20.0 / 44,
                "conversion_goal_4": None,
                "avg_cost_per_conversion_goal_4": None,
                "conversion_goal_5": None,
                "avg_cost_per_conversion_goal_5": None,
                "pixel_1_24": 0,
                "avg_cost_per_pixel_1_24": None,
                "pixel_1_168": 5,
                "avg_cost_per_pixel_1_168": 20.0 / 5,
                "pixel_1_720": 5,
                "avg_cost_per_pixel_1_720": 20.0 / 5,
                "pixel_1_2160": 5,
                "avg_cost_per_pixel_1_2160": 20.0 / 5,
            },
        ]

        postprocess.apply_performance_columns(
            ["campaign_id", "ad_group_id"],
            rows,
            dash.models.CampaignGoal.objects.all(),
            dash.models.CampaignGoalValue.objects.all(),
            dash.models.ConversionGoal.objects.all(),
            dash.models.ConversionPixel.objects.all(),
        )

        self.assertEqual(
            rows,
            [
                {
                    "performance_campaign_goal_1": dash.constants.CampaignGoalPerformance.SUPERPERFORMING,
                    "etfm_performance_campaign_goal_1": dash.constants.CampaignGoalPerformance.SUPERPERFORMING,
                    "performance_campaign_goal_2": dash.constants.CampaignGoalPerformance.SUPERPERFORMING,
                    "etfm_performance_campaign_goal_2": dash.constants.CampaignGoalPerformance.SUPERPERFORMING,
                    "campaign_id": 1,
                    "ad_group_id": 1,
                    "clicks": 1,
                    "cpc": 0.45,
                    "cpm": 1.45,
                    "e_media_cost": 10,
                    "media_cost": 10,
                    "etfm_cost": 10,
                    "conversion_goal_2": 22,
                    "avg_cost_per_conversion_goal_2": 10.0 / 22,
                    "conversion_goal_3": None,
                    "avg_cost_per_conversion_goal_3": None,
                    "conversion_goal_4": None,
                    "avg_cost_per_conversion_goal_4": None,
                    "conversion_goal_5": None,
                    "avg_cost_per_conversion_goal_5": None,
                    "pixel_1_24": 22,
                    "avg_cost_per_pixel_1_24": 10.0 / 22,
                    "pixel_1_168": 22,
                    "avg_cost_per_pixel_1_168": 10.0 / 22,
                    "pixel_1_720": 22,
                    "avg_cost_per_pixel_1_720": 10.0 / 22,
                    "pixel_1_2160": 22,
                    "avg_cost_per_pixel_1_2160": 10.0 / 22,
                },
                {
                    "performance_campaign_goal_1": dash.constants.CampaignGoalPerformance.AVERAGE,
                    "etfm_performance_campaign_goal_1": dash.constants.CampaignGoalPerformance.AVERAGE,
                    "performance_campaign_goal_2": dash.constants.CampaignGoalPerformance.AVERAGE,
                    "etfm_performance_campaign_goal_2": dash.constants.CampaignGoalPerformance.AVERAGE,
                    "campaign_id": 1,
                    "ad_group_id": 2,
                    "clicks": 1,
                    "cpc": 0.56,
                    "cpm": 1.56,
                    "e_media_cost": 20,
                    "media_cost": 20,
                    "etfm_cost": 20,
                    "conversion_goal_2": 33,
                    "avg_cost_per_conversion_goal_2": 20.0 / 33,
                    "conversion_goal_3": 44,
                    "avg_cost_per_conversion_goal_3": 20.0 / 44,
                    "conversion_goal_4": None,
                    "avg_cost_per_conversion_goal_4": None,
                    "conversion_goal_5": None,
                    "avg_cost_per_conversion_goal_5": None,
                    "pixel_1_24": 0,
                    "avg_cost_per_pixel_1_24": None,
                    "pixel_1_168": 5,
                    "avg_cost_per_pixel_1_168": 20.0 / 5,
                    "pixel_1_720": 5,
                    "avg_cost_per_pixel_1_720": 20.0 / 5,
                    "pixel_1_2160": 5,
                    "avg_cost_per_pixel_1_2160": 20.0 / 5,
                },
            ],
        )
