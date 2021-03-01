import datetime

import mock
from django.conf import settings
from django.test import TestCase

import dash.constants
from core.features import bid_modifiers
from dash import models
from dash import publisher_helpers
from stats import api_breakdowns
from stats import constants
from utils import test_helper
from utils import threads
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission
from zemauth.models import User


@mock.patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
class ApiBreakdownQueryTest(BaseTestCase):
    fixtures = ["test_api_breakdowns.yaml"]
    permissions = ["can_see_sspd_url", "can_see_managers_in_campaigns_table"]

    def setUp(self):
        super().setUp()
        account = models.Account.objects.get(pk=1)
        test_helper.add_entity_permissions(
            self.user,
            [Permission.READ, Permission.AGENCY_SPEND_MARGIN, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE],
            account,
        )

    @mock.patch("redshiftapi.api_breakdowns.query_structure_with_stats")
    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_query_rs_first(self, mock_rs_query, mock_str_w_stats):
        mock_rs_query.return_value = [{"clicks": 1, "campaign_id": 1}]

        mock_str_w_stats.return_value = []

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
        offset = 0
        limit = 2

        result = api_breakdowns.query(
            dash.constants.Level.ACCOUNTS, self.user, breakdown, constraints, goals, parents, order, offset, limit
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
            0,
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
                    "campaign_manager": "supertestuser@test.com",
                    "archived": False,
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=1),
                    "campaign_type": dash.constants.CampaignType.get_text(dash.constants.CampaignType.CONTENT),
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
                    "campaign_manager": "mad.max@zemanta.com",
                    "parent_breakdown_id": "",
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=2),
                    "campaign_type": dash.constants.CampaignType.get_text(dash.constants.CampaignType.CONTENT),
                },
            ],
        )

    @mock.patch("redshiftapi.api_breakdowns.query_stats_for_rows")
    def test_query_dash_first(self, mock_rs_query):
        mock_rs_query.return_value = [{"clicks": 1, "campaign_id": 1}, {"clicks": 2, "campaign_id": 2}]

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
            dash.constants.Level.ACCOUNTS, self.user, breakdown, constraints, goals, parents, order, offset, limit
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
                    "campaign_manager": "supertestuser@test.com",
                    "archived": False,
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=1),
                    "campaign_type": dash.constants.CampaignType.get_text(dash.constants.CampaignType.CONTENT),
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
                    "campaign_manager": "mad.max@zemanta.com",
                    "archived": True,  # archived last
                    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=2),
                    "campaign_type": dash.constants.CampaignType.get_text(dash.constants.CampaignType.CONTENT),
                },
            ],
        )

    def test_should_use_publishers_view(self):
        self.assertFalse(api_breakdowns.should_use_publishers_view([constants.AD_GROUP]))
        self.assertTrue(api_breakdowns.should_use_publishers_view([constants.PUBLISHER]))
        self.assertTrue(api_breakdowns.should_use_publishers_view([constants.PLACEMENT]))
        self.assertFalse(api_breakdowns.should_use_publishers_view([constants.CONTENT_AD, constants.PUBLISHER]))
        self.assertTrue(
            api_breakdowns.should_use_publishers_view([constants.AD_GROUP, constants.PUBLISHER, constants.PLACEMENT])
        )

        # Breakdown by content_ad_id when querying placements is currently not supported.
        self.assertTrue(
            api_breakdowns.should_use_publishers_view(
                [constants.AD_GROUP, constants.CONTENT_AD, constants.PUBLISHER, constants.PLACEMENT]
            )
        )

    def test_query_counts_dash(self):
        breakdown = ["campaign_id"]
        constraints = {
            "show_archived": True,
            "account": models.Account.objects.get(pk=1),
            "filtered_sources": models.Source.objects.all(),
            "allowed_campaigns": models.Campaign.objects.filter(pk__in=[1, 2]),
            "date__gte": datetime.date(2016, 8, 1),
            "date__lte": datetime.date(2016, 8, 5),
        }
        parents = []
        goals = api_breakdowns.get_goals(constraints, breakdown)

        result = api_breakdowns.counts(dash.constants.Level.ACCOUNTS, self.user, breakdown, constraints, parents, goals)

        self.assertEqual(result, [{"parent_breakdown_id": None, "count": 2}])


