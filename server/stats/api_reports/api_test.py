import datetime

from django.test import TestCase
from mock import patch

import dash.models
from core.features import bid_modifiers
from dash import publisher_helpers
from stats import api_reports
from stats.api_reports import constraints_helper
from utils import test_helper
from utils.base_test_case import BaseTestCase
from zemauth.models import User


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

        self.assertEqual(
            api_reports.get_filename(
                ["placement_id"],
                {
                    "date__gte": datetime.date(2016, 10, 10),
                    "date__lte": datetime.date(2016, 10, 20),
                    "allowed_accounts": dash.models.Account.objects.filter(pk__in=[1]),
                    "allowed_campaigns": dash.models.Campaign.objects.filter(pk__in=[1]),
                    "allowed_ad_groups": dash.models.AdGroup.objects.filter(pk__in=[1, 2]),
                },
            ),
            "test-account-1_test-campaign-1_by_placement_report_2016-10-10_2016-10-20",
        )

        self.assertEqual(
            api_reports.get_filename(
                ["placement_id", "day"],
                {
                    "date__gte": datetime.date(2016, 10, 10),
                    "date__lte": datetime.date(2016, 10, 20),
                    "allowed_accounts": dash.models.Account.objects.filter(pk__in=[1]),
                    "allowed_campaigns": dash.models.Campaign.objects.filter(pk__in=[1]),
                    "allowed_ad_groups": dash.models.AdGroup.objects.filter(pk__in=[1]),
                },
            ),
            "test-account-1_test-campaign-1_test-adgroup-1_by_placement_by_day_report_2016-10-10_2016-10-20",
        )

    def test_extract_order(self):
        self.assertEqual(api_reports.extract_order("-clicks"), "-clicks")
        self.assertEqual(api_reports.extract_order("bid_cpc"), "e_media_cost")


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


