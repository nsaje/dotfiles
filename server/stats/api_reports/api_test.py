import datetime

from django.test import TestCase

import dash.models
from stats import api_reports
from utils import test_helper


class ApiReportsTest(TestCase):

    fixtures = ["test_api_breakdowns.yaml"]

    def test_get_filename(self):
        self.assertEqual(
            api_reports.get_filename(
                ["publisher_id"],
                {
                    "date__gte": datetime.date(2016, 10, 10),
                    "date__lte": datetime.date(2016, 10, 20),
                    "allowed_accounts": dash.models.Account.objects.filter(pk__in=[1]),
                    "allowed_campaigns": dash.models.Campaign.objects.filter(pk__in=[1]),
                    "allowed_ad_groups": dash.models.AdGroup.objects.filter(pk__in=[1, 2]),
                },
            ),
            "test-account-1_test-campaign-1_by_publisher_report_2016-10-10_2016-10-20",
        )

        self.assertEqual(
            api_reports.get_filename(
                ["publisher_id", "day"],
                {
                    "date__gte": datetime.date(2016, 10, 10),
                    "date__lte": datetime.date(2016, 10, 20),
                    "allowed_accounts": dash.models.Account.objects.filter(pk__in=[1]),
                    "allowed_campaigns": dash.models.Campaign.objects.filter(pk__in=[1]),
                    "allowed_ad_groups": dash.models.AdGroup.objects.filter(pk__in=[1]),
                },
            ),
            "test-account-1_test-campaign-1_test-adgroup-1_by_publisher_by_day_report_2016-10-10_2016-10-20",
        )

        self.assertEqual(
            api_reports.get_filename(
                ["publisher_id", "week"],
                {
                    "date__gte": datetime.date(2016, 10, 10),
                    "date__lte": datetime.date(2016, 10, 20),
                    "allowed_accounts": dash.models.Account.objects.filter(pk__in=[1]),
                    "allowed_campaigns": dash.models.Campaign.objects.none(),
                    "allowed_ad_groups": dash.models.AdGroup.objects.none(),
                },
            ),
            "test-account-1_by_publisher_by_week_report_2016-10-10_2016-10-20",
        )

    def test_extract_order(self):
        self.assertEqual(api_reports.extract_order("-clicks"), "-clicks")
        self.assertEqual(api_reports.extract_order("pacing"), "e_media_cost")


class CampaignGoalTest(TestCase):
    fixtures = ["test_augmenter.yaml"]

    def test_get_goals(self):
        sources = dash.models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        goals = api_reports.get_goals(
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "allowed_accounts": dash.models.Account.objects.filter(pk=1),
                "allowed_campaigns": dash.models.Campaign.objects.filter(pk=1),
            },
            ["ad_group_id"],
        )

        self.assertEqual(
            goals.campaign_goals, test_helper.QuerySetMatcher(dash.models.CampaignGoal.objects.filter(pk__in=[1, 2]))
        )
        self.assertEqual(
            goals.conversion_goals,
            test_helper.QuerySetMatcher(dash.models.ConversionGoal.objects.filter(pk__in=[1, 2, 3, 4, 5])),
        )
        self.assertEqual(
            goals.campaign_goal_values,
            test_helper.QuerySetMatcher(dash.models.CampaignGoalValue.objects.filter(pk__in=[1, 2])),
        )
        self.assertEqual(goals.pixels, test_helper.QuerySetMatcher(dash.models.ConversionPixel.objects.filter(pk=1)))
        self.assertEqual(
            goals.primary_goals, test_helper.QuerySetMatcher(dash.models.CampaignGoal.objects.filter(pk__in=[2]))
        )

    def test_get_goals_no_constraints(self):
        sources = dash.models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        goals = api_reports.get_goals(
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "allowed_accounts": dash.models.Account.objects.filter(pk__in=[1, 2]),
                "allowed_campaigns": dash.models.Campaign.objects.filter(pk__in=[1, 2]),
            },
            [],
        )
        self.assertEqual(goals.campaign_goals, [])
        self.assertEqual(goals.conversion_goals, [])
        self.assertEqual(goals.campaign_goal_values, [])
        self.assertEqual(goals.pixels, [])
        self.assertEqual(goals.primary_goals, [])

    def test_get_goals_no_campaign(self):
        sources = dash.models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        goals = api_reports.get_goals(
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "allowed_accounts": dash.models.Account.objects.filter(pk=1),
                "allowed_campaigns": dash.models.Campaign.objects.filter(pk__in=[1, 2]),
            },
            ["campaign_id"],
        )

        self.assertEqual(
            goals.campaign_goals, test_helper.QuerySetMatcher(dash.models.CampaignGoal.objects.filter(pk__in=[1, 2]))
        )
        self.assertEqual(
            goals.conversion_goals,
            test_helper.QuerySetMatcher(dash.models.ConversionGoal.objects.filter(pk__in=[1, 2, 3, 4, 5])),
        )
        self.assertEqual(
            goals.campaign_goal_values,
            test_helper.QuerySetMatcher(dash.models.CampaignGoalValue.objects.filter(pk__in=[1, 2])),
        )
        self.assertEqual(goals.pixels, test_helper.QuerySetMatcher(dash.models.ConversionPixel.objects.filter(pk=1)))
        self.assertEqual(
            goals.primary_goals, test_helper.QuerySetMatcher(dash.models.CampaignGoal.objects.filter(pk__in=[2]))
        )
