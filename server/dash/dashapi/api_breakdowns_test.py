import copy
import datetime
from decimal import Decimal

import mock
from django.conf import settings
from mock import MagicMock
from mock import patch

import core.features.bid_modifiers
import core.models
from dash import models
from dash import publisher_helpers
from dash.constants import CampaignType
from dash.constants import DeviceType
from dash.constants import Level
from dash.constants import OperatingSystem
from dash.constants import PublisherBlacklistLevel
from dash.dashapi import api_breakdowns
from dash.dashapi import augmenter
from dash.dashapi import helpers
from utils import threads
from utils.base_test_case import BaseTestCase
from utils.dict_helper import dict_join
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission
from zemauth.models import User

"""
NOTE 1: The following dicts represent rows that are returned by dashapi.api_breakdowns query functions.
Whenever a new field is added to augmenter/loader, add it here so that all instances of the row
get updated.

NOTE 2: To check for correct results use "assertEqual" and not "assertCountEqual" as the order in which results
are returned matters.
"""


START_DATE, END_DATE = datetime.date(2016, 7, 1), datetime.date(2016, 8, 31)
R1_CREATIVE_REDIRECT_URL = "https://r1.zemanta.com/creative/123"

SOURCE_1 = {
    "archived": False,
    "maintenance": False,
    "name": "AdsNative",
    "source_id": 1,
    "source_slug": "adsnative",
    "id": 1,
}  # noqa
SOURCE_2 = {
    "archived": False,
    "maintenance": False,
    "name": "Gravity",
    "source_id": 2,
    "source_slug": "gravity",
    "id": 2,
}  # noqa

ACCOUNT_1 = {
    "account_id": 1,
    "agency_id": None,
    "archived": False,
    "name": "test account 1",
    "status": 2,
    "default_account_manager": "mad.max@zemanta.com",
    "default_sales_representative": "supertestuser@test.com",
    "salesforce_url": "",
    "default_cs_representative": "supercsuser@test.com",
    "ob_sales_representative": None,
    "ob_account_manager": None,
    "agency": "",
    "account_type": "Activated",
    "sspd_url": settings.SSPD_ACCOUNT_REDIRECT_URL.format(id=1),
    "daily_budget": 0,
}

CAMPAIGN_1 = {
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "archived": False,
    "name": "test campaign 1",
    "status": 1,
    "campaign_manager": "supertestuser@test.com",
    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=1),
    "campaign_type": CampaignType.get_text(CampaignType.CONTENT),
    "daily_budget": 0,
}
CAMPAIGN_2 = {
    "campaign_id": 2,
    "account_id": 1,
    "agency_id": None,
    "archived": True,
    "name": "test campaign 2",
    "status": 2,
    "campaign_manager": "mad.max@zemanta.com",
    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=2),
    "campaign_type": CampaignType.get_text(CampaignType.CONTENT),
    "daily_budget": 0,
}

AD_GROUP_1 = {
    "ad_group_id": 1,
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "archived": False,
    "name": "test adgroup 1",
    "status": 1,
    "state": 1,
    "sspd_url": settings.SSPD_AD_GROUP_REDIRECT_URL.format(id=1),
}
AD_GROUP_2 = {
    "ad_group_id": 2,
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "archived": False,
    "name": "test adgroup 2",
    "status": 2,
    "state": 2,
    "sspd_url": settings.SSPD_AD_GROUP_REDIRECT_URL.format(id=2),
}

AD_GROUP_BASE_1 = dict_join(AD_GROUP_1, {"campaign_has_available_budget": True})
AD_GROUP_BASE_2 = dict_join(AD_GROUP_2, {"campaign_has_available_budget": True})

CONTENT_AD_1 = {
    "content_ad_id": 1,
    "ad_group_id": 1,
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "title": "Title 1",
    "creative_type": "Content ad",
    "creative_size": "200x300",
    "description": "Example description",
    "brand_name": "Example",
    "archived": False,
    "name": "Title 1",
    "display_url": "example.com",
    "call_to_action": "Call to action",
    "label": "",
    "image_hash": "100",
    "image_urls": {
        "square": "/100.jpg?w=300&h=300&fit=crop&crop=center",
        "landscape": "/100.jpg?w=720&h=450&fit=crop&crop=center",
        "portrait": "/100.jpg?w=375&h=480&fit=crop&crop=center",
        "icon": "/1000.jpg?w=300&h=300&fit=crop&crop=center",
        "image": "/100.jpg?w=200&h=300&fit=crop&crop=center",
        "ad_tag": None,
    },
    "amplify_live_preview_link": "https://www.taste.com.au/recipes/tandoori-roast-cauliflower-rice/g9h9ol5t?_b1_ad_group_id=1&_b1_cpm=500&_b1_no_targeting=1",
    "batch_id": 1,
    "batch_name": "batch 1",
    "upload_time": datetime.datetime(2015, 2, 23, 0, 0),
    "redirector_url": R1_CREATIVE_REDIRECT_URL,
    "url": "http://testurl1.com",
    "state": 1,
    "status": 1,
    "status_per_source": {
        1: {
            "source_id": 1,
            "submission_status": 1,
            "source_name": "AdsNative",
            "source_status": 1,
            "submission_errors": None,
        },
        2: {
            "source_id": 2,
            "submission_status": 2,
            "source_name": "Gravity",
            "source_status": 2,
            "submission_errors": None,
        },
    },
    "tracker_urls": ["http://testurl1.com", "http://testurl2.com"],
    "sspd_url": settings.SSPD_CONTENT_AD_REDIRECT_URL.format(id=1),
    "bid_modifier": {"id": None, "modifier": None, "source_slug": None, "target": "1", "type": "AD"},
    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
}