class PlacementBreakdownQueryTestCase(BaseTestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=2)
        test_helper.add_permissions(self.user, permissions=["can_see_sspd_url"])

    def _convert_to_placement_entries(self):
        # convert existing PublisherGroupEntry objects into placement ones
        for i in range(1, 6):
            dash.models.PublisherGroupEntry.objects.filter(publisher_group_id=i).update(placement="plac{}".format(i))

    @classmethod
    def _create_rs_rows(cls, indices, **kwargs):
        rs_rows = []
        for i in indices:
            pge = dash.models.PublisherGroupEntry.objects.get(id=i)
            if pge.source_id is None:
                continue
            placement = "plac{}".format(i)
            placement_id = publisher_helpers.create_placement_id(pge.publisher, pge.source_id, placement)

            row = {
                "clicks": i,
                "placement_id": placement_id,
                "publisher": pge.publisher,
                "source_id": pge.source_id,
                "placement": placement,
                "placement_type": i,
            }
            row.update(kwargs)
            rs_rows.append(row)

        return rs_rows

    @patch("redshiftapi.api_breakdowns.query")
    def test_no_placement_entries(self, mock_rs_query):
        mock_rs_query.return_value = [
            {
                "ad_group_id": 1,
                "clicks": 1,
                "placement_id": "pubx.com__2__plac1",
                "publisher_id": "pubx.com__2",
                "publisher": "pubx.com",
                "source_id": 2,
                "placement": "plac1",
                "placement_type": 1,
            }
        ]

        breakdown = ["placement_id"]
        constraints = constraints_helper.prepare_constraints(
            self.user,
            breakdown,
            datetime.date(2016, 8, 1),
            datetime.date(2016, 8, 5),
            dash.models.Source.objects.all(),
            True,
            account_ids=[1],
            ad_group_ids=[1],
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
        )

        goals = constraints_helper.get_goals(constraints, breakdown)
        order = "clicks"
        offset = 1
        limit = 2

        result = api_reports.query(
            self.user, breakdown, constraints, goals, order, offset, limit, dash.constants.Level.AD_GROUPS
        )

        mock_rs_query.assert_called_with(
            ["placement_id"],
            {
                "account_id": [1],
                "campaign_id": [1],
                "ad_group_id": [1],
                "date__gte": datetime.date(2016, 8, 1),
                "date__lte": datetime.date(2016, 8, 5),
                "source_id": test_helper.ListMatcher([1, 2]),
            },
            None,
            goals,
            "clicks",
            1,
            2,
            extra_name="report_all",
            is_reports=True,
            use_publishers_view=True,
        )

        self.assertEqual(
            result,
            [
                {
                    "placement_id": "pubx.com__2__plac1",
                    "publisher": "pubx.com",
                    "placement": "plac1",
                    "source_id": 2,
                    "name": "plac1",
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pubx.com",
                    "domain_link": "http://pubx.com",
                    "status": "ACTIVE",
                    "blacklisted": "Active",
                    "blacklisted_level": "",
                    "ad_group_id": 1,
                    "clicks": 1,
                    "publisher_id": "pubx.com__2",
                    "publisher_status": "ACTIVE",
                    "source": "Gravity",
                    "placement_type": "In feed",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": None,
                }
            ],
        )

    @patch("redshiftapi.api_breakdowns.query")
    def test_include_with_no_spend(self, mock_rs_query):
        bid_modifier, _ = bid_modifiers.set(
            dash.models.AdGroup.objects.get(id=1),
            bid_modifiers.BidModifierType.PLACEMENT,
            "pub2.com__2__plac2",
            dash.models.Source.objects.get(id=2),
            0.75,
        )

        self._convert_to_placement_entries()

        mock_rs_query.return_value = [
            {
                "ad_group_id": 1,
                "clicks": 1,
                "placement_id": "pubx.com__2__plac1",
                "publisher_id": "pubx.com__2",
                "publisher": "pubx.com",
                "source_id": 2,
                "placement": "plac1",
                "placement_type": 1,
            },
            {
                "ad_group_id": 1,
                "clicks": 1,
                "placement_id": "pub2.com__2__plac2",
                "publisher_id": "pub2.com__2",
                "publisher": "pub2.com",
                "source_id": 2,
                "placement": "plac2",
                "placement_type": 2,
            },
            {
                "ad_group_id": 1,
                "clicks": 1,
                "placement_id": "pub5.com__2__plac5",
                "publisher_id": "pub5.com__2",
                "publisher": "pub5.com",
                "source_id": 2,
                "placement": "plac5",
                "placement_type": 3,
            },
        ]

        breakdown = ["ad_group_id", "placement_id"]
        constraints = constraints_helper.prepare_constraints(
            self.user,
            breakdown,
            datetime.date(2016, 8, 1),
            datetime.date(2016, 8, 5),
            dash.models.Source.objects.all(),
            True,
            account_ids=[1],
            ad_group_ids=[1],
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
        )

        goals = constraints_helper.get_goals(constraints, breakdown)
        order = "clicks"
        offset = 1
        limit = 2

        result = api_reports.query(
            self.user,
            breakdown,
            constraints,
            goals,
            order,
            offset,
            limit,
            dash.constants.Level.AD_GROUPS,
            include_items_with_no_spend=True,
        )

        mock_rs_query.assert_called_with(
            ["ad_group_id", "placement_id"],
            {
                "account_id": [1],
                "campaign_id": [1],
                "ad_group_id": [1],
                "date__gte": datetime.date(2016, 8, 1),
                "date__lte": datetime.date(2016, 8, 5),
                "source_id": test_helper.ListMatcher([1, 2]),
            },
            None,
            goals,
            "clicks",
            1,
            2,
            extra_name="report_all",
            is_reports=True,
            use_publishers_view=True,
        )

        self.assertEqual(
            result,
            [
                # "pubx.com__2__plac1" is missing due to stats.helpers.merge_rows issue
                {
                    "ad_group_id": 1,
                    "agency_id": None,
                    "account_id": 1,
                    "campaign_id": 1,
                    "name": "plac2",
                    "sspd_url": "http://localhost:8081/ad-review?adGroupId=1",
                    "archived": False,
                    "status": "WHITELISTED",
                    "state": 1,
                    "ad_group": "test adgroup 1",
                    "ad_group_status": "ENABLED",
                    "placement_id": "pub2.com__2__plac2",
                    "publisher": "pub2.com",
                    "placement": "plac2",
                    "source_id": 2,
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pub2.com",
                    "domain_link": "http://pub2.com",
                    "blacklisted": "Whitelisted",
                    "blacklisted_level": "AD GROUP",
                    "blacklisted_level_description": "Whitelisted in this ad group",
                    "notifications": {"message": "Whitelisted in this ad group"},
                    "source": "Gravity",
                    "publisher_status": "WHITELISTED",
                    "clicks": 1,
                    "publisher_id": "pub2.com__2",
                    "placement_type": "In article page",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": 0.75,
                },
                {
                    "ad_group_id": 1,
                    "agency_id": None,
                    "account_id": 1,
                    "campaign_id": 1,
                    "name": "plac5",
                    "sspd_url": "http://localhost:8081/ad-review?adGroupId=1",
                    "archived": False,
                    "status": "BLACKLISTED",
                    "state": 1,
                    "ad_group": "test adgroup 1",
                    "ad_group_status": "ENABLED",
                    "placement_id": "pub5.com__2__plac5",
                    "publisher": "pub5.com",
                    "placement": "plac5",
                    "source_id": 2,
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pub5.com",
                    "domain_link": "http://pub5.com",
                    "blacklisted": "Blacklisted",
                    "blacklisted_level": "ACCOUNT",
                    "blacklisted_level_description": "Blacklisted in this account",
                    "notifications": {"message": "Blacklisted in this account"},
                    "source": "Gravity",
                    "publisher_status": "BLACKLISTED",
                    "clicks": 1,
                    "publisher_id": "pub5.com__2",
                    "placement_type": "Ads section",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": None,
                },
            ],
        )
