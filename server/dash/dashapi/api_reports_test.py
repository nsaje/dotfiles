import copy
import datetime
from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from mock import MagicMock
from mock import patch

from dash import constants
from dash import models
from dash.dashapi import api_reports
from zemauth.models import User

R1_CREATIVE_REDIRECT_URL = "https://r1.zemanta.com/creative/123"
ACCOUNT_1 = {
    "account": "test account 1",
    "agency_id": "",
    "account_id": 1,
    "archived": False,
    "name": "test account 1",
    "status": "PAUSED",
    "account_status": "PAUSED",
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
    "campaign": "test campaign 1",
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "archived": False,
    "name": "test campaign 1",
    "status": "ACTIVE",
    "campaign_status": "ACTIVE",
    "campaign_manager": "supertestuser@test.com",
    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=1),
    "campaign_type": constants.CampaignType.get_text(constants.CampaignType.CONTENT),
    "daily_budget": 0,
}
CAMPAIGN_2 = {
    "campaign": "test campaign 2",
    "campaign_id": 2,
    "account_id": 1,
    "agency_id": None,
    "archived": True,
    "name": "test campaign 2",
    "status": "PAUSED",
    "campaign_status": "PAUSED",
    "campaign_manager": "mad.max@zemanta.com",
    "sspd_url": settings.SSPD_CAMPAIGN_REDIRECT_URL.format(id=2),
    "campaign_type": constants.CampaignType.get_text(constants.CampaignType.CONTENT),
    "daily_budget": 0,
}

AD_GROUP_1 = {
    "ad_group": "test adgroup 1",
    "ad_group_id": 1,
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "archived": False,
    "name": "test adgroup 1",
    "status": "ENABLED",
    "ad_group_status": "ENABLED",
    "state": 1,
    "sspd_url": settings.SSPD_AD_GROUP_REDIRECT_URL.format(id=1),
}
AD_GROUP_2 = {
    "ad_group": "test adgroup 2",
    "ad_group_id": 2,
    "campaign_id": 1,
    "account_id": 1,
    "agency_id": None,
    "archived": False,
    "name": "test adgroup 2",
    "status": "PAUSED",
    "ad_group_status": "PAUSED",
    "state": 2,
    "sspd_url": settings.SSPD_AD_GROUP_REDIRECT_URL.format(id=2),
}

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
    "content_ad": "Title 1",
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
    "image_url": "/100.jpg?w=200&h=300&fit=crop&crop=center",
    "amplify_live_preview_link": "https://www.taste.com.au/recipes/tandoori-roast-cauliflower-rice/g9h9ol5t?_b1_ad_group_id=1&_b1_cpm=500&_b1_no_targeting=1",
    "batch_id": 1,
    "batch_name": "batch 1",
    "upload_time": datetime.datetime(2015, 2, 23, 0, 0),
    "redirector_url": R1_CREATIVE_REDIRECT_URL,
    "url": "http://testurl1.com",
    "tracker_urls": ["http://testurl1.com", "http://testurl2.com"],
    "state": 1,
    "status": "ENABLED",
    "content_ad_status": "ENABLED",
    "sspd_url": settings.SSPD_CONTENT_AD_REDIRECT_URL.format(id=1),
    "bid_modifier": {
        "bid_max": 1.0,
        "bid_min": 1.0,
        "id": None,
        "modifier": None,
        "source_slug": None,
        "target": "1",
        "type": "AD",
    },
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
    "content_ad": "Title 2",
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
    "image_url": "/200.jpg?w=200&h=300&fit=crop&crop=center",
    "amplify_live_preview_link": "https://www.taste.com.au/recipes/tandoori-roast-cauliflower-rice/g9h9ol5t?_b1_ad_group_id=1&_b1_cpm=500&_b1_no_targeting=1",
    "batch_id": 1,
    "batch_name": "batch 1",
    "upload_time": datetime.datetime(2015, 2, 23, 0, 0),
    "redirector_url": R1_CREATIVE_REDIRECT_URL,
    "url": "http://testurl2.com",
    "tracker_urls": [],
    "state": 2,
    "status": "PAUSED",
    "content_ad_status": "PAUSED",
    "sspd_url": settings.SSPD_CONTENT_AD_REDIRECT_URL.format(id=2),
    "bid_modifier": {
        "bid_max": 1.0,
        "bid_min": 1.0,
        "id": None,
        "modifier": None,
        "source_slug": None,
        "target": "2",
        "type": "AD",
    },
    "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
}

SOURCE_1 = {
    "archived": False,
    "maintenance": False,
    "name": "AdsNative",
    "source_id": 1,
    "source_slug": "adsnative",
    "id": 1,
    "source": "AdsNative",
}
SOURCE_2 = {
    "archived": False,
    "maintenance": False,
    "name": "Gravity",
    "source_id": 2,
    "source_slug": "gravity",
    "id": 2,
    "source": "Gravity",
}

