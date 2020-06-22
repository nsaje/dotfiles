import mock
from django.test import TestCase

import core.features.goals
import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from ... import config
from ... import constants
from ... import models
from .. import helpers
from . import stats


@mock.patch("redshiftapi.api_rules.query_conversions")
@mock.patch("redshiftapi.api_rules.query")
class QueryStatsTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.request = magic_mixer.blend_request_user()
        self.conversion_goal = magic_mixer.blend(
            core.features.goals.ConversionGoal,
            type=dash.constants.ConversionGoalType.PIXEL,
            pixel__slug="testslug",
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
        self.campaign_goal = core.features.goals.CampaignGoal.objects.create(
            self.request,
            campaign=self.campaign,
            conversion_goal=self.conversion_goal,
            goal_type=dash.constants.CampaignGoalKPI.CPA,
            value=100,
            primary=True,
        )

        self.rule = magic_mixer.blend(models.Rule, ad_groups_included=[self.ad_group])

        self.raw_stats = [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "local_etfm_cost": 100,
                "etfm_cpc": 0.2,
                "etfm_cpm": 0.3,
            }
        ]
        self.conversion_stats = [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_1_DAY,
                "count": 100,
                "count_view": 250,
            }
        ]

    def test_query_stats(self, mock_query, mock_query_conversions):
        mock_query.return_value = self.raw_stats
        mock_query_conversions.return_value = self.conversion_stats

        result = stats.query_stats(constants.TargetType.PUBLISHER, helpers.get_rules_by_ad_group_map([self.rule]))
        self.assertEqual(
            {
                self.ad_group.id: {
                    "pub1.com__12": {
                        "local_etfm_cost": {constants.MetricWindow.LAST_3_DAYS: 100},
                        "etfm_cpc": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                        "etfm_cpm": {constants.MetricWindow.LAST_3_DAYS: 0.3},
                    }
                }
            },
            result,
        )

    def test_query_stats_add_missing_rows(self, mock_query, mock_query_conversions):
        active_ad = magic_mixer.blend(
            core.models.ContentAd,
            ad_group=self.ad_group,
            archived=False,
            state=dash.constants.ContentAdSourceState.ACTIVE,
        )

        mock_query.return_value = []
        mock_query_conversions.return_value = []

        result = stats.query_stats(constants.TargetType.AD, helpers.get_rules_by_ad_group_map([self.rule]))

        self.assertCountEqual([self.ad_group.id], result.keys())
        self.assertCountEqual([str(active_ad.id)], result[self.ad_group.id].keys())

        target_stats = result[self.ad_group.id][str(active_ad.id)]
        self.assertCountEqual(config.STATS_FIELDS_DEFAULTS.keys(), target_stats)
        for metric, value in config.STATS_FIELDS_DEFAULTS.items():
            for window_key in constants.MetricWindow.get_all():
                self.assertEqual(value, target_stats[metric][window_key])

    def test_query_stats_cpa_operand(self, mock_query, mock_query_conversions):
        mock_query.return_value = self.raw_stats
        mock_query_conversions.return_value = self.conversion_stats

        magic_mixer.blend(
            models.RuleCondition,
            rule=self.rule,
            left_operand_type=constants.MetricType.AVG_COST_PER_CONVERSION,
            right_operand_type=constants.ValueType.ABSOLUTE,
        )

        result = stats.query_stats(constants.TargetType.PUBLISHER, helpers.get_rules_by_ad_group_map([self.rule]))
        self.assertTrue("local_avg_etfm_cost_per_conversion" in result[self.ad_group.id]["pub1.com__12"])
        self.assertTrue("local_avg_etfm_cost_per_conversion_view" in result[self.ad_group.id]["pub1.com__12"])
        self.assertTrue("local_avg_etfm_cost_per_conversion_total" in result[self.ad_group.id]["pub1.com__12"])

    def test_query_stats_cpa_email_subject(self, mock_query, mock_query_conversions):
        mock_query.return_value = self.raw_stats
        mock_query_conversions.return_value = self.conversion_stats

        rule = magic_mixer.blend(
            models.Rule,
            ad_groups_included=[self.ad_group],
            action_type=constants.ActionType.SEND_EMAIL,
            send_email_subject="{AVG_COST_PER_CONVERSION_LAST_7_DAYS}",
        )
        magic_mixer.blend(
            models.RuleCondition,
            rule=rule,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            right_operand_type=constants.ValueType.ABSOLUTE,
        )

        result = stats.query_stats(constants.TargetType.PUBLISHER, helpers.get_rules_by_ad_group_map([rule]))
        self.assertTrue("local_avg_etfm_cost_per_conversion" in result[self.ad_group.id]["pub1.com__12"])
        self.assertTrue("local_avg_etfm_cost_per_conversion_view" in result[self.ad_group.id]["pub1.com__12"])
        self.assertTrue("local_avg_etfm_cost_per_conversion_total" in result[self.ad_group.id]["pub1.com__12"])

    def test_query_stats_cpa_email_body(self, mock_query, mock_query_conversions):
        mock_query.return_value = self.raw_stats
        mock_query_conversions.return_value = self.conversion_stats

        rule = magic_mixer.blend(
            models.Rule,
            ad_groups_included=[self.ad_group],
            action_type=constants.ActionType.SEND_EMAIL,
            send_email_body="{AVG_COST_PER_CONVERSION_LAST_7_DAYS}",
        )
        magic_mixer.blend(
            models.RuleCondition,
            rule=rule,
            left_operand_type=constants.MetricType.TOTAL_SPEND,
            right_operand_type=constants.ValueType.ABSOLUTE,
        )

        result = stats.query_stats(constants.TargetType.PUBLISHER, helpers.get_rules_by_ad_group_map([rule]))
        self.assertTrue("local_avg_etfm_cost_per_conversion" in result[self.ad_group.id]["pub1.com__12"])
        self.assertTrue("local_avg_etfm_cost_per_conversion_view" in result[self.ad_group.id]["pub1.com__12"])
        self.assertTrue("local_avg_etfm_cost_per_conversion_total" in result[self.ad_group.id]["pub1.com__12"])


class MergeTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.request = magic_mixer.blend_request_user()
        self.conversion_goal = magic_mixer.blend(
            core.features.goals.ConversionGoal,
            type=dash.constants.ConversionGoalType.PIXEL,
            pixel__slug="testslug",
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
        self.campaign_goal = core.features.goals.CampaignGoal.objects.create(
            self.request,
            campaign=self.campaign,
            conversion_goal=self.conversion_goal,
            goal_type=dash.constants.CampaignGoalKPI.CPA,
            value=100,
            primary=True,
        )
        self.raw_stats = [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "local_etfm_cost": 100,
            }
        ]
        self.conversion_stats = [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_1_DAY,
                "count": 100,
                "count_view": 250,
            }
        ]

    def test_merge(self):
        merged_rows = stats._merge(
            constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, self.conversion_stats
        )
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                    "conversions_click": 100,
                    "conversions_view": 250,
                    "conversions_total": 350,
                    "local_avg_etfm_cost_per_conversion": 1.0,
                    "local_avg_etfm_cost_per_conversion_view": 0.4,
                    "local_avg_etfm_cost_per_conversion_total": 0.2857142857142857,
                }
            ],
            merged_rows,
        )

    def test_non_primary_goal(self):
        core.features.goals.CampaignGoal.objects.create(
            self.request, campaign=self.campaign, goal_type=dash.constants.CampaignGoalKPI.CPC, value=50, primary=True
        )

        merged_rows = stats._merge(
            constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, self.conversion_stats
        )
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                    "conversions_click": 100,
                    "conversions_view": 250,
                    "conversions_total": 350,
                    "local_avg_etfm_cost_per_conversion": 1.0,
                    "local_avg_etfm_cost_per_conversion_view": 0.4,
                    "local_avg_etfm_cost_per_conversion_total": 0.2857142857142857,
                }
            ],
            merged_rows,
        )

    def test_conversion_window_1_day(self):
        conversion_stats = self.conversion_stats + [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_7_DAYS,
                "count": 175,
                "count_view": 350,
            },
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_30_DAYS,
                "count": 225,
                "count_view": 800,
            },
        ]

        merged_rows = stats._merge(constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, conversion_stats)
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                    "conversions_click": 100,
                    "conversions_view": 250,
                    "conversions_total": 350,
                    "local_avg_etfm_cost_per_conversion": 1.0,
                    "local_avg_etfm_cost_per_conversion_view": 0.4,
                    "local_avg_etfm_cost_per_conversion_total": 0.2857142857142857,
                }
            ],
            merged_rows,
        )

    def test_conversion_window_7_days(self):
        self.conversion_goal.conversion_window = dash.constants.ConversionWindows.LEQ_7_DAYS
        self.conversion_goal.save()

        conversion_stats = self.conversion_stats + [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_7_DAYS,
                "count": 175,
                "count_view": 350,
            },
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_30_DAYS,
                "count": 225,
                "count_view": 800,
            },
        ]

        merged_rows = stats._merge(constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, conversion_stats)
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                    "conversions_click": 275,
                    "conversions_view": 600,
                    "conversions_total": 875,
                    "local_avg_etfm_cost_per_conversion": 0.36363636363636365,
                    "local_avg_etfm_cost_per_conversion_view": 0.16666666666666666,
                    "local_avg_etfm_cost_per_conversion_total": 0.11428571428571428,
                }
            ],
            merged_rows,
        )

    def test_conversion_window_30_days(self):
        self.conversion_goal.conversion_window = dash.constants.ConversionWindows.LEQ_30_DAYS
        self.conversion_goal.save()

        conversion_stats = self.conversion_stats + [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_7_DAYS,
                "count": 175,
                "count_view": 350,
            },
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_30_DAYS,
                "count": 225,
                "count_view": 800,
            },
        ]

        merged_rows = stats._merge(constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, conversion_stats)
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                    "conversions_click": 500,
                    "conversions_view": 1400,
                    "conversions_total": 1900,
                    "local_avg_etfm_cost_per_conversion": 0.2,
                    "local_avg_etfm_cost_per_conversion_view": 0.07142857142857142,
                    "local_avg_etfm_cost_per_conversion_total": 0.05263157894736842,
                }
            ],
            merged_rows,
        )

    def test_merge_no_pixel_rows(self):
        merged_rows = stats._merge(constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, [])
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                    "conversions_click": None,
                    "conversions_view": None,
                    "conversions_total": None,
                    "local_avg_etfm_cost_per_conversion": None,
                    "local_avg_etfm_cost_per_conversion_view": None,
                    "local_avg_etfm_cost_per_conversion_total": None,
                }
            ],
            merged_rows,
        )

    def test_no_cpa_goal(self):
        self.campaign_goal.type = dash.constants.CampaignGoalKPI.CPC
        self.campaign_goal.save()

        merged_rows = stats._merge(constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, [])
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                }
            ],
            merged_rows,
        )

    def test_ad_group_not_matching(self):
        self.raw_stats[0]["ad_group_id"] = self.ad_group.id + 1

        merged_rows = stats._merge(constants.TargetType.PUBLISHER, [self.ad_group], self.raw_stats, [])
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id + 1,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                }
            ],
            merged_rows,
        )

    def test_multiple_window_keys(self):
        raw_stats = [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "local_etfm_cost": 100,
            },
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "local_etfm_cost": 200,
            },
        ]

        conversion_stats = [
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_1_DAY,
                "count": 100,
                "count_view": 250,
            },
            {
                "ad_group_id": self.ad_group.id,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "slug": "testslug",
                "window": dash.constants.ConversionWindows.LEQ_1_DAY,
                "count": 200,
                "count_view": 500,
            },
        ]

        merged_rows = stats._merge(constants.TargetType.PUBLISHER, [self.ad_group], raw_stats, conversion_stats)
        self.assertEqual(
            [
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_3_DAYS,
                    "local_etfm_cost": 100,
                    "conversions_click": 100,
                    "conversions_view": 250,
                    "conversions_total": 350,
                    "local_avg_etfm_cost_per_conversion": 1.0,
                    "local_avg_etfm_cost_per_conversion_view": 0.4,
                    "local_avg_etfm_cost_per_conversion_total": 0.2857142857142857,
                },
                {
                    "ad_group_id": self.ad_group.id,
                    "source_id": 12,
                    "publisher": "pub1.com",
                    "window_key": constants.MetricWindow.LAST_7_DAYS,
                    "local_etfm_cost": 200,
                    "conversions_click": 200,
                    "conversions_view": 500,
                    "conversions_total": 700,
                    "local_avg_etfm_cost_per_conversion": 1.0,
                    "local_avg_etfm_cost_per_conversion_view": 0.4,
                    "local_avg_etfm_cost_per_conversion_total": 0.2857142857142857,
                },
            ],
            sorted(merged_rows, key=lambda x: x["window_key"]),
        )


