import datetime
from decimal import Decimal

from django.http.request import HttpRequest
from django.test import TestCase
from mock import patch

from dash import campaign_goals
from dash import constants
from dash import history_helpers
from dash import infobox_helpers
from dash import models
from dash.constants import CampaignGoalPerformance as cgp
from zemauth.models import User


class CampaignGoalsTestCase(TestCase):
    fixtures = ["test_models.yaml"]

    def setUp(self):

        self.request = HttpRequest()
        self.request.user = User.objects.get(pk=1)
        self.campaign = models.Campaign.objects.get(pk=1)

        self.user = self.request.user

        all_goal_types = constants.CampaignGoalKPI.get_all()
        for i, goal_type in enumerate(all_goal_types):
            models.CampaignGoal.objects.create_unsafe(
                campaign=self.campaign, type=goal_type, primary=not i, created_by=self.user
            )

        cpa_goal = self._goal(constants.CampaignGoalKPI.CPA)
        conversion_goal = models.ConversionGoal.objects.create_unsafe(
            campaign=self.campaign, type=constants.ConversionGoalType.GA, name="test conversion goal", goal_id="123"
        )
        cpa_goal.conversion_goal = conversion_goal
        cpa_goal.save()

    def _goal(self, goal_type):
        return models.CampaignGoal.objects.filter(type=goal_type).first()

    def _add_value(self, goal_type, value):
        goal = self._goal(goal_type)
        models.CampaignGoalValue.objects.create(
            campaign_goal=goal, value=Decimal(value), local_value=Decimal(value), created_by=self.user
        )
        return goal

    def test_get_primary_campaign_goal(self):
        models.CampaignGoal.objects.all().delete()
        campaign = models.Campaign.objects.get(pk=1)
        self.assertTrue(campaign_goals.get_primary_campaign_goal(campaign) is None)

        models.CampaignGoal.objects.create_unsafe(type=1, campaign=campaign, primary=False)
        models.CampaignGoal.objects.create_unsafe(type=2, campaign=campaign, primary=True)
        self.assertEqual(campaign_goals.get_primary_campaign_goal(campaign).type, 2)

        models.CampaignGoal.objects.all().delete()
        models.CampaignGoal.objects.create_unsafe(type=1, campaign_id=2, primary=False)
        models.CampaignGoal.objects.create_unsafe(type=2, campaign_id=2, primary=True)
        self.assertTrue(campaign_goals.get_primary_campaign_goal(campaign) is None)

    def test_cpa_goal_primary(self):
        self._goal(constants.CampaignGoalKPI.CPA).set_primary(self.request)
        self.assertTrue(self._goal(constants.CampaignGoalKPI.CPA).primary)

        self.assertEqual(
            models.CampaignGoal.objects.filter(campaign=self.campaign, primary=True).get().type,
            constants.CampaignGoalKPI.CPA,
        )

        self._goal(constants.CampaignGoalKPI.PAGES_PER_SESSION).set_primary(self.request)
        self.assertFalse(self._goal(constants.CampaignGoalKPI.CPA).primary)
        self.assertTrue(self._goal(constants.CampaignGoalKPI.PAGES_PER_SESSION).primary)
        self.assertEqual(
            models.CampaignGoal.objects.filter(campaign=self.campaign, primary=True).get().type,
            constants.CampaignGoalKPI.PAGES_PER_SESSION,
        )

    def test_delete_campaign_goal(self):
        models.CampaignGoal.objects.all().delete()
        models.ConversionGoal.objects.all().delete()

        goal = models.CampaignGoal.objects.create_unsafe(type=1, primary=True, campaign_id=1)
        models.CampaignGoalValue.objects.create(value=Decimal("10"), campaign_goal=goal)

        campaign_goals.delete_campaign_goal(self.request, goal.pk, self.campaign)
        self.assertFalse(models.CampaignGoalValue.objects.all().count())
        self.assertFalse(models.CampaignGoal.objects.all().count())

        hist = history_helpers.get_campaign_history(self.campaign).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Deleted campaign goal "Time on Site - Seconds"')

        conv_goal = models.ConversionGoal.objects.create_unsafe(goal_id="123", name="123", type=3, campaign_id=1)
        goal = models.CampaignGoal.objects.create_unsafe(type=1, primary=True, campaign_id=1, conversion_goal=conv_goal)
        models.CampaignGoalValue.objects.create(value=Decimal("10"), campaign_goal=goal)

        campaign_goals.delete_campaign_goal(self.request, goal.pk, self.campaign)
        self.assertFalse(models.CampaignGoalValue.objects.all().count())
        self.assertFalse(models.CampaignGoal.objects.all().count())
        self.assertFalse(models.ConversionGoal.objects.all().count())

        hist = history_helpers.get_campaign_history(self.campaign).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Deleted conversion goal "123"')

    def test_get_campaign_goal_values(self):
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 1)
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 5)
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)

        values = campaign_goals.get_campaign_goal_values(self.campaign)
        self.assertEqual(75, values[0].value)

        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)

        values = campaign_goals.get_campaign_goal_values(self.campaign).values_list("value", flat=True)
        self.assertCountEqual([75, 5, 60], values)

    def test_get_campaign_goals(self):
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)
        self._add_value(constants.CampaignGoalKPI.CPV, 0.5)
        self._add_value(constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT, 2.25)
        self._add_value(constants.CampaignGoalKPI.CPA, 10)

        cam_goals = campaign_goals.get_campaign_goals(self.campaign, [])

        result = [
            {
                "name": "Time on Site - Seconds",
                "conversion": None,
                "value": 60,
                "fields": {"total_seconds": True, "avg_etfm_cost_per_minute": True},
                "primary": True,
            },
            {
                "name": "Pageviews per Visit",
                "conversion": None,
                "value": 5,
                "fields": {"total_pageviews": True, "avg_etfm_cost_per_pageview": True},
                "primary": False,
            },
            {
                "name": "Max Bounce Rate",
                "conversion": None,
                "value": 75,
                "fields": {"non_bounced_visits": True, "avg_etfm_cost_per_non_bounced_visit": True},
                "primary": False,
            },
            {
                "name": "Cost per Visit",
                "conversion": None,
                "value": 0.5,
                "fields": {"avg_etfm_cost_per_visit": True},
                "primary": False,
            },
            {"name": "Avg. CPA", "conversion": "test conversion goal", "value": 10, "fields": {}, "primary": False},
            {
                "name": "Cost per Non-Bounced Visit",
                "conversion": None,
                "value": 2.25,
                "fields": {"non_bounced_visits": True, "avg_etfm_cost_per_non_bounced_visit": True},
                "primary": False,
            },
        ]

        self.assertCountEqual(result, cam_goals)

    @patch("stats.api_breakdowns.totals")
    def test_get_goal_performance(self, mock_totals):
        start_date, end_date = datetime.date.today() - datetime.timedelta(7), datetime.date.today()

        goal_1 = self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)
        goal_2 = self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        goal_3 = self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)
        goal_4 = self._add_value(constants.CampaignGoalKPI.CPA, 10)
        goal_5 = self._add_value(constants.CampaignGoalKPI.CPV, 15)
        goal_6 = self._add_value(constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT, 2)
        goal_7 = self._goal(constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS)
        goal_8 = self._add_value(constants.CampaignGoalKPI.CPC, 0.02)
        goal_9 = self._add_value(constants.CampaignGoalKPI.CP_NEW_VISITOR, 3)
        goal_10 = self._add_value(constants.CampaignGoalKPI.CP_PAGE_VIEW, 4)
        goal_11 = self._add_value(constants.CampaignGoalKPI.CPCV, 0.01)

        mock_totals.return_value = {
            "etfm_cpc": 0.01,
            "conversion_goal_1": 10,
            "etfm_cost": 5,
            "bounce_rate": 10,
            "pv_per_visit": 10,
            "avg_tos": 10,
            "percent_new_users": 1.2,
            "avg_etfm_cost_per_visit": 35,
            "avg_etfm_cost_per_non_bounced_visit": 8,
            "avg_etfm_cost_for_new_visitor": 9,
            "avg_etfm_cost_per_pageview": 7,
            "video_etfm_cpcv": 6,
        }
        performance = campaign_goals.get_goals_performance_campaign(self.user, self.campaign, start_date, end_date)
        self.assertCountEqual(
            performance,
            [
                (cgp.SUPERPERFORMING, 10, Decimal("75.00000"), goal_1),
                (cgp.SUPERPERFORMING, 10, Decimal("5.00000"), goal_2),
                (cgp.UNDERPERFORMING, 10, Decimal("60.00000"), goal_3),
                (cgp.SUPERPERFORMING, 0.5, Decimal("10.00000"), goal_4),
                (cgp.UNDERPERFORMING, 35, Decimal("15.00000"), goal_5),
                (cgp.UNDERPERFORMING, 8, Decimal("2.00000"), goal_6),
                (cgp.AVERAGE, 1.2, None, goal_7),
                (cgp.SUPERPERFORMING, 0.01, Decimal("0.0200"), goal_8),
                (cgp.UNDERPERFORMING, 9, Decimal("3.0000"), goal_9),
                (cgp.UNDERPERFORMING, 7, Decimal("4.0000"), goal_10),
                (cgp.UNDERPERFORMING, 6, Decimal("0.0100"), goal_11),
            ],
        )

        mock_totals.return_value["conversion_goal_1"] = None
        mock_totals.return_value["etfm_cpc"] = Decimal("0.0001")  # check low numbers
        performance = campaign_goals.get_goals_performance_campaign(self.user, self.campaign, start_date, end_date)

        self.assertCountEqual(
            performance,
            [
                (cgp.SUPERPERFORMING, 10, Decimal("75.00000"), goal_1),
                (cgp.SUPERPERFORMING, 10, Decimal("5.00000"), goal_2),
                (cgp.UNDERPERFORMING, 10, Decimal("60.00000"), goal_3),
                (cgp.UNDERPERFORMING, None, Decimal("10.00000"), goal_4),
                (cgp.UNDERPERFORMING, 35, Decimal("15.00000"), goal_5),
                (cgp.UNDERPERFORMING, 8, Decimal("2.00000"), goal_6),
                (cgp.AVERAGE, 1.2, None, goal_7),
                (cgp.SUPERPERFORMING, Decimal("0.0001"), Decimal("0.0200"), goal_8),
                (cgp.UNDERPERFORMING, 9, Decimal("3.0000"), goal_9),
                (cgp.UNDERPERFORMING, 7, Decimal("4.0000"), goal_10),
                (cgp.UNDERPERFORMING, 6, Decimal("0.0100"), goal_11),
            ],
        )

    @patch("stats.api_breakdowns.totals")
    def test_infobox_campaign(self, mock_totals):
        start_date, end_date = datetime.date.today() - datetime.timedelta(7), datetime.date.today()

        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)
        self._add_value(constants.CampaignGoalKPI.CPA, 10)
        self._add_value(constants.CampaignGoalKPI.CPV, 15)
        self._add_value(constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT, 2)

        mock_totals.return_value = {
            "bounce_rate": 10,
            "total_pageviews": 10,
            "pv_per_visit": 10,
            "avg_tos": 10,
            "cpc": 0.1,
            "e_media_cost": 5,
            "percent_new_users": 1.2,
            "conversions": {"ga__123": 20.00},
            "avg_cost_per_visit": 35,
            "avg_cost_per_non_bounced_visit": 8,
        }

        goals_infobox = infobox_helpers.get_primary_campaign_goal(self.user, self.campaign, start_date, end_date)

        self.assertEqual(
            goals_infobox,
            [
                {
                    "section_start": True,
                    "internal": True,
                    "type": "setting",
                    "name": "Primary Goal:",
                    "value": "10.00 Time on Site - Seconds",
                    "icon": constants.Emoticon.SAD,
                    "description": "planned 60.00",
                }
            ],
        )

    @patch("stats.api_breakdowns.totals")
    def test_infobox_ad_group(self, mock_totals):
        start_date, end_date = datetime.date.today() - datetime.timedelta(7), datetime.date.today()

        ad_group = models.AdGroup.objects.filter(campaign=self.campaign)[0]

        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)
        self._add_value(constants.CampaignGoalKPI.CPA, 10)
        self._add_value(constants.CampaignGoalKPI.CPV, 15)
        self._add_value(constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT, 2)

        mock_totals.return_value = {
            "bounce_rate": 10,
            "total_pageviews": 10,
            "avg_tos": 10,
            "cpc": 0.1,
            "e_media_cost": 5,
            "pv_per_visit": 10,
            "percent_new_users": 1.2,
            "conversions": {"ga__123": 20.00},
            "avg_cost_per_visit": 10,
            "avg_cost_per_non_bounced_visit": 8,
        }

        goals_infobox = infobox_helpers.get_primary_campaign_goal(self.user, ad_group.campaign, start_date, end_date)
        self.assertEqual(
            goals_infobox,
            [
                {
                    "section_start": True,
                    "internal": True,
                    "type": "setting",
                    "name": "Primary Goal:",
                    "value": "10.00 Time on Site - Seconds",
                    "icon": constants.Emoticon.SAD,
                    "description": "planned 60.00",
                }
            ],
        )

    def test_get_performance_value(self):
        self.assertEqual(
            campaign_goals._get_performance_value(
                constants.CampaignGoalKPI.PAGES_PER_SESSION, Decimal("1"), Decimal("1")
            ),
            Decimal("1"),
        )
        self.assertEqual(
            campaign_goals._get_performance_value(
                constants.CampaignGoalKPI.PAGES_PER_SESSION, Decimal("1"), Decimal("1.1")
            ),
            Decimal("0.9090909090909090909090909091"),
        )
        self.assertEqual(
            campaign_goals._get_performance_value(
                constants.CampaignGoalKPI.PAGES_PER_SESSION, Decimal("0.5"), Decimal("1")
            ),
            Decimal("0.5"),
        )

        self.assertEqual(
            campaign_goals._get_performance_value(constants.CampaignGoalKPI.CPC, Decimal("1"), Decimal("1")),
            Decimal("1"),
        )
        self.assertEqual(
            campaign_goals._get_performance_value(constants.CampaignGoalKPI.CPC, Decimal("1.5"), Decimal("1")),
            Decimal("0.5"),
        )
        self.assertEqual(
            campaign_goals._get_performance_value(constants.CampaignGoalKPI.CPC, Decimal("0.5"), Decimal("1")),
            Decimal("1.5"),
        )

    def get_performance_value_rounding(self):
        self.assertEqual(
            campaign_goals._get_performance_value(constants.CampaignGoalKPI.CPC, Decimal("0.55"), Decimal("1")),
            campaign_goals._get_performance_value(constants.CampaignGoalKPI.CPC, Decimal("0.55555"), Decimal("1")),
        )
        self.assertEqual(
            campaign_goals._get_performance_value(constants.CampaignGoalKPI.CPC, Decimal("0.56"), Decimal("1")),
            campaign_goals._get_performance_value(constants.CampaignGoalKPI.CPC, Decimal("0.55655"), Decimal("1")),
        )

    def test_get_goal_performance_status(self):
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.PAGES_PER_SESSION, Decimal("1"), Decimal("1")
            ),
            constants.CampaignGoalPerformance.SUPERPERFORMING,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.PAGES_PER_SESSION, Decimal("1"), Decimal("1.1")
            ),
            constants.CampaignGoalPerformance.AVERAGE,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.PAGES_PER_SESSION, Decimal("0.5"), Decimal("1")
            ),
            constants.CampaignGoalPerformance.UNDERPERFORMING,
        )

        self.assertEqual(
            campaign_goals.get_goal_performance_status(constants.CampaignGoalKPI.CPC, Decimal("1"), Decimal("1")),
            constants.CampaignGoalPerformance.SUPERPERFORMING,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(constants.CampaignGoalKPI.CPC, Decimal("1.5"), Decimal("1")),
            constants.CampaignGoalPerformance.UNDERPERFORMING,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(constants.CampaignGoalKPI.CPC, Decimal("1.1"), Decimal("1")),
            constants.CampaignGoalPerformance.AVERAGE,
        )

    def test_get_goal_performance_status_cost_dependant(self):
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC, Decimal("1.1"), Decimal("1.0"), cost=Decimal("100000000")
            ),
            constants.CampaignGoalPerformance.AVERAGE,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC, None, Decimal("1.0"), cost=Decimal("100000000")
            ),
            constants.CampaignGoalPerformance.UNDERPERFORMING,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC, None, Decimal("1.0"), cost=None  # same as 0
            ),
            constants.CampaignGoalPerformance.AVERAGE,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC, None, Decimal("1.0"), cost=Decimal("0.000")
            ),
            constants.CampaignGoalPerformance.AVERAGE,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC, None, Decimal("1.0"), cost=Decimal("0.00001")  # should be rounded to 0
            ),
            constants.CampaignGoalPerformance.AVERAGE,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC, Decimal("0.009"), Decimal("0.350"), cost=Decimal("0.69")
            ),
            constants.CampaignGoalPerformance.SUPERPERFORMING,
        )

    def test_generate_series(self):
        campaign = models.Campaign.objects.get(pk=1)

        goal = models.CampaignGoal.objects.create_unsafe(
            type=constants.CampaignGoalKPI.MAX_BOUNCE_RATE,
            primary=False,
            campaign_id=1,
            created_dt=datetime.date(2016, 1, 5),
        )
        cgv1 = models.CampaignGoalValue.objects.create(campaign_goal=goal, value=Decimal(5), created_by=self.user)
        cgv1.created_dt = datetime.date(2016, 1, 5)
        cgv1.save()

        cgv2 = models.CampaignGoalValue.objects.create(campaign_goal=goal, value=Decimal(10), created_by=self.user)
        cgv2.created_dt = datetime.date(2016, 1, 10)
        cgv2.save()

        metrics_basic = campaign_goals.get_campaign_goal_metrics(
            campaign, datetime.date(2016, 1, 5), datetime.date(2016, 1, 10)
        )

        self.assertEqual(
            {
                constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.MAX_BOUNCE_RATE): [
                    [
                        (datetime.date(2016, 1, 5), 5.0),
                        (datetime.date(2016, 1, 6), 5.0),
                        (datetime.date(2016, 1, 7), 5.0),
                        (datetime.date(2016, 1, 8), 5.0),
                        (datetime.date(2016, 1, 9), 5.0),
                        (datetime.date(2016, 1, 10), 5.0),
                    ],
                    [(datetime.date(2016, 1, 10), 10.0), (datetime.date(2016, 1, 10), 10.0)],
                ]
            },
            metrics_basic,
        )

        metrics_basic_inner_1 = campaign_goals.get_campaign_goal_metrics(
            campaign, datetime.date(2016, 1, 6), datetime.date(2016, 1, 10)
        )

        self.assertEqual(
            {
                constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.MAX_BOUNCE_RATE): [
                    [
                        (datetime.date(2016, 1, 6), 5.0),
                        (datetime.date(2016, 1, 7), 5.0),
                        (datetime.date(2016, 1, 8), 5.0),
                        (datetime.date(2016, 1, 9), 5.0),
                        (datetime.date(2016, 1, 10), 5.0),
                    ],
                    [(datetime.date(2016, 1, 10), 10.0), (datetime.date(2016, 1, 10), 10.0)],
                ]
            },
            metrics_basic_inner_1,
        )

        metrics_basic_inner_2 = campaign_goals.get_campaign_goal_metrics(
            campaign, datetime.date(2016, 1, 6), datetime.date(2016, 1, 9)
        )

        self.assertEqual(
            {
                constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.MAX_BOUNCE_RATE): [
                    [
                        (datetime.date(2016, 1, 6), 5.0),
                        (datetime.date(2016, 1, 7), 5.0),
                        (datetime.date(2016, 1, 8), 5.0),
                        (datetime.date(2016, 1, 9), 5.0),
                    ]
                ]
            },
            metrics_basic_inner_2,
        )

        metrics_basic_cross_1 = campaign_goals.get_campaign_goal_metrics(
            campaign, datetime.date(2016, 1, 7), datetime.date(2016, 1, 12)
        )

        self.assertEqual(
            {
                constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.MAX_BOUNCE_RATE): [
                    [
                        (datetime.date(2016, 1, 7), 5.0),
                        (datetime.date(2016, 1, 8), 5.0),
                        (datetime.date(2016, 1, 9), 5.0),
                        (datetime.date(2016, 1, 10), 5.0),
                    ],
                    [
                        (datetime.date(2016, 1, 10), 10.0),
                        (datetime.date(2016, 1, 11), 10.0),
                        (datetime.date(2016, 1, 12), 10.0),
                    ],
                ]
            },
            metrics_basic_cross_1,
        )

        metrics_basic_cross_2 = campaign_goals.get_campaign_goal_metrics(
            campaign, datetime.date(2016, 1, 3), datetime.date(2016, 1, 7)
        )

        self.assertEqual(
            {
                constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.MAX_BOUNCE_RATE): [
                    [
                        (datetime.date(2016, 1, 5), 5.0),
                        (datetime.date(2016, 1, 6), 5.0),
                        (datetime.date(2016, 1, 7), 5.0),
                    ]
                ]
            },
            metrics_basic_cross_2,
        )

    def test_get_pre_campaign_goal_values(self):
        # (campaign, date, conversion_goals=False):
        date = datetime.date(2016, 1, 1)
        campaign = models.Campaign.objects.get(pk=1)
        pre_values = campaign_goals.get_pre_campaign_goal_values(campaign, date, conversion_goals=False)
        self.assertEqual({}, pre_values)

        goal = models.CampaignGoal.objects.create_unsafe(
            type=constants.CampaignGoalKPI.MAX_BOUNCE_RATE,
            primary=False,
            campaign_id=1,
            created_dt=datetime.date(2016, 1, 5),
        )
        cgv = models.CampaignGoalValue.objects.create(campaign_goal=goal, value=Decimal(5), created_by=self.user)
        cgv.created_dt = datetime.date(2016, 1, 5)
        cgv.save()

        pre_values_1 = campaign_goals.get_pre_campaign_goal_values(
            campaign, datetime.datetime(2016, 1, 4), conversion_goals=False
        )
        self.assertEqual({}, pre_values_1)

        pre_values_2 = campaign_goals.get_pre_campaign_goal_values(
            campaign, datetime.datetime(2016, 1, 5), conversion_goals=False
        )
        self.assertEqual({}, pre_values_2)

        pre_values_3 = campaign_goals.get_pre_campaign_goal_values(
            campaign, datetime.datetime(2016, 1, 6), conversion_goals=False
        )
        self.assertTrue(goal.id in pre_values_3)
        self.assertEqual(Decimal(5), pre_values_3[goal.id].value)

    def test_get_pre_campaign_goal_values_latest(self):
        campaign = models.Campaign.objects.get(pk=1)

        goal = models.CampaignGoal.objects.create_unsafe(
            type=constants.CampaignGoalKPI.MAX_BOUNCE_RATE,
            primary=False,
            campaign_id=1,
            created_dt=datetime.date(2016, 1, 5),
        )
        cgv1 = models.CampaignGoalValue.objects.create(campaign_goal=goal, value=Decimal(5), created_by=self.user)
        cgv1.created_dt = datetime.date(2016, 1, 5)
        cgv1.save()

        cgv2 = models.CampaignGoalValue.objects.create(campaign_goal=goal, value=Decimal(10), created_by=self.user)
        cgv2.created_dt = datetime.date(2016, 1, 6)
        cgv2.save()

        pre_values = campaign_goals.get_pre_campaign_goal_values(
            campaign, datetime.datetime(2016, 1, 7), conversion_goals=False
        )
        self.assertTrue(goal.id in pre_values)
        self.assertEqual(Decimal(10), pre_values[goal.id].value)

    def test_goal_name(self):
        goal = models.CampaignGoal.objects.create_unsafe(
            type=constants.CampaignGoalKPI.MAX_BOUNCE_RATE, primary=False, campaign_id=1
        )
        self.assertEqual(
            constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.MAX_BOUNCE_RATE),
            campaign_goals.goal_name(goal),
        )

        conv_goal = models.ConversionGoal.objects.create_unsafe(goal_id="123", name="123", type=3, campaign_id=1)
        goal = models.CampaignGoal.objects.create_unsafe(
            type=constants.CampaignGoalKPI.CPA, primary=False, campaign_id=1, conversion_goal=conv_goal
        )

        self.assertEqual(
            "avg_etfm_cost_per_conversion_goal_1", campaign_goals.goal_name(goal, conversion_goals=[conv_goal])
        )