# sources on ad group level
AD_GROUP_SOURCE_1 = {
    "source_id": 1,
    "source_slug": "adsnative",
    "id": 1,
    "name": "AdsNative",
    "source": "AdsNative",
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
    "status": "ENABLED",
    "source_status": "ENABLED",
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
    "notifications": {},
}
AD_GROUP_SOURCE_2 = {
    "source_id": 2,
    "source_slug": "gravity",
    "id": 2,
    "name": "Gravity",
    "source": "Gravity",
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
    "status": "PAUSED",
    "source_status": "PAUSED",
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
    "notifications": {},
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
    "source": "AdsNative",
    "status": "BLACKLISTED",
    "publisher_status": "BLACKLISTED",
    "blacklisted": "Blacklisted",
    "blacklisted_level": "GLOBAL",
    "blacklisted_level_description": "Blacklisted globally",
    "notifications": {"message": "Blacklisted globally"},
    "bid_modifier": None,
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
    "source": "AdsNative",
    "status": "ACTIVE",
    "publisher_status": "ACTIVE",
    "blacklisted": "Active",
    "blacklisted_level": "",
    "bid_modifier": None,
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
    "source": "Gravity",
    "status": "WHITELISTED",
    "publisher_status": "WHITELISTED",
    "blacklisted": "Whitelisted",
    "blacklisted_level": "AD GROUP",
    "blacklisted_level_description": "Whitelisted in this ad group",
    "notifications": {"message": "Whitelisted in this ad group"},
    "bid_modifier": None,
    "editable_fields": {"bid_modifier": {"message": None, "enabled": True}},
}