class FormatTest(TestCase):
    def test_format_publisher_stats(self):
        target_type = constants.TargetType.PUBLISHER
        raw_stats = [
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "etfm_cpc": 0.5,
                "etfm_cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "etfm_cpc": 0.3,
                "etfm_cpm": 0.1,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "etfm_cpc": 0.5,
                "etfm_cpm": 0.2,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LIFETIME,
                "etfm_cpc": None,
                "etfm_cpm": 0.8,
            },
            {
                "ad_group_id": 321,
                "source_id": 32,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "etfm_cpc": 0.1,
                "etfm_cpm": 0.2,
            },
            {
                "ad_group_id": 321,
                "source_id": 21,
                "publisher": "pub3.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "etfm_cpc": 0.2,
                "etfm_cpm": 0.1,
            },
            {
                "ad_group_id": None,
                "source_id": 12,
                "publisher": "pub4.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": None,
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
            {
                "ad_group_id": 123,
                "source_id": None,
                "publisher": "pub4.com",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
            {
                "ad_group_id": 321,
                "source_id": 12,
                "publisher": "pub5",
                "window_key": None,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
            {
                "ad_group_id": 321,
                "publisher": "pub5",
                "window_key": constants.MetricWindow.LAST_DAY,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
        ]
        formatted_stats = stats._format(target_type, raw_stats)
        self.assertEqual(
            {
                123: {
                    "pub1.com__12": {
                        "etfm_cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "etfm_cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    },
                    "pub2.com__12": {
                        "etfm_cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "etfm_cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    },
                },
                321: {
                    "pub1.com__32": {
                        "etfm_cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "etfm_cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    },
                    "pub3.com__21": {
                        "etfm_cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "etfm_cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    },
                },
            },
            formatted_stats,
        )

    def test_format_ad_group_stats(self):
        target_type = constants.TargetType.AD_GROUP
        raw_stats = [
            {"ad_group_id": 123, "window_key": constants.MetricWindow.LAST_3_DAYS, "etfm_cpc": 0.5, "etfm_cpm": 0.7},
            {"ad_group_id": 123, "window_key": constants.MetricWindow.LAST_30_DAYS, "etfm_cpc": 0.3, "etfm_cpm": 0.1},
            {"ad_group_id": 111, "window_key": constants.MetricWindow.LAST_DAY, "etfm_cpc": 0.5, "etfm_cpm": 0.2},
            {"ad_group_id": 111, "window_key": constants.MetricWindow.LIFETIME, "etfm_cpc": None, "etfm_cpm": 0.8},
            {"ad_group_id": 321, "window_key": constants.MetricWindow.LAST_3_DAYS, "etfm_cpc": 0.1, "etfm_cpm": 0.2},
            {"ad_group_id": 222, "window_key": constants.MetricWindow.LAST_DAY, "etfm_cpc": 0.2, "etfm_cpm": 0.1},
            {"ad_group_id": None, "window_key": constants.MetricWindow.LAST_3_DAYS, "etfm_cpc": 0.7, "etfm_cpm": 0.9},
            {"ad_group_id": 333, "window_key": None, "etfm_cpc": 0.7, "etfm_cpm": 0.9},
        ]
        formatted_stats = stats._format(target_type, raw_stats)
        self.assertEqual(
            {
                123: {
                    "123": {
                        "etfm_cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "etfm_cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    }
                },
                111: {
                    "111": {
                        "etfm_cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "etfm_cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    }
                },
                321: {
                    "321": {
                        "etfm_cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "etfm_cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    }
                },
                222: {
                    "222": {
                        "etfm_cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "etfm_cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    }
                },
            },
            formatted_stats,
        )

    def test_format_stats(self):
        test_cases = {
            target_type: constants.TARGET_TYPE_STATS_MAPPING[target_type][0]
            for target_type in [
                constants.TargetType.AD,
                constants.TargetType.DEVICE,
                constants.TargetType.COUNTRY,
                constants.TargetType.STATE,
                constants.TargetType.DMA,
                constants.TargetType.OS,
                constants.TargetType.ENVIRONMENT,
                constants.TargetType.SOURCE,
            ]
        }

        for target_type, mv_column in test_cases.items():
            self._test_format_stats(target_type, mv_column)

    def _test_format_stats(self, target_type, mv_column):
        raw_stats = [
            {
                "ad_group_id": 123,
                mv_column: "12",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "etfm_cpc": 0.5,
                "etfm_cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                mv_column: "12",
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "etfm_cpc": 0.3,
                "etfm_cpm": 0.1,
            },
            {
                "ad_group_id": 111,
                mv_column: 12,
                "window_key": constants.MetricWindow.LAST_DAY,
                "etfm_cpc": 0.5,
                "etfm_cpm": 0.2,
            },
            {
                "ad_group_id": 111,
                mv_column: 12,
                "window_key": constants.MetricWindow.LIFETIME,
                "etfm_cpc": None,
                "etfm_cpm": 0.8,
            },
            {
                "ad_group_id": 321,
                mv_column: "32",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "etfm_cpc": 0.1,
                "etfm_cpm": 0.2,
            },
            {
                "ad_group_id": 321,
                mv_column: 21,
                "window_key": constants.MetricWindow.LAST_DAY,
                "etfm_cpc": 0.2,
                "etfm_cpm": 0.1,
            },
            {
                "ad_group_id": None,
                mv_column: "12",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
            {
                "ad_group_id": 123,
                mv_column: None,
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
            {
                "ad_group_id": 222,
                mv_column: "Other",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "etfm_cpc": 0.7,
                "etfm_cpm": 0.9,
            },
            {"ad_group_id": 321, mv_column: "12", "window_key": None, "etfm_cpc": 0.7, "etfm_cpm": 0.9},
            {"ad_group_id": 321, "window_key": constants.MetricWindow.LAST_DAY, "etfm_cpc": 0.7, "etfm_cpm": 0.9},
        ]
        formatted_stats = stats._format(target_type, raw_stats)
        self.assertEqual(
            {
                123: {
                    "12": {
                        "etfm_cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "etfm_cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    }
                },
                111: {
                    "12": {
                        "etfm_cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "etfm_cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    }
                },
                321: {
                    "32": {
                        "etfm_cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "etfm_cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    },
                    "21": {
                        "etfm_cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "etfm_cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    },
                },
            },
            formatted_stats,
        )


@mock.patch("automation.autopilot.recalculate_budgets_ad_group", mock.MagicMock())
class AddMissingTargetsTest(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)

    def test_add_missing_ad_group_targets(self):
        empty_stats = {}
        stats._add_missing_targets(constants.TargetType.AD_GROUP, [self.ad_group], empty_stats)

        self.assertCountEqual([self.ad_group.id], empty_stats.keys())
        self.assertCountEqual([str(self.ad_group.id)], empty_stats[self.ad_group.id].keys())
        self._assert_target_stats_defaults(empty_stats[self.ad_group.id][str(self.ad_group.id)])

    def test_add_missing_content_ad_targets(self):
        active_ad = magic_mixer.blend(
            core.models.ContentAd,
            ad_group=self.ad_group,
            archived=False,
            state=dash.constants.ContentAdSourceState.ACTIVE,
        )
        magic_mixer.blend(
            core.models.ContentAd, archived=False, state=dash.constants.ContentAdSourceState.ACTIVE
        )  # active ad another ad group
        magic_mixer.blend(
            core.models.ContentAd,
            ad_group=self.ad_group,
            archived=False,
            state=dash.constants.ContentAdSourceState.INACTIVE,
        )  # inactive ad
        magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group, archived=True)  # archived ad

        empty_stats = {}
        stats._add_missing_targets(constants.TargetType.AD, [self.ad_group], empty_stats)

        self.assertCountEqual([self.ad_group.id], empty_stats.keys())
        self.assertCountEqual([str(active_ad.id)], empty_stats[self.ad_group.id].keys())
        self._assert_target_stats_defaults(empty_stats[self.ad_group.id][str(active_ad.id)])

    def test_add_missing_source_targets(self):
        active_ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group)
        active_ad_group_source.settings.update(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

        active_ad_group_source_another_ad_group = magic_mixer.blend(core.models.AdGroupSource)
        active_ad_group_source_another_ad_group.settings.update(
            None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE
        )

        inactive_ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group)
        inactive_ad_group_source.settings.update(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)

        empty_stats = {}
        stats._add_missing_targets(constants.TargetType.SOURCE, [self.ad_group], empty_stats)

        self.assertCountEqual([self.ad_group.id], empty_stats.keys())
        self.assertCountEqual([str(active_ad_group_source.source_id)], empty_stats[self.ad_group.id].keys())
        self._assert_target_stats_defaults(empty_stats[self.ad_group.id][str(active_ad_group_source.source_id)])

    def test_add_missing_delivery_targets(self):
        for target_type in [
            constants.TargetType.PUBLISHER,
            constants.TargetType.DEVICE,
            constants.TargetType.COUNTRY,
            constants.TargetType.STATE,
            constants.TargetType.DMA,
            constants.TargetType.OS,
            constants.TargetType.ENVIRONMENT,
        ]:
            empty_stats = {}
            stats._add_missing_targets(target_type, [self.ad_group], empty_stats)
            self.assertEqual({}, empty_stats)

    def _assert_target_stats_defaults(self, target_stats):
        self.assertCountEqual(config.STATS_FIELDS_DEFAULTS.keys(), target_stats)
        for metric, value in config.STATS_FIELDS_DEFAULTS.items():
            for window_key in constants.MetricWindow.get_all():
                self.assertEqual(value, target_stats[metric][window_key])