@mock.patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
class PlacementBreakdownQueryTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    @staticmethod
    def _convert_to_placement_entries():
        # convert existing PublisherGroupEntry objects into placement ones
        for i in range(1, 6):
            models.PublisherGroupEntry.objects.filter(publisher_group_id=i).update(placement="plac{}".format(i))

    @classmethod
    def _create_rs_rows(cls, indices, **kwargs):
        rs_rows = []
        for i in indices:
            pge = models.PublisherGroupEntry.objects.get(id=i)
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

    @mock.patch("redshiftapi.api_breakdowns.query_structure_with_stats")
    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_campaign(self, mock_rs_query, mock_str_w_stats):
        self._convert_to_placement_entries()

        mock_rs_query.return_value = self._create_rs_rows(range(1, 6), campaign_id=1)

        mock_str_w_stats.return_value = []

        user = User.objects.get(pk=1)
        breakdown = ["placement_id"]
        constraints = {
            "account": models.Account.objects.get(pk=1),
            "campaign": models.Campaign.objects.get(pk=1),
            "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
            "show_archived": True,
            "filtered_sources": models.Source.objects.all(),
            "publisher_blacklist_filter": dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 3, 5]),
            "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4]),
            "publisher_group_targeting": {
                "ad_group": {"included": set([2]), "excluded": set([3])},
                "campaign": {"included": set([4]), "excluded": set()},
                "account": {"included": set(), "excluded": set([5])},
                "global": {"excluded": set([1])},
            },
            "date__gte": datetime.date(2016, 8, 1),
            "date__lte": datetime.date(2016, 8, 5),
        }
        goals = api_breakdowns.get_goals(constraints, breakdown)
        parents = []
        order = "clicks"
        offset = 1
        limit = 2

        result = api_breakdowns.query(
            dash.constants.Level.CAMPAIGNS, user, breakdown, constraints, goals, parents, order, offset, limit
        )

        mock_rs_query.assert_called_with(
            ["placement_id"],
            {
                "account_id": 1,
                "campaign_id": 1,
                "date__gte": datetime.date(2016, 8, 1),
                "date__lte": datetime.date(2016, 8, 5),
                "source_id": test_helper.ListMatcher([1, 2]),
            },
            None,
            goals,
            "clicks",
            1,
            2,
            use_publishers_view=True,
        )

        self.assertEqual(
            result,
            [
                {
                    "placement_id": "pub1.com__1__plac1",
                    "publisher": "pub1.com",
                    "placement": "plac1",
                    "source_id": 1,
                    "name": "plac1",
                    "source_name": "AdsNative",
                    "source_slug": "adsnative",
                    "exchange": "AdsNative",
                    "domain": "pub1.com",
                    "domain_link": "http://pub1.com",
                    "status": 2,
                    "blacklisted": "Blacklisted",
                    "blacklisted_level": "global",
                    "blacklisted_level_description": "Blacklisted globally",
                    "notifications": {"message": "Blacklisted globally"},
                    "clicks": 1,
                    "placement_type": "In feed",
                    "campaign_id": 1,
                    "breakdown_id": "pub1.com__1__plac1",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac1",
                },
                {
                    "placement_id": "pub2.com__2__plac2",
                    "publisher": "pub2.com",
                    "placement": "plac2",
                    "source_id": 2,
                    "name": "plac2",
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pub2.com",
                    "domain_link": "http://pub2.com",
                    "status": 1,
                    "blacklisted": "Whitelisted",
                    "blacklisted_level": "adgroup",
                    "blacklisted_level_description": "Whitelisted in this ad group",
                    "notifications": {"message": "Whitelisted in this ad group"},
                    "clicks": 2,
                    "placement_type": "In article page",
                    "campaign_id": 1,
                    "breakdown_id": "pub2.com__2__plac2",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac2",
                },
                {
                    "placement_id": "pub5.com__2__plac5",
                    "publisher": "pub5.com",
                    "placement": "plac5",
                    "source_id": 2,
                    "name": "plac5",
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pub5.com",
                    "domain_link": "http://pub5.com",
                    "status": 2,
                    "blacklisted": "Blacklisted",
                    "blacklisted_level": "account",
                    "blacklisted_level_description": "Blacklisted in this account",
                    "notifications": {"message": "Blacklisted in this account"},
                    "clicks": 5,
                    "placement_type": "Other",
                    "campaign_id": 1,
                    "breakdown_id": "pub5.com__2__plac5",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac5",
                },
            ],
        )

    @mock.patch("redshiftapi.api_breakdowns.query_structure_with_stats")
    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_ad_group(self, mock_rs_query, mock_str_w_stats):
        self._convert_to_placement_entries()

        mock_rs_query.return_value = self._create_rs_rows(range(1, 6), ad_group_id=1)

        mock_str_w_stats.return_value = []

        user = User.objects.get(pk=1)
        breakdown = ["placement_id"]
        constraints = {
            "account": models.Account.objects.get(pk=1),
            "ad_group": models.AdGroup.objects.get(pk=1),
            "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
            "show_archived": True,
            "filtered_sources": models.Source.objects.all(),
            "publisher_blacklist_filter": dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 3, 5]),
            "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4]),
            "publisher_group_targeting": {
                "ad_group": {"included": set([2]), "excluded": set([3])},
                "campaign": {"included": set([4]), "excluded": set()},
                "account": {"included": set(), "excluded": set([5])},
                "global": {"excluded": set([1])},
            },
            "date__gte": datetime.date(2016, 8, 1),
            "date__lte": datetime.date(2016, 8, 5),
        }
        goals = api_breakdowns.get_goals(constraints, breakdown)
        parents = []
        order = "clicks"
        offset = 1
        limit = 2

        result = api_breakdowns.query(
            dash.constants.Level.AD_GROUPS, user, breakdown, constraints, goals, parents, order, offset, limit
        )

        mock_rs_query.assert_called_with(
            ["placement_id"],
            {
                "account_id": 1,
                "ad_group_id": 1,
                "date__gte": datetime.date(2016, 8, 1),
                "date__lte": datetime.date(2016, 8, 5),
                "source_id": test_helper.ListMatcher([1, 2]),
            },
            None,
            goals,
            "clicks",
            1,
            2,
            use_publishers_view=True,
        )

        self.assertEqual(
            result,
            [
                {
                    "placement_id": "pub1.com__1__plac1",
                    "publisher": "pub1.com",
                    "placement": "plac1",
                    "source_id": 1,
                    "name": "plac1",
                    "source_name": "AdsNative",
                    "source_slug": "adsnative",
                    "exchange": "AdsNative",
                    "domain": "pub1.com",
                    "domain_link": "http://pub1.com",
                    "status": 2,
                    "blacklisted": "Blacklisted",
                    "blacklisted_level": "global",
                    "blacklisted_level_description": "Blacklisted globally",
                    "notifications": {"message": "Blacklisted globally"},
                    "clicks": 1,
                    "placement_type": "In feed",
                    "ad_group_id": 1,
                    "breakdown_id": "pub1.com__1__plac1",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac1",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": {
                        "id": None,
                        "modifier": None,
                        "source_slug": "adsnative",
                        "target": "pub1.com__1__plac1",
                        "type": "PLACEMENT",
                    },
                },
                {
                    "placement_id": "pub2.com__2__plac2",
                    "publisher": "pub2.com",
                    "placement": "plac2",
                    "source_id": 2,
                    "name": "plac2",
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pub2.com",
                    "domain_link": "http://pub2.com",
                    "status": 1,
                    "blacklisted": "Whitelisted",
                    "blacklisted_level": "adgroup",
                    "blacklisted_level_description": "Whitelisted in this ad group",
                    "notifications": {"message": "Whitelisted in this ad group"},
                    "clicks": 2,
                    "placement_type": "In article page",
                    "ad_group_id": 1,
                    "breakdown_id": "pub2.com__2__plac2",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac2",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": {
                        "id": None,
                        "modifier": None,
                        "source_slug": "gravity",
                        "target": "pub2.com__2__plac2",
                        "type": "PLACEMENT",
                    },
                },
                {
                    "placement_id": "pub5.com__2__plac5",
                    "publisher": "pub5.com",
                    "placement": "plac5",
                    "source_id": 2,
                    "name": "plac5",
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pub5.com",
                    "domain_link": "http://pub5.com",
                    "status": 2,
                    "blacklisted": "Blacklisted",
                    "blacklisted_level": "account",
                    "blacklisted_level_description": "Blacklisted in this account",
                    "notifications": {"message": "Blacklisted in this account"},
                    "clicks": 5,
                    "placement_type": "Other",
                    "ad_group_id": 1,
                    "breakdown_id": "pub5.com__2__plac5",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac5",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": {
                        "id": None,
                        "modifier": None,
                        "source_slug": "gravity",
                        "target": "pub5.com__2__plac5",
                        "type": "PLACEMENT",
                    },
                },
            ],
        )

    @mock.patch("redshiftapi.api_breakdowns.query_structure_with_stats")
    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_ad_group_blacklisted_only(self, mock_rs_query, mock_str_w_stats):
        self._convert_to_placement_entries()
        # add some publisher group entries that should not appear in the query
        magic_mixer.blend(
            models.PublisherGroupEntry, publisher_group_id=1, publisher="pub1.com", source_id=1, placement=None
        )
        magic_mixer.blend(
            models.PublisherGroupEntry, publisher_group_id=3, publisher="pub3.com", source=None, placement=None
        )
        magic_mixer.blend(
            models.PublisherGroupEntry, publisher_group_id=5, publisher="pub5.com", source_id=2, placement=None
        )

        mock_rs_query.return_value = self._create_rs_rows([1, 3, 5], ad_group_id=1)

        mock_str_w_stats.return_value = []

        user = User.objects.get(pk=1)
        breakdown = ["placement_id"]
        constraints = {
            "account": models.Account.objects.get(pk=1),
            "ad_group": models.AdGroup.objects.get(pk=1),
            "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
            "show_archived": True,
            "filtered_sources": models.Source.objects.all(),
            "publisher_blacklist_filter": dash.constants.PublisherBlacklistFilter.SHOW_BLACKLISTED,
            "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 3, 5]),
            "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4]),
            "publisher_group_targeting": {
                "ad_group": {"included": set([2]), "excluded": set([3])},
                "campaign": {"included": set([4]), "excluded": set()},
                "account": {"included": set(), "excluded": set([5])},
                "global": {"excluded": set([1])},
            },
            "date__gte": datetime.date(2016, 8, 1),
            "date__lte": datetime.date(2016, 8, 5),
        }
        goals = api_breakdowns.get_goals(constraints, breakdown)
        parents = []
        order = "clicks"
        offset = 1
        limit = 2

        result = api_breakdowns.query(
            dash.constants.Level.AD_GROUPS, user, breakdown, constraints, goals, parents, order, offset, limit
        )

        mock_rs_query.assert_called_with(
            ["placement_id"],
            {
                "account_id": 1,
                "ad_group_id": 1,
                "date__gte": datetime.date(2016, 8, 1),
                "date__lte": datetime.date(2016, 8, 5),
                "source_id": test_helper.ListMatcher([1, 2]),
                "placement_id": test_helper.ListMatcher(
                    ["pub1.com__1__plac1", "pub3.com____plac3", "pub5.com__2__plac5"]
                ),
            },
            None,
            goals,
            "clicks",
            1,
            2,
            use_publishers_view=True,
        )

        self.assertEqual(
            result,
            [
                {
                    "placement_id": "pub1.com__1__plac1",
                    "publisher": "pub1.com",
                    "placement": "plac1",
                    "source_id": 1,
                    "name": "plac1",
                    "source_name": "AdsNative",
                    "source_slug": "adsnative",
                    "exchange": "AdsNative",
                    "domain": "pub1.com",
                    "domain_link": "http://pub1.com",
                    "status": 2,
                    "blacklisted": "Blacklisted",
                    "blacklisted_level": "global",
                    "blacklisted_level_description": "Blacklisted globally",
                    "notifications": {"message": "Blacklisted globally"},
                    "clicks": 1,
                    "placement_type": "In feed",
                    "ad_group_id": 1,
                    "breakdown_id": "pub1.com__1__plac1",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac1",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": {
                        "id": None,
                        "modifier": None,
                        "source_slug": "adsnative",
                        "target": "pub1.com__1__plac1",
                        "type": "PLACEMENT",
                    },
                },
                {
                    "placement_id": "pub5.com__2__plac5",
                    "publisher": "pub5.com",
                    "placement": "plac5",
                    "source_id": 2,
                    "name": "plac5",
                    "source_name": "Gravity",
                    "source_slug": "gravity",
                    "exchange": "Gravity",
                    "domain": "pub5.com",
                    "domain_link": "http://pub5.com",
                    "status": 2,
                    "blacklisted": "Blacklisted",
                    "blacklisted_level": "account",
                    "blacklisted_level_description": "Blacklisted in this account",
                    "notifications": {"message": "Blacklisted in this account"},
                    "clicks": 5,
                    "placement_type": "Other",
                    "ad_group_id": 1,
                    "breakdown_id": "pub5.com__2__plac5",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac5",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": {
                        "id": None,
                        "modifier": None,
                        "source_slug": "gravity",
                        "target": "pub5.com__2__plac5",
                        "type": "PLACEMENT",
                    },
                },
            ],
        )

    @mock.patch("redshiftapi.api_breakdowns.query_structure_with_stats")
    @mock.patch("redshiftapi.api_breakdowns.query")
    def test_ad_group_no_placement_entries(self, mock_rs_query, mock_str_w_stats):
        bid_modifier, _ = bid_modifiers.set(
            dash.models.AdGroup.objects.get(id=1),
            bid_modifiers.BidModifierType.PLACEMENT,
            "pubx.com__2__plac1",
            dash.models.Source.objects.get(id=2),
            0.75,
        )
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

        mock_str_w_stats.return_value = []

        user = User.objects.get(pk=1)
        breakdown = ["placement_id"]
        constraints = {
            "account": models.Account.objects.get(pk=1),
            "ad_group": models.AdGroup.objects.get(pk=1),
            "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
            "show_archived": True,
            "filtered_sources": models.Source.objects.all(),
            "publisher_blacklist_filter": dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 3, 5]),
            "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4]),
            "publisher_group_targeting": {
                "ad_group": {"included": set([2]), "excluded": set([3])},
                "campaign": {"included": set([4]), "excluded": set()},
                "account": {"included": set(), "excluded": set([5])},
                "global": {"excluded": set([1])},
            },
            "date__gte": datetime.date(2016, 8, 1),
            "date__lte": datetime.date(2016, 8, 5),
        }
        goals = api_breakdowns.get_goals(constraints, breakdown)
        parents = []
        order = "clicks"
        offset = 1
        limit = 2

        result = api_breakdowns.query(
            dash.constants.Level.AD_GROUPS, user, breakdown, constraints, goals, parents, order, offset, limit
        )

        mock_rs_query.assert_called_with(
            ["placement_id"],
            {
                "account_id": 1,
                "ad_group_id": 1,
                "date__gte": datetime.date(2016, 8, 1),
                "date__lte": datetime.date(2016, 8, 5),
                "source_id": test_helper.ListMatcher([1, 2]),
            },
            None,
            goals,
            "clicks",
            1,
            2,
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
                    "status": 3,
                    "blacklisted": "Active",
                    "ad_group_id": 1,
                    "clicks": 1,
                    "publisher_id": "pubx.com__2",
                    "placement_type": "In feed",
                    "breakdown_id": "pubx.com__2__plac1",
                    "parent_breakdown_id": "",
                    "breakdown_name": "plac1",
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                    "bid_modifier": {
                        "id": bid_modifier.id,
                        "modifier": 0.75,
                        "source_slug": "gravity",
                        "target": "pubx.com__2__plac1",
                        "type": "PLACEMENT",
                    },
                }
            ],
        )
