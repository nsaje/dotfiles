import datetime

import mock
from django.conf import settings
from django.test import TestCase

from dash import models
from dash.constants import CampaignType
from dash.constants import Level
from stats import api_breakdowns
from utils import test_helper
from utils import threads
from zemauth.models import User


@mock.patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
class ApiBreakdownQueryTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    @mock.patch("redshiftapi.api_breakdowns.query_structure_with_stats")
    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_query_rs_first(self, mock_rs_query, mock_str_w_stats):

        mock_rs_query.return_value = [{"clicks": 1, "campaign_id": 1}]

        mock_str_w_stats.return_value = []

        user = User.objects.get(pk=1)
        breakdown = ["campaign_id"]
        constraints = {
            "show_archived": True,
            "account": models.Account.objects.get(pk=1),
            "allowed_campaigns": models.Campaign.objects.filter(pk__in=[1, 2]),
            "filtered_sources": models.Source.objects.all(),
            "date__gte": datetime.date(2016, 8, 1),
            "date__lte": datetime.date(2016, 8, 5),
        }
        goals = api_breakdowns.get_goals(constraints, breakdown)
        parents = []
        order = "clicks"
        offset = 1
        limit = 2

        result = api_breakdowns.query(
            Level.ACCOUNTS, user, breakdown, constraints, goals, parents, order, offset, limit
        )

        mock_rs_query.assert_called_with(
            ["campaign_id"],
            {
                "account_id": 1,
                "campaign_id": test_helper.ListMatcher([1, 2]),
                "date__gte": datetime.date(2016, 8, 1),
                "date__lte": datetime.date(2016, 8, 5),
                "source_id": test_helper.ListMatcher([1, 2]),
            },
            None,
            goals,
            "clicks",
            1,
            2,
            use_publishers_view=False,
        )

        self.assertEqual(
            result,
            [
                {
                    "campaign_id": 1,
                    "account_id": 1,
                    "agency_id": None,
                    "name": "test campaign 1",
                    "breakdown_id": "1",
                    "breakdown_name": "test campaign 1",
                    "clicks": 1,
                    "parent_breakdown_id": "",
                    "status": 1,
                    "pacing": None,
                    "allocated_budgets": None,
                    "spend_projection": None,
                    "license_fee_projection": None,
                    "campaign_manager": "supertestuser@test.com",
                    "archived": False,
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=1),
                    "campaign_type": CampaignType.get_text(CampaignType.CONTENT),
                },
                {
                    "status": 2,
                    "archived": True,
                    "breakdown_name": "test campaign 2",
                    "name": "test campaign 2",
                    "breakdown_id": "2",
                    "campaign_id": 2,
                    "account_id": 1,
                    "agency_id": None,
                    "pacing": None,
                    "spend_projection": None,
                    "allocated_budgets": None,
                    "campaign_manager": "mad.max@zemanta.com",
                    "parent_breakdown_id": "",
                    "license_fee_projection": None,
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=2),
                    "campaign_type": CampaignType.get_text(CampaignType.CONTENT),
                },
            ],
        )

    @mock.patch("redshiftapi.api_breakdowns.query_stats_for_rows")
    def test_query_dash_first(self, mock_rs_query):

        mock_rs_query.return_value = [{"clicks": 1, "campaign_id": 1}, {"clicks": 2, "campaign_id": 2}]

        user = User.objects.get(pk=1)
        breakdown = ["campaign_id"]
        constraints = {
            "show_archived": True,
            "account": models.Account.objects.get(pk=1),
            "filtered_sources": models.Source.objects.all(),
            "allowed_campaigns": models.Campaign.objects.filter(pk__in=[1, 2]),
            "date__gte": datetime.date(2016, 8, 1),
            "date__lte": datetime.date(2016, 8, 5),
        }
        goals = api_breakdowns.get_goals(constraints, breakdown)
        parents = []
        order = "-name"
        offset = 0
        limit = 10

        result = api_breakdowns.query(
            Level.ACCOUNTS, user, breakdown, constraints, goals, parents, order, offset, limit
        )

        self.assertEqual(
            result,
            [
                {
                    "campaign_id": 1,
                    "account_id": 1,
                    "agency_id": None,
                    "name": "test campaign 1",
                    "breakdown_id": "1",
                    "breakdown_name": "test campaign 1",
                    "clicks": 1,
                    "parent_breakdown_id": "",
                    "status": 1,
                    "pacing": None,
                    "allocated_budgets": None,
                    "spend_projection": None,
                    "license_fee_projection": None,
                    "campaign_manager": "supertestuser@test.com",
                    "archived": False,
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=1),
                    "campaign_type": CampaignType.get_text(CampaignType.CONTENT),
                },
                {
                    "campaign_id": 2,
                    "account_id": 1,
                    "agency_id": None,
                    "name": "test campaign 2",
                    "breakdown_id": "2",
                    "breakdown_name": "test campaign 2",
                    "clicks": 2,
                    "parent_breakdown_id": "",
                    "status": 2,
                    "pacing": None,
                    "allocated_budgets": None,
                    "spend_projection": None,
                    "license_fee_projection": None,
                    "campaign_manager": "mad.max@zemanta.com",
                    "archived": True,  # archived last
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=2),
                    "campaign_type": CampaignType.get_text(CampaignType.CONTENT),
                },
            ],
        )
