import datetime
import json
from operator import itemgetter

from django.test import Client
from django.urls import reverse
from mock import ANY
from mock import patch

import core.features.publisher_groups
from dash import constants
from dash import models
from dash.constants import Level
from dash.views import breakdown_helpers
from stats.helpers import Goals
from utils import test_helper
from utils import threads
from utils.base_test_case import BaseTestCase
from zemauth.models import User


def get_publisher_group_targeting_dict():
    d = core.features.publisher_groups.get_default_publisher_group_targeting_dict()
    d["account"]["excluded"] = set([1])
    d["account"]["included"] = set([1])
    d["campaign"]["excluded"] = set([1])
    d["campaign"]["included"] = set([1])
    return d


@patch("stats.api_breakdowns.query")
class AllAccountsBreakdownTestCase(BaseTestCase):
    fixtures = ["test_api", "test_views", "test_non_superuser.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    @patch("stats.api_breakdowns.counts")
    def test_post(self, mock_counts, mock_query):
        mock_counts.return_value = []
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": ["1-2-33", "1-2-34", "1-3-22"],
        }

        response = self.client.post(
            reverse("breakdown_all_accounts", kwargs={"breakdown": "/account/campaign/dma/day"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.ALL_ACCOUNTS,
            self.user,
            ["account_id", "campaign_id", "dma", "day"],
            {
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": True,
                "allowed_accounts": test_helper.QuerySetMatcher(models.Account.objects.filter(pk__in=[1, 2])),
                "allowed_campaigns": test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1, 2, 3])),
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[])
                ),
                "publisher_group_targeting": {
                    "account": {"excluded": set([]), "included": set()},
                    "campaign": {"excluded": set(), "included": set([])},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
            ANY,
            ["1-2-33", "1-2-34", "1-3-22"],
            "-clicks",
            33,
            5,
        )

    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {"ctr": 0.9, "clicks": 123}
        mock_counts.return_value = [{"parent_breakdown_id": None, "count": 3}]
        mock_query.return_value = [
            {
                "account_id": 116,
                "account_type": "Activated",
                "agency": "MBuy",
                "archived": False,
                "breakdown_id": "116",
                "breakdown_name": "Cat's Pride",
                "click_discrepancy": None,
                "ctr": 0.682212242285772,
                "default_account_manager": "Helen Wagner",
                "default_sales_representative": "David Kaplan",
                "impressions": 9484585,
                "name": "Cat's Pride",
                "parent_breakdown_id": None,
                "pv_per_visit": None,
                "status": 1,
            },
            {
                "account_id": 305,
                "account_type": "Pilot",
                "agency": "",
                "archived": False,
                "breakdown_id": "305",
                "breakdown_name": "Outbrain",
                "click_discrepancy": None,
                "ctr": 0.445301342321372,
                "default_account_manager": "Tadej Pavli\u010d",
                "default_sales_representative": "David Kaplan",
                "impressions": 13136273,
                "name": "Outbrain",
                "parent_breakdown_id": None,
                "pv_per_visit": None,
                "status": 1,
            },
        ]

        params = {
            "limit": 2,
            "offset": 1,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": None,
        }

        response = self.client.post(
            reverse("breakdown_all_accounts", kwargs={"breakdown": "/account"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)

        self.assertDictEqual(
            result,
            {
                "success": True,
                "data": [
                    {
                        "breakdown_id": None,
                        "conversion_goals": [],
                        "currency": "USD",
                        "pixels": [],
                        "pagination": {"count": 3, "limit": 2, "offset": 1},
                        "rows": [
                            {
                                "account_id": 116,
                                "account_type": "Activated",
                                "agency": "MBuy",
                                "archived": False,
                                "breakdown_id": "116",
                                "breakdown_name": "Cat's Pride",
                                "click_discrepancy": None,
                                "ctr": 0.682212242285772,
                                "default_account_manager": "Helen Wagner",
                                "default_sales_representative": "David Kaplan",
                                "impressions": 9484585,
                                "name": "Cat's Pride",
                                "parent_breakdown_id": None,
                                "pv_per_visit": None,
                                "status": {"value": 1},
                            },
                            {
                                "account_id": 305,
                                "account_type": "Pilot",
                                "agency": "",
                                "archived": False,
                                "breakdown_id": "305",
                                "breakdown_name": "Outbrain",
                                "click_discrepancy": None,
                                "ctr": 0.445301342321372,
                                "default_account_manager": "Tadej Pavli\u010d",
                                "default_sales_representative": "David Kaplan",
                                "impressions": 13136273,
                                "name": "Outbrain",
                                "parent_breakdown_id": None,
                                "pv_per_visit": None,
                                "status": {"value": 1},
                            },
                        ],
                        "totals": {"ctr": 0.9, "clicks": 123},
                    }
                ],
            },
        )


@patch("stats.api_breakdowns.query")
class AccountBreakdownTestCase(BaseTestCase):
    fixtures = ["test_api", "test_views", "test_non_superuser.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    @patch("stats.api_breakdowns.counts")
    def test_post(self, mock_counts, mock_query):
        mock_counts.return_value = []
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": ["1-2-33", "1-2-34", "1-3-22"],
        }

        response = self.client.post(
            reverse("breakdown_accounts", kwargs={"account_id": 1, "breakdown": "/campaign/source/dma/day"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.ACCOUNTS,
            self.user,
            ["campaign_id", "source_id", "dma", "day"],
            {
                "account": models.Account.objects.get(pk=1),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "allowed_campaigns": test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1, 2])),
                "allowed_ad_groups": test_helper.QuerySetMatcher(
                    models.AdGroup.objects.filter(pk__in=[1, 2, 9, 10, 987])
                ),
                "show_archived": True,
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1])
                ),
                "publisher_group_targeting": {
                    "account": {"excluded": set([1]), "included": set([1])},
                    "campaign": {"excluded": set(), "included": set()},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
            ANY,
            ["1-2-33", "1-2-34", "1-3-22"],
            "-clicks",
            33,
            5,
        )

    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {"clicks": 123}
        mock_counts.return_value = [{"parent_breakdown_id": None, "count": 3}]
        mock_query.return_value = [
            {
                "campaign_id": 198,
                "breakdown_id": "198",
                "breakdown_name": "Blog Campaign [Desktop]",
                "parent_breakdown_id": None,
                "archived": False,
                "campaign_manager": "Ana Dejanovi\u0107",
                "cost": 9196.1064,
                "impressions": 9621740,
                "name": "Blog Campaign [Desktop]",
                "pageviews": 78853,
                "status": 1,
            },
            {
                "campaign_id": 413,
                "breakdown_id": "413",
                "breakdown_name": "Learning Center",
                "parent_breakdown_id": None,
                "archived": False,
                "campaign_manager": "Ana Dejanovi\u0107",
                "cost": 7726.1054,
                "impressions": 10441143,
                "name": "Learning Center",
                "pageviews": 51896,
                "status": 1,
            },
        ]

        params = {
            "limit": 2,
            "offset": 1,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": None,
        }

        response = self.client.post(
            reverse("breakdown_accounts", kwargs={"account_id": 1, "breakdown": "/campaign"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)

        self.assertDictEqual(
            result,
            {
                "success": True,
                "data": [
                    {
                        "breakdown_id": None,
                        "currency": "USD",
                        "pagination": {"count": 3, "limit": 2, "offset": 1},
                        "rows": [
                            {
                                "campaign_id": 198,
                                "breakdown_id": "198",
                                "breakdown_name": "Blog Campaign [Desktop]",
                                "parent_breakdown_id": None,
                                "archived": False,
                                "campaign_manager": "Ana Dejanovi\u0107",
                                "cost": 9196.1064,
                                "impressions": 9621740,
                                "name": "Blog Campaign [Desktop]",
                                "pageviews": 78853,
                                "status": {"value": 1},
                            },
                            {
                                "campaign_id": 413,
                                "breakdown_id": "413",
                                "breakdown_name": "Learning Center",
                                "parent_breakdown_id": None,
                                "archived": False,
                                "campaign_manager": "Ana Dejanovi\u0107",
                                "cost": 7726.1054,
                                "impressions": 10441143,
                                "name": "Learning Center",
                                "pageviews": 51896,
                                "status": {"value": 1},
                            },
                        ],
                        "totals": {"clicks": 123},
                        "pixels": [{"name": "test", "prefix": "pixel_1"}],
                        "conversion_goals": [
                            {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                            {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                            {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                            {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                        ],
                    }
                ],
            },
        )

    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level_delivery(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {"clicks": 123}
        mock_counts.return_value = [{"parent_breakdown_id": None, "count": 3}]
        mock_query.return_value = [
            {
                "campaign_id": 198,
                "breakdown_id": "198",
                "breakdown_name": "Blog Campaign [Desktop]",
                "parent_breakdown_id": None,
                "archived": False,
                "campaign_manager": "Ana Dejanovi\u0107",
                "cost": 9196.1064,
                "impressions": 9621740,
                "name": "Blog Campaign [Desktop]",
                "pageviews": 78853,
                "status": 1,
            },
            {
                "campaign_id": 413,
                "breakdown_id": "413",
                "breakdown_name": "Learning Center",
                "parent_breakdown_id": None,
                "archived": False,
                "campaign_manager": "Ana Dejanovi\u0107",
                "cost": 7726.1054,
                "impressions": 10441143,
                "name": "Learning Center",
                "pageviews": 51896,
                "status": 1,
            },
        ]

        params = {
            "limit": 2,
            "offset": 1,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": None,
        }

        response = self.client.post(
            reverse("breakdown_accounts", kwargs={"account_id": 1, "breakdown": "/device_type"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)

        self.assertDictEqual(
            result,
            {
                "success": True,
                "data": [
                    {
                        "breakdown_id": None,
                        "currency": "USD",
                        "pagination": {"count": 3, "limit": 2, "offset": 1},
                        "rows": [
                            {
                                "campaign_id": 198,
                                "breakdown_id": "198",
                                "breakdown_name": "Blog Campaign [Desktop]",
                                "parent_breakdown_id": None,
                                "archived": False,
                                "campaign_manager": "Ana Dejanovi\u0107",
                                "cost": 9196.1064,
                                "impressions": 9621740,
                                "name": "Blog Campaign [Desktop]",
                                "pageviews": 78853,
                                "status": {"value": 1},
                            },
                            {
                                "campaign_id": 413,
                                "breakdown_id": "413",
                                "breakdown_name": "Learning Center",
                                "parent_breakdown_id": None,
                                "archived": False,
                                "campaign_manager": "Ana Dejanovi\u0107",
                                "cost": 7726.1054,
                                "impressions": 10441143,
                                "name": "Learning Center",
                                "pageviews": 51896,
                                "status": {"value": 1},
                            },
                        ],
                        "totals": {"clicks": 123},
                        "pixels": [{"name": "test", "prefix": "pixel_1"}],
                        "conversion_goals": [],
                    }
                ],
            },
        )


@patch("stats.api_breakdowns.query")
class CampaignBreakdownTestCase(BaseTestCase):
    fixtures = ["test_api", "test_views", "test_non_superuser.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    @patch("stats.api_breakdowns.counts")
    def test_post(self, mock_counts, mock_query):
        mock_counts.return_value = []
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "false",
            "parents": ["1-2-33", "1-2-34", "1-3-22"],
        }

        response = self.client.post(
            reverse("breakdown_campaigns", kwargs={"campaign_id": 1, "breakdown": "/ad_group/source/dma/day"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        ad_groups = models.Campaign.objects.get(pk=1).adgroup_set.all().exclude_archived()
        content_ads = models.ContentAd.objects.filter(ad_group__in=ad_groups).exclude_archived()

        mock_query.assert_called_with(
            Level.CAMPAIGNS,
            self.user,
            ["ad_group_id", "source_id", "dma", "day"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "allowed_ad_groups": test_helper.QuerySetMatcher(ad_groups),
                "allowed_content_ads": test_helper.QuerySetMatcher(content_ads),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": False,
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1])
                ),
                "publisher_group_targeting": {
                    "account": {"excluded": set([1]), "included": set([1])},
                    "campaign": {"excluded": set([1]), "included": set([1])},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
            ANY,
            ["1-2-33", "1-2-34", "1-3-22"],
            "-clicks",
            33,
            5,
        )

    @patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level_delivery(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {}
        mock_counts.return_value = []
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "false",
        }

        response = self.client.post(
            reverse("breakdown_campaigns", kwargs={"campaign_id": 1, "breakdown": "/device_type"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        ad_groups = models.Campaign.objects.get(pk=1).adgroup_set.all().exclude_archived()
        content_ads = models.ContentAd.objects.filter(ad_group__in=ad_groups).exclude_archived()

        mock_query.assert_called_with(
            Level.CAMPAIGNS,
            self.user,
            ["device_type"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "allowed_ad_groups": test_helper.QuerySetMatcher(ad_groups),
                "allowed_content_ads": test_helper.QuerySetMatcher(content_ads),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": False,
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1])
                ),
                "publisher_group_targeting": {
                    "account": {"excluded": set([1]), "included": set([1])},
                    "campaign": {"excluded": set([1]), "included": set([1])},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
            ANY,
            [],
            "-clicks",
            33,
            5,
        )


@patch("stats.api_breakdowns.query")
class AdGroupBreakdownTestCase(BaseTestCase):
    fixtures = ["test_api", "test_views", "test_non_superuser.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    @patch("stats.api_breakdowns.counts")
    def test_post(self, mock_counts, mock_query):
        mock_counts.return_value = []
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": ["1-2-33", "1-2-34", "1-3-22"],
        }

        response = self.client.post(
            reverse("breakdown_ad_groups", kwargs={"ad_group_id": 1, "breakdown": "/content_ad/source/dma/day"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ["content_ad_id", "source_id", "dma", "day"],
            {
                "allowed_content_ads": test_helper.QuerySetMatcher(models.ContentAd.objects.filter(ad_group_id=1)),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": True,
                "publisher_blacklist_filter": constants.PublisherBlacklistFilter.SHOW_ALL,
                "publisher_blacklist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_whitelist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": get_publisher_group_targeting_dict(),
            },
            ANY,
            ["1-2-33", "1-2-34", "1-3-22"],
            "-clicks",
            33,
            5,
        )

    @patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level_delivery(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {}
        mock_counts.return_value = []
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
        }

        response = self.client.post(
            reverse("breakdown_ad_groups", kwargs={"ad_group_id": 1, "breakdown": "/device_type"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ["device_type"],
            {
                "allowed_content_ads": test_helper.QuerySetMatcher(models.ContentAd.objects.filter(ad_group_id=1)),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": True,
                "publisher_blacklist_filter": constants.PublisherBlacklistFilter.SHOW_ALL,
                "publisher_blacklist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_whitelist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": get_publisher_group_targeting_dict(),
            },
            ANY,
            [],
            "-clicks",
            33,
            5,
        )

    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level_content_ads(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {"clicks": 123}
        mock_counts.return_value = [{"parent_breakdown_id": None, "count": 33}]
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": [],
        }

        response = self.client.post(
            reverse("breakdown_ad_groups", kwargs={"ad_group_id": 1, "breakdown": "/content_ad"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ["content_ad_id"],
            {
                "allowed_content_ads": test_helper.QuerySetMatcher(models.ContentAd.objects.filter(ad_group_id=1)),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": True,
                "publisher_blacklist_filter": constants.PublisherBlacklistFilter.SHOW_ALL,
                "publisher_blacklist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_whitelist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": get_publisher_group_targeting_dict(),
            },
            ANY,
            [],
            "-clicks",
            33,
            5,
        )

        self.assertDictEqual(
            json.loads(response.content),
            {
                "data": [
                    {
                        "agency_uses_realtime_autopilot": True,
                        "autopilot_state": "ACTIVE_CPC_BUDGET",
                        "bid": "1.0000",
                        "bidding_type": "CPC",
                        "currency": "USD",
                        "pagination": {"count": 33, "limit": 0, "offset": 33},
                        "rows": {},
                        "breakdown_id": None,
                        "totals": {"clicks": 123},
                        "batches": [{"id": 4, "name": "batch 4"}, {"id": 1, "name": "batch 1"}],
                        "campaign_goals": [],
                        "conversion_goals": [
                            {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                            {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                            {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                            {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                        ],
                        "pixels": [{"prefix": "pixel_1", "name": "test"}],
                        "type_summaries": [{"count": 8, "max": 1.0, "min": 1.0, "type": "SOURCE"}],
                    }
                ],
                "success": True,
            },
        )

    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level_source(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {"clicks": 123}
        mock_counts.return_value = [{"parent_breakdown_id": None, "count": 33}]
        mock_query.return_value = {}

        s = models.AdGroup.objects.get(pk=1).get_current_settings().copy_settings()
        s.b1_sources_group_enabled = False
        s.save(None)

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": [],
        }

        response = self.client.post(
            reverse("breakdown_ad_groups", kwargs={"ad_group_id": 1, "breakdown": "/source"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ["source_id"],
            {
                "allowed_content_ads": test_helper.QuerySetMatcher(models.ContentAd.objects.filter(ad_group_id=1)),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": True,
                "publisher_blacklist_filter": constants.PublisherBlacklistFilter.SHOW_ALL,
                "publisher_blacklist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_whitelist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": get_publisher_group_targeting_dict(),
            },
            ANY,
            [],
            "-clicks",
            33,
            5,
        )

        self.assertDictEqual(
            json.loads(response.content),
            {
                "data": [
                    {
                        "agency_uses_realtime_autopilot": True,
                        "autopilot_state": "ACTIVE_CPC_BUDGET",
                        "bid": "1.0000",
                        "bidding_type": "CPC",
                        "currency": "USD",
                        "pagination": {"count": 33, "limit": 0, "offset": 33},
                        "rows": {},
                        "breakdown_id": None,
                        "totals": {"clicks": 123},
                        "campaign_goals": [],
                        "conversion_goals": [
                            {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                            {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                            {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                            {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                        ],
                        "pixels": [{"prefix": "pixel_1", "name": "test"}],
                        "enabling_autopilot_sources_allowed": True,
                        "ad_group_autopilot_state": 1,
                        "campaign_autopilot": False,
                        "type_summaries": [{"count": 8, "max": 1.0, "min": 1.0, "type": "SOURCE"}],
                    }
                ],
                "success": True,
            },
        )

    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level_publisher(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {"clicks": 123}
        mock_counts.return_value = [{"parent_breakdown_id": None, "count": 33}]
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": [],
        }

        response = self.client.post(
            reverse("breakdown_ad_groups", kwargs={"ad_group_id": 1, "breakdown": "/publisher"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ["publisher_id"],
            {
                "allowed_content_ads": test_helper.QuerySetMatcher(models.ContentAd.objects.filter(ad_group_id=1)),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": True,
                "publisher_blacklist_filter": constants.PublisherBlacklistFilter.SHOW_ALL,
                "publisher_blacklist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_whitelist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": get_publisher_group_targeting_dict(),
            },
            ANY,
            [],
            "-clicks",
            33,
            5,
        )

        self.assertDictEqual(
            json.loads(response.content),
            {
                "data": [
                    {
                        "agency_uses_realtime_autopilot": True,
                        "autopilot_state": "ACTIVE_CPC_BUDGET",
                        "bid": "1.0000",
                        "bidding_type": "CPC",
                        "currency": "USD",
                        "pagination": {"count": 33, "limit": 0, "offset": 33},
                        "rows": {},
                        "breakdown_id": None,
                        "totals": {"clicks": 123},
                        "ob_blacklisted_count": 0,
                        "campaign_goals": [],
                        "conversion_goals": [
                            {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                            {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                            {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                            {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                        ],
                        "pixels": [{"prefix": "pixel_1", "name": "test"}],
                        "type_summaries": [{"count": 8, "max": 1.0, "min": 1.0, "type": "SOURCE"}],
                    }
                ],
                "success": True,
            },
        )

    @patch("stats.api_breakdowns.counts")
    @patch("stats.api_breakdowns.totals")
    def test_post_base_level_placement(self, mock_totals, mock_counts, mock_query):
        mock_totals.return_value = {"clicks": 123}
        mock_counts.return_value = [{"parent_breakdown_id": None, "count": 33}]
        mock_query.return_value = {}

        params = {
            "limit": 5,
            "offset": 33,
            "order": "-clicks",
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "show_archived": "true",
            "parents": [],
        }

        response = self.client.post(
            reverse("breakdown_ad_groups", kwargs={"ad_group_id": 1, "breakdown": "/placement"}),
            data=json.dumps({"params": params}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ["placement_id"],
            {
                "allowed_content_ads": test_helper.QuerySetMatcher(models.ContentAd.objects.filter(ad_group_id=1)),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": models.Campaign.objects.get(pk=1),
                "account": models.Account.objects.get(pk=1),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 3),
                "filtered_sources": test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                "show_archived": True,
                "publisher_blacklist_filter": constants.PublisherBlacklistFilter.SHOW_ALL,
                "publisher_blacklist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_whitelist": test_helper.QuerySetMatcher(models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": get_publisher_group_targeting_dict(),
            },
            ANY,
            [],
            "-clicks",
            33,
            5,
        )

        self.assertDictEqual(
            json.loads(response.content),
            {
                "data": [
                    {
                        "agency_uses_realtime_autopilot": True,
                        "autopilot_state": "ACTIVE_CPC_BUDGET",
                        "bid": "1.0000",
                        "bidding_type": "CPC",
                        "currency": "USD",
                        "pagination": {"count": 33, "limit": 0, "offset": 33},
                        "rows": {},
                        "breakdown_id": None,
                        "totals": {"clicks": 123},
                        "campaign_goals": [],
                        "conversion_goals": [
                            {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                            {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                            {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                            {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                        ],
                        "pixels": [{"prefix": "pixel_1", "name": "test"}],
                        "type_summaries": [{"count": 8, "max": 1.0, "min": 1.0, "type": "SOURCE"}],
                    }
                ],
                "success": True,
            },
        )


class BreakdownHelperTest(BaseTestCase):
    fixtures = ["test_augmenter.yaml"]

    def test_add_performance_indicators(self):
        rows = [
            {
                "etfm_performance_campaign_goal_1": constants.CampaignGoalPerformance.AVERAGE,
                "etfm_performance_campaign_goal_2": constants.CampaignGoalPerformance.AVERAGE,
                "ad_group_id": 1,
                "etfm_cpc": 0.2,
                "local_etfm_cpc": 0.4,
            },
            {
                "etfm_performance_campaign_goal_1": constants.CampaignGoalPerformance.SUPERPERFORMING,
                "etfm_performance_campaign_goal_2": constants.CampaignGoalPerformance.UNDERPERFORMING,
                "ad_group_id": 2,
                "etfm_cpc": 0.2,
                "local_etfm_cpc": 0.4,
                "avg_etfm_cost_per_pixel_1_168": 5.0,
                "local_avg_etfm_cost_per_pixel_1_168": 10.0,
            },
        ]

        campaign_goals = models.CampaignGoal.objects.filter(pk__in=[1, 2])
        breakdown_helpers.format_report_rows_performance_fields(
            rows, Goals(campaign_goals, [], [], [], [campaign_goals[0]]), constants.Currency.USD
        )

        self.assertEqual(
            rows,
            test_helper.ListMatcher(
                [
                    {
                        "ad_group_id": 1,
                        "etfm_cpc": 0.2,
                        "local_etfm_cpc": 0.4,
                        "performance": {
                            "list": test_helper.ListMatcher(
                                [
                                    {"emoticon": constants.Emoticon.NEUTRAL, "text": "$0.400 CPC"},
                                    {"emoticon": constants.Emoticon.NEUTRAL, "text": "N/A CPA - test conversion goal"},
                                ],
                                key=itemgetter("text"),
                            ),
                            "overall": constants.Emoticon.NEUTRAL,
                        },
                        "etfm_performance_campaign_goal_1": constants.CampaignGoalPerformance.AVERAGE,
                        "etfm_performance_campaign_goal_2": constants.CampaignGoalPerformance.AVERAGE,
                        "styles": {},
                    },
                    {
                        "ad_group_id": 2,
                        "etfm_cpc": 0.2,
                        "local_etfm_cpc": 0.4,
                        "performance": {
                            "list": test_helper.ListMatcher(
                                [
                                    {"emoticon": constants.Emoticon.HAPPY, "text": "$0.400 CPC"},
                                    {"emoticon": constants.Emoticon.SAD, "text": "$10.00 CPA - test conversion goal"},
                                ],
                                key=itemgetter("text"),
                            ),
                            "overall": constants.Emoticon.HAPPY,
                        },
                        "avg_etfm_cost_per_pixel_1_168": 5.0,
                        "local_avg_etfm_cost_per_pixel_1_168": 10.0,
                        "etfm_performance_campaign_goal_1": constants.CampaignGoalPerformance.SUPERPERFORMING,
                        "etfm_performance_campaign_goal_2": constants.CampaignGoalPerformance.UNDERPERFORMING,
                        "styles": {"avg_etfm_cost_per_pixel_1_168": 3, "etfm_cpc": 1},
                    },
                ],
                key=itemgetter("ad_group_id"),
            ),
        )

    def test_dont_add_performance_indicators(self):
        rows = [{"ad_group_id": 1}, {"ad_group_id": 2}]

        breakdown_helpers.format_report_rows_performance_fields(rows, Goals([], [], [], [], []), constants.Currency.USD)

        self.assertEqual(rows, [{"ad_group_id": 1}, {"ad_group_id": 2}])

    def test_clean_non_relevant_fields(self):
        rows = [
            {"ad_group_id": 1, "campaign_has_available_budget": 1, "performance": {}, "status_per_source": 1},
            {"ad_group_id": 2, "campaign_has_available_budget": 1, "performance": {}},
        ]

        breakdown_helpers.clean_non_relevant_fields(rows)

        self.assertEqual(rows, [{"ad_group_id": 1, "performance": {}}, {"ad_group_id": 2, "performance": {}}])

    def test_content_ad_editable_rows(self):
        rows = [
            {
                "content_ad_id": 1,
                "status_per_source": {
                    1: {
                        "source_id": 1,
                        "source_name": "Gravity",
                        "source_status": 1,
                        "submission_status": 1,
                        "submission_errors": None,
                    },
                    2: {
                        "source_id": 2,
                        "source_name": "AdsNative",
                        "source_status": 2,
                        "submission_status": 2,
                        "submission_errors": "Sumtingwoing",
                    },
                },
            }
        ]

        breakdown_helpers.format_report_rows_content_ad_editable_fields(rows)

        self.assertEqual(
            rows,
            [
                {
                    "content_ad_id": 1,
                    "id": 1,
                    "submission_status": [
                        {"status": 1, "text": "Pending", "name": "Gravity", "source_state": ""},
                        {"status": 2, "text": "Approved", "name": "AdsNative", "source_state": "(paused)"},
                    ],
                    "status_per_source": {  # this node gets removed in cleanup
                        1: {
                            "source_id": 1,
                            "submission_status": 1,
                            "source_name": "Gravity",
                            "source_status": 1,
                            "submission_errors": None,
                        },
                        2: {
                            "source_id": 2,
                            "submission_status": 2,
                            "source_name": "AdsNative",
                            "source_status": 2,
                            "submission_errors": "Sumtingwoing",
                        },
                    },
                    "editable_fields": {
                        "state": {"message": None, "enabled": True},
                        "bid_modifier": {"message": None, "enabled": True},
                    },
                }
            ],
        )