CONTENT_AD_2 = {
    "content_ad_id": 2,
    "ad_group_id": 1,
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "title": "Title 2",
    "creative_type": "Content ad",
    "creative_size": "200x300",
    "description": "Example description",
    "brand_name": "Example",
    "archived": False,
    "name": "Title 2",
    "display_url": "example.com",
    "call_to_action": "Call to action",
    "label": "",
    "image_hash": "200",
    "image_urls": {
        "square": "/200.jpg?w=300&h=300&fit=crop&crop=center",
        "landscape": "/200.jpg?w=720&h=450&fit=crop&crop=center",
        "portrait": "/200.jpg?w=375&h=480&fit=crop&crop=center",
        "icon": "/d/icons/IAB24.jpg?w=300&h=300&fit=crop&crop=center",
        "image": "/200.jpg?w=200&h=300&fit=crop&crop=center",
        "ad_tag": None,
    },
    "amplify_live_preview_link": "https://www.taste.com.au/recipes/tandoori-roast-cauliflower-rice/g9h9ol5t?_b1_ad_group_id=1&_b1_cpm=500&_b1_no_targeting=1",
    "batch_id": 1,
    "batch_name": "batch 1",
    "upload_time": datetime.datetime(2015, 2, 23, 0, 0),
    "redirector_url": R1_CREATIVE_REDIRECT_URL,
    "url": "http://testurl2.com",
    "state": 2,
    "status": 2,
    "status_per_source": {
        2: {
            "source_id": 2,
            "submission_status": 2,
            "source_name": "Gravity",
            "source_status": 2,
            "submission_errors": None,
        }
    },
    "tracker_urls": [],
    "sspd_url": settings.SSPD_CONTENT_AD_REDIRECT_URL.format(id=2),
    "bid_modifier": {"id": None, "modifier": None, "source_slug": None, "target": "2", "type": "AD"},
    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
}

# sources on ad group level
AD_GROUP_SOURCE_1 = {
    "source_id": 1,
    "source_slug": "adsnative",
    "id": 1,
    "name": "AdsNative",
    "daily_budget": Decimal("10.0000"),
    "current_daily_budget": Decimal("10.0000"),
    "local_daily_budget": Decimal("10.0000"),
    "local_current_daily_budget": Decimal("10.0000"),
    "bid_cpc": Decimal("0.5010"),
    "current_bid_cpc": Decimal("0.5010"),
    "local_bid_cpc": Decimal("0.5010"),
    "local_current_bid_cpc": Decimal("0.5010"),
    "bid_cpm": Decimal("0.4010"),
    "current_bid_cpm": Decimal("0.4010"),
    "local_bid_cpm": Decimal("0.4010"),
    "local_current_bid_cpm": Decimal("0.4010"),
    "archived": False,
    "maintenance": False,
    "supply_dash_url": None,
    "supply_dash_disabled_message": "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",  # noqa
    "state": 1,
    "status": 1,
    "editable_fields": {
        "state": {"message": "This source must be managed manually.", "enabled": False},
        "bid_cpc": {"message": "This value cannot be edited because the ad group is on Autopilot.", "enabled": False},
        "bid_cpm": {"message": "This value cannot be edited because the ad group is on Autopilot.", "enabled": False},
        "bid_modifier": {
            "message": "This value cannot be edited because the ad group is on Autopilot.",
            "enabled": False,
        },
        "daily_budget": {
            "message": "This value cannot be edited because the ad group is on Autopilot.",
            "enabled": False,
        },
    },
    "bid_modifier": {"id": None, "modifier": None, "source_slug": None, "target": "adsnative", "type": "SOURCE"},
    "notifications": {},
}
AD_GROUP_SOURCE_2 = {
    "source_id": 2,
    "source_slug": "gravity",
    "id": 2,
    "name": "Gravity",
    "daily_budget": Decimal("20.0000"),
    "current_daily_budget": Decimal("20.0000"),
    "local_daily_budget": Decimal("20.0000"),
    "local_current_daily_budget": Decimal("20.0000"),
    "bid_cpc": Decimal("0.5020"),
    "current_bid_cpc": Decimal("0.5020"),
    "local_bid_cpc": Decimal("0.5020"),
    "local_current_bid_cpc": Decimal("0.5020"),
    "bid_cpm": Decimal("0.4020"),
    "current_bid_cpm": Decimal("0.4020"),
    "local_bid_cpm": Decimal("0.4020"),
    "local_current_bid_cpm": Decimal("0.4020"),
    "archived": False,
    "maintenance": False,
    "supply_dash_url": None,
    "supply_dash_disabled_message": "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",  # noqa
    "state": 2,
    "status": 2,
    "editable_fields": {
        "state": {"message": None, "enabled": True},
        "bid_cpc": {"message": "This value cannot be edited because the ad group is on Autopilot.", "enabled": False},
        "bid_cpm": {"message": "This value cannot be edited because the ad group is on Autopilot.", "enabled": False},
        "bid_modifier": {
            "message": "This value cannot be edited because the ad group is on Autopilot.",
            "enabled": False,
        },
        "daily_budget": {
            "message": "This value cannot be edited because the ad group is on Autopilot.",
            "enabled": False,
        },
    },
    "bid_modifier": {"id": None, "modifier": None, "source_slug": None, "target": "gravity", "type": "SOURCE"},
    "notifications": {},
}