@patch("utils.sspd_client.get_content_ad_status", MagicMock())
class AnnotateTest(TestCase):
    fixtures = ["test_api_breakdowns"]
    maxDiff = None

    def test_annotate_accounts(self):
        rows = [{"account_id": 1}]
        api_reports.annotate(
            rows,
            User.objects.get(pk=1),
            ["account_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.all(),
                "show_archived": False,
                "filtered_sources": models.Source.objects.all(),
            },
            constants.Level.ALL_ACCOUNTS,
        )

        self.assertEqual(rows, [ACCOUNT_1])

    def test_annotate_campaigns(self):
        rows = [{"campaign_id": 1}, {"campaign_id": 2}]
        api_reports.annotate(
            rows,
            User.objects.get(pk=1),
            ["campaign_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_campaigns": models.Campaign.objects.filter(account_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            constants.Level.ACCOUNTS,
        )

        self.assertEqual(rows, [CAMPAIGN_1, CAMPAIGN_2])

    def test_annotate_ad_groups(self):
        rows = [{"ad_group_id": 1}, {"ad_group_id": 2}]
        api_reports.annotate(
            rows,
            User.objects.get(pk=1),
            ["ad_group_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_ad_groups": models.AdGroup.objects.filter(campaign_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            constants.Level.CAMPAIGNS,
        )

        self.assertEqual(rows, [AD_GROUP_1, AD_GROUP_2])

    @patch("utils.redirector.construct_redirector_url")
    def test_annotate_content_ads(self, mock_construct_redirector_url):
        mock_construct_redirector_url.return_value = R1_CREATIVE_REDIRECT_URL
        rows = [{"content_ad_id": 1}, {"content_ad_id": 2}]
        api_reports.annotate(
            rows,
            User.objects.get(pk=1),
            ["content_ad_id"],
            {
                "ad_group": models.AdGroup.objects.get(pk=1),
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group_id=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            constants.Level.AD_GROUPS,
        )
        content_ad_1 = CONTENT_AD_1.copy()
        content_ad_2 = CONTENT_AD_2.copy()
        content_ad_1.update({"bid_modifier": None})
        content_ad_2.update({"bid_modifier": None})

        self.assertEqual(rows, [content_ad_1, content_ad_2])

    def test_annotate_source(self):
        rows = [{"source_id": 1}, {"source_id": 2}]
        api_reports.annotate(
            rows,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            constants.Level.CAMPAIGNS,
        )

        self.assertEqual(rows, [SOURCE_1, SOURCE_2])

    def test_annotate_ad_group_source(self):
        rows = [{"source_id": 1}, {"source_id": 2}]
        api_reports.annotate(
            rows,
            User.objects.get(pk=1),
            ["source_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
                "ad_group": models.AdGroup.objects.get(pk=1),
            },
            constants.Level.AD_GROUPS,
        )

        ad_group_source_1 = AD_GROUP_SOURCE_1.copy()
        ad_group_source_2 = AD_GROUP_SOURCE_2.copy()
        ad_group_source_1.update({"bid_modifier": None})
        ad_group_source_2.update({"bid_modifier": None})

        self.assertEqual(rows, [ad_group_source_1, ad_group_source_2])

    def test_annotate_publisher(self):
        rows = [
            {"publisher_id": "pub1.com__1", "source_id": 1},
            {"publisher_id": "pub2.com__1", "source_id": 1},
            {"publisher_id": "pub2.com__2", "source_id": 2},
        ]

        api_reports.annotate(
            rows,
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
            constants.Level.AD_GROUPS,
        )

        self.assertEqual(rows, [PUBLISHER_1__SOURCE_1, PUBLISHER_2__SOURCE_1, PUBLISHER_2__SOURCE_2])

    def test_annotate_publisher_campaign_level(self):
        rows = [
            {"publisher_id": "pub1.com__1", "source_id": 1},
            {"publisher_id": "pub2.com__1", "source_id": 1},
            {"publisher_id": "pub2.com__2", "source_id": 2},
        ]

        api_reports.annotate(
            rows,
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
            constants.Level.CAMPAIGNS,
        )

        TEMP_PUBLISHER_1__SOURCE_1 = PUBLISHER_1__SOURCE_1.copy()
        TEMP_PUBLISHER_2__SOURCE_1 = PUBLISHER_2__SOURCE_1.copy()
        TEMP_PUBLISHER_2__SOURCE_2 = PUBLISHER_2__SOURCE_2.copy()

        TEMP_PUBLISHER_1__SOURCE_1.pop("bid_modifier")
        TEMP_PUBLISHER_2__SOURCE_1.pop("bid_modifier")
        TEMP_PUBLISHER_2__SOURCE_2.pop("bid_modifier")

        TEMP_PUBLISHER_1__SOURCE_1.pop("editable_fields")
        TEMP_PUBLISHER_2__SOURCE_1.pop("editable_fields")
        TEMP_PUBLISHER_2__SOURCE_2.pop("editable_fields")

        # Publishers have the bid_modifier field only on ad_group level (see 'test_annotate_publisher').

        self.assertEqual(rows, [TEMP_PUBLISHER_1__SOURCE_1, TEMP_PUBLISHER_2__SOURCE_1, TEMP_PUBLISHER_2__SOURCE_2])

    @patch("utils.redirector.construct_redirector_url")
    def test_annotate_breakdown(self, mock_construct_redirector_url):
        mock_construct_redirector_url.return_value = R1_CREATIVE_REDIRECT_URL
        rows = [
            {"account_id": 1, "campaign_id": 1, "ad_group_id": 1, "content_ad_id": 1, "source_id": 1},
            {"account_id": 1, "campaign_id": 1, "ad_group_id": 1, "content_ad_id": 2, "source_id": 1},
        ]
        api_reports.annotate(
            rows,
            User.objects.get(pk=1),
            ["account_id", "campaign_id", "ad_group_id", "content_ad_id", "source_id"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 31),
                "allowed_accounts": models.Account.objects.filter(pk=1),
                "allowed_campaigns": models.Campaign.objects.filter(pk=1),
                "allowed_ad_groups": models.AdGroup.objects.filter(pk=1),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group_id=1),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            constants.Level.AD_GROUPS,
        )

        content_ad_1 = copy.copy(ACCOUNT_1)
        content_ad_1.update(CAMPAIGN_1)
        content_ad_1.update(AD_GROUP_1)
        content_ad_1.update(CONTENT_AD_1)
        content_ad_1.update(AD_GROUP_SOURCE_1)
        content_ad_1.update({"bid_modifier": None})

        content_ad_2 = copy.copy(ACCOUNT_1)
        content_ad_2.update(CAMPAIGN_1)
        content_ad_2.update(AD_GROUP_1)
        content_ad_2.update(CONTENT_AD_2)
        content_ad_2.update(AD_GROUP_SOURCE_1)
        content_ad_2.update({"bid_modifier": None})

        self.assertEqual(rows, [content_ad_1, content_ad_2])


@patch("utils.sspd_client.get_content_ad_status", MagicMock())
class QueryTest(TestCase):
    fixtures = ["test_api_breakdowns"]

    def test_breakdown(self):
        rows = api_reports.query(
            User.objects.get(pk=1),
            ["account_id", "campaign_id", "ad_group_id", "content_ad_id", "source_id", "day"],
            {
                "date__gte": datetime.date(2016, 7, 1),
                "date__lte": datetime.date(2016, 7, 30),
                "allowed_accounts": models.Account.objects.all(),
                "allowed_campaigns": models.Campaign.objects.all(),
                "allowed_ad_groups": models.AdGroup.objects.all(),
                "allowed_content_ads": models.ContentAd.objects.filter(ad_group_id=1),
                "ad_group": models.AdGroup.objects.get(pk=1),
                "show_archived": True,
                "filtered_sources": models.Source.objects.all(),
            },
            constants.Level.AD_GROUPS,
        )

        self.assertEqual(2 * 3 * 30, len(rows))