SOURCE_1__CONTENT_AD_1 = {
    "source_id": 1,
    "content_ad_id": 1,
    "ad_group_id": 1,
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "title": "Title 1",
    "creative_type": "Content ad",
    "creative_size": "200x300",
    "description": "Example description",
    "brand_name": "Example",
    "archived": False,
    "name": "Title 1",
    "display_url": "example.com",
    "call_to_action": "Call to action",
    "label": "",
    "tracker_urls": ["http://testurl1.com", "http://testurl2.com"],
    "image_hash": "100",
    "image_urls": {
        "square": "/100.jpg?w=300&h=300&fit=crop&crop=center",
        "landscape": "/100.jpg?w=720&h=450&fit=crop&crop=center",
        "portrait": "/100.jpg?w=375&h=480&fit=crop&crop=center",
        "icon": "/1000.jpg?w=300&h=300&fit=crop&crop=center",
        "image": "/100.jpg?w=200&h=300&fit=crop&crop=center",
        "ad_tag": None,
    },
    "batch_id": 1,
    "amplify_live_preview_link": "https://www.taste.com.au/recipes/tandoori-roast-cauliflower-rice/g9h9ol5t?_b1_ad_group_id=1&_b1_cpm=500&_b1_no_targeting=1",
    "batch_name": "batch 1",
    "upload_time": datetime.datetime(2015, 2, 23, 0, 0),
    "redirector_url": R1_CREATIVE_REDIRECT_URL,
    "url": "http://testurl1.com",
    "state": 1,
    "status": 1,
    "status_per_source": {
        1: {
            "source_id": 1,
            "submission_status": 1,
            "source_name": "AdsNative",
            "source_status": 1,
            "submission_errors": None,
        }
    },
    "sspd_url": settings.SSPD_CONTENT_AD_REDIRECT_URL.format(id=1),
    "bid_modifier": {"id": None, "modifier": None, "source_slug": None, "target": "1", "type": "AD"},
    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
}

PUBLISHER_1__SOURCE_1 = {
    "publisher_id": "pub1.com__1",
    "publisher": "pub1.com",
    "domain": "pub1.com",
    "name": "pub1.com",
    "domain_link": "http://pub1.com",  # noqa
    "source_id": 1,
    "source_name": "AdsNative",
    "exchange": "AdsNative",
    "source_slug": "adsnative",
    "status": 2,
    "blacklisted": "Blacklisted",
    "blacklisted_level": "global",
    "blacklisted_level_description": "Blacklisted globally",
    "notifications": {"message": "Blacklisted globally"},
    "bid_modifier": {
        "id": None,
        "type": core.features.bid_modifiers.BidModifierType.get_name(
            core.features.bid_modifiers.BidModifierType.PUBLISHER
        ),
        "target": "pub1.com",
        "source_slug": "adsnative",
        "modifier": None,
    },
    "editable_fields": {"bid_modifier": {"message": None, "enabled": True}},
}
PUBLISHER_2__SOURCE_1 = {
    "publisher_id": "pub2.com__1",
    "publisher": "pub2.com",
    "domain": "pub2.com",
    "name": "pub2.com",
    "domain_link": "http://pub2.com",  # noqa
    "source_id": 1,
    "source_name": "AdsNative",
    "exchange": "AdsNative",
    "source_slug": "adsnative",
    "status": 3,
    "blacklisted": "Active",
    "bid_modifier": {
        "id": None,
        "type": core.features.bid_modifiers.BidModifierType.get_name(
            core.features.bid_modifiers.BidModifierType.PUBLISHER
        ),
        "target": "pub2.com",
        "source_slug": "adsnative",
        "modifier": None,
    },
    "editable_fields": {"bid_modifier": {"message": None, "enabled": True}},
}
PUBLISHER_2__SOURCE_2 = {
    "publisher_id": "pub2.com__2",
    "publisher": "pub2.com",
    "name": "pub2.com",
    "domain": "pub2.com",
    "domain_link": "http://pub2.com",  # noqa
    "source_id": 2,
    "source_name": "Gravity",
    "exchange": "Gravity",
    "source_slug": "gravity",
    "status": 1,
    "blacklisted": "Whitelisted",
    "blacklisted_level": "adgroup",
    "blacklisted_level_description": "Whitelisted in this ad group",
    "notifications": {"message": "Whitelisted in this ad group"},
    "bid_modifier": {
        "id": None,
        "type": core.features.bid_modifiers.BidModifierType.get_name(
            core.features.bid_modifiers.BidModifierType.PUBLISHER
        ),
        "target": "pub2.com",
        "source_slug": "gravity",
        "modifier": None,
    },
    "editable_fields": {"bid_modifier": {"message": None, "enabled": True}},
}
PUBLISHER_3__SOURCE_2 = {
    "publisher_id": "pub3.com__2",
    "publisher": "pub3.com",
    "domain": "pub3.com",
    "name": "pub3.com",
    "domain_link": "http://pub3.com",  # noqa
    "source_id": 2,
    "source_name": "Gravity",
    "exchange": "Gravity",
    "source_slug": "gravity",
    "status": 2,
    "blacklisted": "Blacklisted",
    "blacklisted_level": "adgroup",
    "blacklisted_level_description": "Blacklisted in this ad group",
    "notifications": {"message": "Blacklisted in this ad group"},
    "bid_modifier": {
        "id": None,
        "type": core.features.bid_modifiers.BidModifierType.get_name(
            core.features.bid_modifiers.BidModifierType.PUBLISHER
        ),
        "target": "pub3.com",
        "source_slug": "gravity",
        "modifier": None,
    },
    "editable_fields": {"bid_modifier": {"message": None, "enabled": True}},
}
PUBLISHER_4__SOURCE_2 = {
    "publisher_id": "pub4.com__2",
    "publisher": "pub4.com",
    "name": "pub4.com",
    "domain": "pub4.com",
    "domain_link": "http://pub4.com",  # noqa
    "source_id": 2,
    "source_name": "Gravity",
    "exchange": "Gravity",
    "source_slug": "gravity",
    "status": 1,
    "blacklisted": "Whitelisted",
    "blacklisted_level": "campaign",
    "blacklisted_level_description": "Whitelisted in this campaign",
    "notifications": {"message": "Whitelisted in this campaign"},
    "bid_modifier": {
        "id": None,
        "type": core.features.bid_modifiers.BidModifierType.get_name(
            core.features.bid_modifiers.BidModifierType.PUBLISHER
        ),
        "target": "pub4.com",
        "source_slug": "gravity",
        "modifier": None,
    },
    "editable_fields": {"bid_modifier": {"message": None, "enabled": True}},
}
PUBLISHER_5__SOURCE_2 = {
    "publisher_id": "pub5.com__2",
    "publisher": "pub5.com",
    "name": "pub5.com",
    "domain": "pub5.com",
    "domain_link": "http://pub5.com",  # noqa
    "source_id": 2,
    "source_name": "Gravity",
    "exchange": "Gravity",
    "source_slug": "gravity",
    "status": 2,
    "blacklisted": "Blacklisted",
    "blacklisted_level": PublisherBlacklistLevel.ACCOUNT,
    "blacklisted_level_description": "Blacklisted in this account",
    "notifications": {"message": "Blacklisted in this account"},
    "bid_modifier": {
        "id": None,
        "type": core.features.bid_modifiers.BidModifierType.get_name(
            core.features.bid_modifiers.BidModifierType.PUBLISHER
        ),
        "target": "pub5.com",
        "source_slug": "gravity",
        "modifier": None,
    },
    "editable_fields": {"bid_modifier": {"message": None, "enabled": True}},
}


@patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
@patch("utils.sspd_client.get_content_ad_status", MagicMock())
class QueryTestCase(BaseTestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def test_query_all_accounts_break_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            1,
        )

        self.assertEqual(rows, [ACCOUNT_1])

    def test_query_all_accounts_break_source(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_all_accounts_break_account_source(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id", "source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"account_id": 1}],
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [dict_join({"account_id": 1}, SOURCE_1), dict_join({"account_id": 1}, SOURCE_2)])

    def test_query_all_accounts_break_source_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "name",
            0,
            1,
        )

        self.assertEqual(rows, [dict_join({"source_id": 1}, ACCOUNT_1), dict_join({"source_id": 2}, ACCOUNT_1)])

    def test_query_all_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.filter(pk=1),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "name",
            0,
            1,
        )

        self.assertEqual(rows, [dict_join({"source_id": 1}, CAMPAIGN_1), dict_join({"source_id": 2}, CAMPAIGN_1)])

    def test_query_all_accounts_break_account_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id", "campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.filter(pk=1),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"account_id": 1}, {"account_id": 2}],
            "name",
            0,
            1,
        )

        self.assertEqual(rows, [dict_join({"account_id": 1}, CAMPAIGN_1)])

    def test_query_accounts_break_campaign(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [CAMPAIGN_1, CAMPAIGN_2])

    def test_query_accounts_break_source(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_accounts_break_campaign_source(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["campaign_id", "source_id"],
            {
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign__account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"campaign_id": 1}, {"campaign_id": 2}],
            "name",
            0,
            2,
        )

        self.assertEqual(
            rows,
            [
                dict_join({"campaign_id": 1}, SOURCE_1),
                dict_join({"campaign_id": 1}, SOURCE_2),
                dict_join({"campaign_id": 2}, SOURCE_1),
            ],
        )

    def test_query_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "name",
            0,
            2,
        )

        self.assertEqual(
            rows,
            [
                dict_join({"source_id": 1}, CAMPAIGN_1),
                dict_join({"source_id": 1}, CAMPAIGN_2),
                dict_join({"source_id": 2}, CAMPAIGN_1),
            ],
        )

    def test_query_accounts_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "ad_group_id"],
            {
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "name",
            0,
            2,
        )

        self.assertEqual(
            rows,
            [
                dict_join({"source_id": 1}, AD_GROUP_1),
                dict_join({"source_id": 1}, AD_GROUP_2),
                dict_join({"source_id": 2}, AD_GROUP_1),
                dict_join({"source_id": 2}, AD_GROUP_2),
            ],
        )

    def test_query_accounts_break_campaign_ad_group_not_allowed(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["campaign_id", "ad_group_id"],
            {
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"campaign_id": 1}, {"campaign_id": 2}],  # campaign 2 is not allowed
            "name",
            0,
            2,
        )

        # campaign_id: 2 does not get queried
        self.assertEqual(rows, [dict_join({"campaign_id": 1}, AD_GROUP_1), dict_join({"campaign_id": 1}, AD_GROUP_2)])

    def test_query_accounts_break_campaign_ad_group(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["campaign_id", "ad_group_id"],
            {
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"campaign_id": 1}],
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [dict_join({"campaign_id": 1}, AD_GROUP_1), dict_join({"campaign_id": 1}, AD_GROUP_2)])

    def test_query_campaigns_break_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["ad_group_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [AD_GROUP_BASE_1, AD_GROUP_BASE_2])

    def test_query_campaigns_break_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["ad_group_id", "source_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group__campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"ad_group_id": 1}, {"ad_group_id": 2}],
            "name",
            0,
            2,
        )

        self.assertEqual(
            rows,
            [
                dict_join({"ad_group_id": 1}, SOURCE_1),
                dict_join({"ad_group_id": 1}, SOURCE_2),
                dict_join({"ad_group_id": 2}, SOURCE_1),
                dict_join({"ad_group_id": 2}, SOURCE_2),
            ],
        )

    def test_query_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["source_id", "ad_group_id"],
            {
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "campaign": models.Campaign.objects.get(pk=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "name",
            0,
            2,
        )

        self.assertEqual(
            rows,
            [
                dict_join({"source_id": 1}, AD_GROUP_1),
                dict_join({"source_id": 1}, AD_GROUP_2),
                dict_join({"source_id": 2}, AD_GROUP_1),
                dict_join({"source_id": 2}, AD_GROUP_2),
            ],
        )

    @patch("utils.redirector.construct_redirector_url")
    def test_query_ad_groups_break_content_ad(self, mock_construct_redirector_url):
        mock_construct_redirector_url.return_value = R1_CREATIVE_REDIRECT_URL
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["content_ad_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [CONTENT_AD_1, CONTENT_AD_2])

    def test_query_ad_groups_break_content_ad_source(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["content_ad_id", "source_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"content_ad_id": 1}],
            "name",
            0,
            2,
        )

        self.assertEqual(
            rows,
            [dict_join({"content_ad_id": 1}, AD_GROUP_SOURCE_1), dict_join({"content_ad_id": 1}, AD_GROUP_SOURCE_2)],
        )

    def test_query_ad_groups_break_source(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [AD_GROUP_SOURCE_1, AD_GROUP_SOURCE_2])

    @patch("utils.redirector.construct_redirector_url")
    def test_query_ad_groups_break_source_content_ad(self, mock_construct_redirector_url):
        mock_construct_redirector_url.return_value = R1_CREATIVE_REDIRECT_URL
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["source_id", "content_ad_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(pk=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}],
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [SOURCE_1__CONTENT_AD_1])

    def test_query_ad_groups_break_publishers(self):
        # this query is not used in the wild as we always perform RS query and than dash for publishers
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["publisher_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
                "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 3, 5]),
                "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4]),
                "publisher_group_targeting": {
                    "ad_group": {"included": set([2]), "excluded": set([3])},
                    "campaign": {"included": set([4]), "excluded": set()},
                    "account": {"included": set(), "excluded": set([5])},
                    "global": {"excluded": set([1])},
                },
            },
            None,
            "name",
            0,
            4,
        )

        self.assertEqual(rows, [PUBLISHER_1__SOURCE_1, PUBLISHER_2__SOURCE_2, PUBLISHER_5__SOURCE_2])

    def test_query_ad_groups_break_placements(self):
        # for the purpose of testing we reuse and slightly modify
        # the existing publisher group entries and constants
        models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 2, 3, 4, 5]).update(
            placement="someplacement"
        )

        def create_publisher_source_for_placement(publisher_source):
            publisher_source = copy.deepcopy(publisher_source)
            del publisher_source["publisher_id"]
            placement_id = publisher_helpers.create_placement_id(
                publisher_source["publisher"], publisher_source["source_id"], "someplacement"
            )
            publisher_source.update(
                {"placement_id": placement_id, "name": "someplacement", "placement": "someplacement"}
            )
            publisher_source["bid_modifier"].update(
                {
                    "target": placement_id,
                    "type": core.features.bid_modifiers.BidModifierType.get_name(
                        core.features.bid_modifiers.BidModifierType.PLACEMENT
                    ),
                }
            )
            return publisher_source

        p1_s1 = create_publisher_source_for_placement(PUBLISHER_1__SOURCE_1)
        p2_s2 = create_publisher_source_for_placement(PUBLISHER_2__SOURCE_2)
        p5_s2 = create_publisher_source_for_placement(PUBLISHER_5__SOURCE_2)

        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["placement_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
                "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 3, 5]),
                "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4]),
                "publisher_group_targeting": {
                    "ad_group": {"included": set([2]), "excluded": set([3])},
                    "campaign": {"included": set([4]), "excluded": set()},
                    "account": {"included": set(), "excluded": set([5])},
                    "global": {"excluded": set([1])},
                },
            },
            None,
            "name",
            0,
            4,
        )

        self.assertEqual(rows, [p1_s1, p2_s2, p5_s2])


@patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
class QueryOrderTestCase(BaseTestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def test_query_campaigns_break_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["ad_group_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [AD_GROUP_BASE_1, AD_GROUP_BASE_2])

        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["ad_group_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "-name",
            0,
            2,
        )

        self.assertEqual(rows, [AD_GROUP_BASE_2, AD_GROUP_BASE_1])

    def test_query_campaigns_break_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "name",
            0,
            2,
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "-name",
            0,
            2,
        )

        self.assertEqual(rows, [SOURCE_2, SOURCE_1])


@patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
@patch("utils.sspd_client.get_content_ad_status", MagicMock())
class QueryForRowsTestCase(BaseTestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def test_query_for_rows_all_accounts_break_account(self):
        rows = api_breakdowns.query_for_rows(
            [{"account_id": 1, "clicks": 1}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [{"account_id": 1}],
        )

        self.assertEqual(rows, [ACCOUNT_1])

    def test_query_for_rows_all_accounts_break_account_no_rows(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(rows, [ACCOUNT_1])

    def test_query_for_rows_all_accounts_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [{"source_id": 1, "clicks": 11}, {"source_id": 2, "clicks": 22}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [{"source_id": 1, "clicks": 11}, {"source_id": 2, "clicks": 22}],
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_for_rows_all_accounts_break_source_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [{"source_id": 1, "clicks": 11}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [{"source_id": 1}],
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_for_rows_all_accounts_break_source_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            1,
            2,
            [{"source_id": 1}],
        )

        self.assertEqual(rows, [SOURCE_2])

    def test_query_for_rows_all_accounts_break_account_source(self):
        rows = api_breakdowns.query_for_rows(
            [{"account_id": 1, "source_id": 1, "clicks": 11}, {"account_id": 1, "source_id": 2, "clicks": 12}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id", "source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"account_id": 1}],
            "clicks",
            0,
            2,
            [{"account_id": 1, "source_id": 1}, {"account_id": 1, "source_id": 2}],
        )

        self.assertEqual(rows, [dict_join({"account_id": 1}, SOURCE_1), dict_join({"account_id": 1}, SOURCE_2)])

    def test_query_for_rows_all_accounts_break_account_source_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [{"account_id": 1, "source_id": 1, "clicks": 11}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id", "source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"account_id": 1}],
            "clicks",
            0,
            2,
            [{"account_id": 1, "source_id": 1}],
        )

        self.assertEqual(rows, [dict_join({"account_id": 1}, SOURCE_1), dict_join({"account_id": 1}, SOURCE_2)])

    def test_query_for_rows_all_accounts_break_account_source_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["account_id", "source_id"],
            {
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"account_id": 1}],
            "clicks",
            1,
            2,
            [{"account_id": 1, "source_id": 1}],
        )

        self.assertEqual(rows, [dict_join({"account_id": 1}, SOURCE_2)])

    def test_query_for_rows_all_accounts_break_source_account(self):
        rows = api_breakdowns.query_for_rows(
            [{"account_id": 1, "source_id": 1, "clicks": 11}, {"account_id": 1, "source_id": 2, "clicks": 12}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "clicks",
            0,
            2,
            [{"account_id": 1, "source_id": 1}, {"account_id": 1, "source_id": 2}],
        )

        self.assertEqual(rows, [dict_join({"source_id": 1}, ACCOUNT_1), dict_join({"source_id": 2}, ACCOUNT_1)])

    def test_query_for_rows_all_accounts_break_source_account_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [{"account_id": 1, "source_id": 2, "clicks": 12}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "clicks",
            0,
            2,
            [{"account_id": 1, "source_id": 2}],
        )

        self.assertEqual(rows, [dict_join({"source_id": 1}, ACCOUNT_1), dict_join({"source_id": 2}, ACCOUNT_1)])

    def test_query_for_rows_all_accounts_break_source_account_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "clicks",
            1,
            2,
            [{"account_id": 1, "source_id": 1}],
        )

        self.assertEqual(rows, [])  # all rows were already shown

    def test_query_for_rows_all_accounts_break_source_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [{"campaign_id": 1, "source_id": 1, "clicks": 11}, {"campaign_id": 1, "source_id": 2, "clicks": 12}],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "clicks",
            0,
            2,
            [{"campaign_id": 1, "source_id": 1}, {"campaign_id": 1, "source_id": 2}],
        )

        self.assertEqual(
            rows,
            [
                dict_join({"source_id": 1}, CAMPAIGN_1),
                dict_join({"source_id": 1}, CAMPAIGN_2),
                dict_join({"source_id": 2}, CAMPAIGN_1),
            ],
        )

    def test_query_for_rows_all_accounts_break_source_campaign_no_rows(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(
            rows,
            [
                dict_join({"source_id": 1}, CAMPAIGN_1),
                dict_join({"source_id": 1}, CAMPAIGN_2),
                dict_join({"source_id": 2}, CAMPAIGN_1),
            ],
        )

    def test_query_for_rows_accounts_break_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [{"campaign_id": 1, "clicks": 11}, {"campaign_id": 2, "clicks": 22}],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign__account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(rows, [CAMPAIGN_1, CAMPAIGN_2])

    def test_query_for_rows_accounts_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [{"source_id": 1, "clicks": 11}, {"source_id": 2, "clicks": 22}],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign__account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_for_rows_accounts_break_campaign_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {"campaign_id": 1, "source_id": 1, "clicks": 11},
                {"campaign_id": 1, "source_id": 2, "clicks": 12},
                {"campaign_id": 2, "source_id": 1, "clicks": 21},
                {"campaign_id": 2, "source_id": 2, "clicks": 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["campaign_id", "source_id"],
            {
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign__account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"campaign_id": 1}, {"campaign_id": 2}],
            "clicks",
            0,
            2,
            [
                {"campaign_id": 1, "source_id": 1},
                {"campaign_id": 1, "source_id": 2},
                {"campaign_id": 2, "source_id": 1},
                {"campaign_id": 2, "source_id": 2},
            ],
        )

        # source_id: 2 was not added to campaign
        self.assertEqual(
            rows,
            [
                dict_join({"campaign_id": 1}, SOURCE_1),
                dict_join({"campaign_id": 1}, SOURCE_2),
                dict_join({"campaign_id": 2}, SOURCE_1),
            ],
        )

    def test_query_for_rows_accounts_break_source_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [
                {"campaign_id": 1, "source_id": 1, "clicks": 11},
                {"campaign_id": 1, "source_id": 2, "clicks": 12},
                {"campaign_id": 2, "source_id": 1, "clicks": 21},
                {"campaign_id": 2, "source_id": 2, "clicks": 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ["source_id", "campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "account": models.Account.objects.get(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "clicks",
            0,
            2,
            [
                {"campaign_id": 1, "source_id": 1, "clicks": 11},
                {"campaign_id": 1, "source_id": 2, "clicks": 12},
                {"campaign_id": 2, "source_id": 1, "clicks": 21},
                {"campaign_id": 2, "source_id": 2, "clicks": 22},
            ],
        )

        self.assertEqual(
            rows,
            [
                dict_join({"source_id": 1}, CAMPAIGN_1),
                dict_join({"source_id": 1}, CAMPAIGN_2),
                dict_join({"source_id": 2}, CAMPAIGN_1),
            ],
        )

    def test_query_for_rows_campaigns_break_ad_group(self):
        rows = api_breakdowns.query_for_rows(
            [{"ad_group_id": 1, "clicks": 11}, {"ad_group_id": 2, "clicks": 22}],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["ad_group_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(rows, [AD_GROUP_BASE_1, AD_GROUP_BASE_2])

    def test_query_for_rows_campaigns_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [{"source_id": 1, "clicks": 11}, {"source_id": 2, "clicks": 22}],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_query_for_rows_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {"ad_group_id": 1, "source_id": 1, "clicks": 11},
                {"ad_group_id": 1, "source_id": 2, "clicks": 12},
                {"ad_group_id": 2, "source_id": 1, "clicks": 21},
                {"ad_group_id": 2, "source_id": 2, "clicks": 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["ad_group_id", "source_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group__campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"ad_group_id": 1}, {"ad_group_id": 2}],
            "clicks",
            0,
            2,
            [
                {"ad_group_id": 1, "source_id": 1, "clicks": 11},
                {"ad_group_id": 1, "source_id": 2, "clicks": 12},
                {"ad_group_id": 2, "source_id": 1, "clicks": 21},
                {"ad_group_id": 2, "source_id": 2, "clicks": 22},
            ],
        )

        self.assertEqual(
            rows,
            [
                dict_join({"ad_group_id": 1}, SOURCE_1),
                dict_join({"ad_group_id": 1}, SOURCE_2),
                dict_join({"ad_group_id": 2}, SOURCE_1),
                dict_join({"ad_group_id": 2}, SOURCE_2),
            ],
        )

    def test_query_for_rows_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query_for_rows(
            [
                {"ad_group_id": 1, "source_id": 1, "clicks": 11},
                {"ad_group_id": 1, "source_id": 2, "clicks": 12},
                {"ad_group_id": 2, "source_id": 1, "clicks": 21},
                {"ad_group_id": 2, "source_id": 2, "clicks": 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ["source_id", "ad_group_id"],
            {
                "campaign": models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group__campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            [{"source_id": 1}, {"source_id": 2}],
            "clicks",
            0,
            2,
            [
                {"ad_group_id": 1, "source_id": 1, "clicks": 11},
                {"ad_group_id": 1, "source_id": 2, "clicks": 12},
                {"ad_group_id": 2, "source_id": 1, "clicks": 21},
                {"ad_group_id": 2, "source_id": 2, "clicks": 22},
            ],
        )

        self.assertEqual(
            rows,
            [
                dict_join({"source_id": 1}, AD_GROUP_1),
                dict_join({"source_id": 1}, AD_GROUP_2),
                dict_join({"source_id": 2}, AD_GROUP_1),
                dict_join({"source_id": 2}, AD_GROUP_2),
            ],
        )

    @patch("utils.redirector.construct_redirector_url")
    def test_query_for_rows_ad_groups_break_content_ad(self, mock_construct_redirector_url):
        mock_construct_redirector_url.return_value = R1_CREATIVE_REDIRECT_URL
        rows = api_breakdowns.query_for_rows(
            [{"content_ad_id": 1, "clicks": 11}, {"content_ad_id": 2, "clicks": 22}],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["content_ad_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(rows, [CONTENT_AD_1, CONTENT_AD_2])

    def test_query_for_rows_ad_groups_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [{"source_id": 1, "clicks": 11}, {"source_id": 2, "clicks": 22}],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(rows, [AD_GROUP_SOURCE_1, AD_GROUP_SOURCE_2])

    def test_query_for_rows_ad_groups_break_publisher(self):
        rows = api_breakdowns.query_for_rows(
            [
                {"publisher_id": "pub1.com__1", "clicks": 11},  # blacklisted globaly
                {"publisher_id": "pub2.com__1", "clicks": 22},  # unlisted
                {"publisher_id": "pub3.com__2", "clicks": 33},  # blacklisted ad group (all sources)
                {"publisher_id": "pub4.com__2", "clicks": 44},  # whitelisted campaign (all sources)
                {"publisher_id": "pub5.com__2", "clicks": 55},  # blacklisted account
            ],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["publisher_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
                "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 3, 5]),
                "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4]),
                "publisher_group_targeting": {
                    "ad_group": {"included": set([2]), "excluded": set([3])},
                    "campaign": {"included": set([4]), "excluded": set()},
                    "account": {"included": set(), "excluded": set([5])},
                    "global": {"excluded": set([1])},
                },
            },
            None,
            "clicks",
            0,
            2,
            [],
        )

        self.assertEqual(
            rows,
            [
                PUBLISHER_1__SOURCE_1,
                PUBLISHER_2__SOURCE_1,
                PUBLISHER_3__SOURCE_2,
                PUBLISHER_4__SOURCE_2,
                PUBLISHER_5__SOURCE_2,
            ],
        )

    def test_query_for_rows_ad_groups_break_delivery(self):
        user = User.objects.get(pk=1)
        account = self.mix_account(user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.create(
            type=core.features.bid_modifiers.BidModifierType.DEVICE,
            ad_group=ad_group,
            target=str(DeviceType.DESKTOP),
            modifier=2.0,
        )
        rows = api_breakdowns.query_for_rows(
            [{"device_type": DeviceType.DESKTOP}],
            Level.AD_GROUPS,
            user,
            ["device_type"],
            {"ad_group": ad_group},
            None,
            "clicks",
            0,
            2,
            [],
        )
        self.assertEqual(
            rows,
            [
                {
                    "device_type": DeviceType.DESKTOP,
                    "bid_modifier": {
                        "id": bid_modifier.id,
                        "type": "DEVICE",
                        "source_slug": bid_modifier.source_slug,
                        "target": "DESKTOP",
                        "modifier": bid_modifier.modifier,
                    },
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                }
            ],
        )

    def test_query_for_rows_ad_groups_break_delivery_os(self):
        user = User.objects.get(pk=1)
        account = self.mix_account(user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.create(
            type=core.features.bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            ad_group=ad_group,
            target=OperatingSystem.MACOSX,
            modifier=2.0,
        )
        rows = api_breakdowns.query_for_rows(
            [{"device_os": "macOS"}],
            Level.AD_GROUPS,
            user,
            ["device_os"],
            {"ad_group": ad_group},
            None,
            "clicks",
            0,
            2,
            [],
        )
        self.assertEqual(
            rows,
            [
                {
                    "device_os": OperatingSystem.MACOSX,
                    "bid_modifier": {
                        "id": bid_modifier.id,
                        "type": "OPERATING_SYSTEM",
                        "source_slug": bid_modifier.source_slug,
                        "target": "MACOSX",
                        "modifier": bid_modifier.modifier,
                    },
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                }
            ],
        )

    def test_query_for_rows_ad_groups_break_delivery_stats_only(self):
        rows = api_breakdowns.query_for_rows(
            [{"device_type": DeviceType.DESKTOP}],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ["device_type"],
            {"ad_group": models.AdGroup.objects.get(pk=1)},
            None,
            "clicks",
            0,
            2,
            [],
        )
        self.assertEqual(
            rows,
            [
                {
                    "device_type": DeviceType.DESKTOP,
                    "bid_modifier": {
                        "id": None,
                        "type": "DEVICE",
                        "source_slug": None,
                        "target": "DESKTOP",
                        "modifier": None,
                    },
                    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
                }
            ],
        )


class HelpersTestCase(BaseTestCase):
    def test_get_adjusted_limits_for_additional_rows(self):

        self.assertEqual(helpers.get_adjusted_limits_for_additional_rows(list(range(5)), list(range(5)), 0, 10), (0, 5))

        self.assertEqual(helpers.get_adjusted_limits_for_additional_rows([], list(range(5)), 5, 10), (0, 10))

        self.assertEqual(helpers.get_adjusted_limits_for_additional_rows([], list(range(5)), 10, 10), (5, 10))

        self.assertEqual(
            helpers.get_adjusted_limits_for_additional_rows(list(range(5)), list(range(15)), 10, 10), (0, 5)
        )

    def test_get_default_order(self):

        self.assertEqual(api_breakdowns.get_default_order("source_id", "-clicks"), ["-name", "-source_id"])

        self.assertEqual(api_breakdowns.get_default_order("source_id", "clicks"), ["name", "source_id"])

        self.assertEqual(api_breakdowns.get_default_order("ad_group_id", "clicks"), ["name", "ad_group_id"])

    def test_make_rows(self):
        loader = mock.MagicMock()
        loader.objs_ids = [1, 2, 3]

        self.assertCountEqual(
            augmenter.make_dash_rows("account_id", loader, None),
            [{"account_id": 1}, {"account_id": 2}, {"account_id": 3}],
        )

        self.assertCountEqual(
            augmenter.make_dash_rows("account_id", loader, {"source_id": 2}),
            [{"account_id": 1, "source_id": 2}, {"account_id": 2, "source_id": 2}, {"account_id": 3, "source_id": 2}],
        )
