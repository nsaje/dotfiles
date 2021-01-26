from decimal import Decimal

import mock
from django.test import TestCase

import stats.constants
from core.features import bid_modifiers
from core.features.bid_modifiers.service_test import add_non_publisher_bid_modifiers
from dash import constants
from dash import models
from dash.dashapi import loaders
from utils import sspd_client
from utils.magic_mixer import magic_mixer
from zemauth.models import User


class GetLoaderTest(TestCase):
    def test_get_loader(self):
        self.assertEqual(loaders.get_loader_for_dimension("content_ad_id", None), loaders.ContentAdsLoader)
        self.assertEqual(loaders.get_loader_for_dimension("ad_group_id", None), loaders.AdGroupsLoader)
        self.assertEqual(loaders.get_loader_for_dimension("campaign_id", None), loaders.CampaignsLoader)
        self.assertEqual(loaders.get_loader_for_dimension("account_id", None), loaders.AccountsLoader)
        self.assertEqual(loaders.get_loader_for_dimension("source_id", constants.Level.ACCOUNTS), loaders.SourcesLoader)
        self.assertEqual(
            loaders.get_loader_for_dimension("source_id", constants.Level.AD_GROUPS), loaders.AdGroupSourcesLoader
        )


class AccountsLoaderTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.accounts = models.Account.objects.all()
        self.sources = models.Source.objects.all()
        self.user = User.objects.get(pk=1)

        self.loader = loaders.AccountsLoader(self.accounts, self.sources, self.user)

    def test_from_constraints(self):
        loader = loaders.AccountsLoader.from_constraints(
            User.objects.get(pk=1),
            {"allowed_accounts": models.Account.objects.all(), "filtered_sources": models.Source.objects.all()},
        )

        self.assertCountEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertCountEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertCountEqual(self.loader.objs_ids, [1])
        self.assertDictEqual(self.loader.objs_map, {1: models.Account.objects.get(pk=1)})

    def test_objs_count(self):
        self.assertEqual(self.loader.objs_count, len(self.accounts))

    def test_settings_map(self):
        self.assertDictEqual(
            self.loader.settings_map,
            {
                1: {
                    "archived": False,
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "default_account_manager": "mad.max@zemanta.com",
                    "default_sales_representative": "supertestuser@test.com",
                    "default_cs_representative": "supercsuser@test.com",
                    "ob_sales_representative": None,
                    "ob_account_manager": None,
                    "account_type": constants.AccountType.get_text(constants.AccountType.ACTIVATED),
                    "settings_id": 1,
                    "salesforce_url": "",
                }
            },
        )

    def test_status_map_filtered_sources(self):
        accounts = models.Account.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.AccountsLoader(accounts, sources, self.user)

        self.assertDictEqual(
            loader.settings_map,
            {
                1: {
                    "archived": False,
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "default_account_manager": "mad.max@zemanta.com",
                    "default_sales_representative": "supertestuser@test.com",
                    "default_cs_representative": "supercsuser@test.com",
                    "ob_sales_representative": None,
                    "ob_account_manager": None,
                    "account_type": constants.AccountType.get_text(constants.AccountType.ACTIVATED),
                    "settings_id": 1,
                    "salesforce_url": "",
                }
            },
        )

    @mock.patch("automation.campaignstop.get_campaignstop_states")
    def test_status_map_campaignstop(self, mock_campaignstop):
        mock_campaignstop.return_value = {1: {"allowed_to_run": False}, 2: {"allowed_to_run": True}}

        loader = loaders.AccountsLoader(self.accounts, self.sources, self.user)
        self.assertDictEqual(
            loader.settings_map,
            {
                1: {
                    "archived": False,
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "default_account_manager": "mad.max@zemanta.com",
                    "default_sales_representative": "supertestuser@test.com",
                    "default_cs_representative": "supercsuser@test.com",
                    "ob_sales_representative": None,
                    "ob_account_manager": None,
                    "account_type": constants.AccountType.get_text(constants.AccountType.ACTIVATED),
                    "settings_id": 1,
                    "salesforce_url": "",
                }
            },
        )


class CampaignsLoaderTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.campaigns = models.Campaign.objects.all()
        self.sources = models.Source.objects.all()
        self.user = User.objects.get(pk=1)

        self.loader = loaders.CampaignsLoader(self.campaigns, self.sources, self.user)

    def test_from_constraints(self):
        loader = loaders.CampaignsLoader.from_constraints(
            User.objects.get(pk=1),
            {"allowed_campaigns": models.Campaign.objects.all(), "filtered_sources": models.Source.objects.all()},
        )

        self.assertCountEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertCountEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertCountEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(
            self.loader.objs_map, {1: models.Campaign.objects.get(pk=1), 2: models.Campaign.objects.get(pk=2)}
        )

    def test_objs_count(self):
        self.assertEqual(self.loader.objs_count, len(self.campaigns))

    def test_settings_map(self):
        self.assertDictEqual(
            self.loader.settings_map,
            {
                1: {
                    "status": constants.AdGroupRunningStatus.ACTIVE,
                    "archived": False,
                    "settings_id": 1,
                    "campaign_manager": "supertestuser@test.com",
                },
                2: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": True,
                    "settings_id": 2,
                    "campaign_manager": "mad.max@zemanta.com",
                },
            },
        )

    def test_status_map_filtered_sources(self):
        campaigns = models.Campaign.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.CampaignsLoader(campaigns, sources, self.user)

        self.assertDictEqual(
            loader.settings_map,
            {
                1: {
                    "status": constants.AdGroupRunningStatus.ACTIVE,
                    "archived": False,
                    "settings_id": 1,
                    "campaign_manager": "supertestuser@test.com",
                },
                2: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": True,
                    "settings_id": 2,
                    "campaign_manager": "mad.max@zemanta.com",
                },
            },
        )

    @mock.patch("automation.campaignstop.get_campaignstop_states")
    def test_status_map_campaignstop(self, mock_campaignstop):
        mock_campaignstop.return_value = {1: {"allowed_to_run": False}, 2: {"allowed_to_run": True}}

        campaigns = models.Campaign.objects.filter(id=1)
        sources = models.Source.objects.all()
        loader = loaders.CampaignsLoader(campaigns, sources, self.user)
        self.assertDictEqual(
            loader.settings_map,
            {
                1: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": False,
                    "settings_id": 1,
                    "campaign_manager": "supertestuser@test.com",
                }
            },
        )


class AdGroupsLoaderTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.ad_groups = models.AdGroup.objects.all()
        self.sources = models.Source.objects.all()
        self.user = User.objects.get(pk=1)

        self.loader = loaders.AdGroupsLoader(self.ad_groups, self.sources, self.user)

    def test_from_constraints(self):
        loader = loaders.AdGroupsLoader.from_constraints(
            User.objects.get(pk=1),
            {"allowed_ad_groups": models.AdGroup.objects.all(), "filtered_sources": models.Source.objects.all()},
        )

        self.assertCountEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertCountEqual(loader.settings_map, self.loader.settings_map)

    def test_settings_map(self):
        self.assertDictEqual(
            self.loader.settings_map,
            {
                1: {
                    "status": constants.AdGroupRunningStatus.ACTIVE,
                    "state": constants.AdGroupRunningStatus.ACTIVE,
                    "archived": False,
                    "settings_id": 4,
                },
                2: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "state": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": False,
                    "settings_id": 2,
                },
                3: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "state": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": True,
                    "settings_id": 3,
                },
            },
        )

    def test_base_level_settings_map(self):
        self.assertDictEqual(
            self.loader.base_level_settings_map,
            {
                1: {"campaign_has_available_budget": True},
                2: {"campaign_has_available_budget": True},
                3: {"campaign_has_available_budget": True},
            },
        )

    def test_objs(self):
        self.assertCountEqual(self.loader.objs_ids, [1, 2, 3])
        self.assertDictEqual(
            self.loader.objs_map,
            {
                1: models.AdGroup.objects.get(pk=1),
                2: models.AdGroup.objects.get(pk=2),
                3: models.AdGroup.objects.get(pk=3),
            },
        )

    def test_objs_count(self):
        self.assertEqual(self.loader.objs_count, len(self.ad_groups))

    def test_status_map_filtered_sources(self):
        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.filter(pk=2)

        loader = loaders.AdGroupsLoader(ad_groups, sources, self.user)

        self.assertDictEqual(
            loader.settings_map,
            {
                1: {
                    "status": constants.AdGroupRunningStatus.ACTIVE,
                    "state": constants.AdGroupRunningStatus.ACTIVE,
                    "archived": False,
                    "settings_id": 4,
                },
                2: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "state": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": False,
                    "settings_id": 2,
                },
                3: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "state": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": True,
                    "settings_id": 3,
                },
            },
        )

    @mock.patch("automation.campaignstop.get_campaignstop_states")
    def test_status_map_campaignstop(self, mock_campaignstop):
        mock_campaignstop.return_value = {1: {"allowed_to_run": False}, 2: {"allowed_to_run": True}}

        ad_groups = models.AdGroup.objects.all()
        sources = models.Source.objects.all()

        loader = loaders.AdGroupsLoader(ad_groups, sources, self.user)
        self.assertDictEqual(
            loader.settings_map,
            {
                1: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "state": constants.AdGroupRunningStatus.ACTIVE,
                    "archived": False,
                    "settings_id": 4,
                },
                2: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "state": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": False,
                    "settings_id": 2,
                },
                3: {
                    "status": constants.AdGroupRunningStatus.INACTIVE,
                    "state": constants.AdGroupRunningStatus.INACTIVE,
                    "archived": True,
                    "settings_id": 3,
                },
            },
        )


class ContentAdLoaderTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.content_ads = models.ContentAd.objects.all()
        self.sources = models.Source.objects.all()

        self.user = magic_mixer.blend_user()
        self.loader = loaders.ContentAdsLoader(self.content_ads, self.sources, self.user)

    def test_from_constraints(self):
        loader = loaders.ContentAdsLoader.from_constraints(
            User.objects.get(pk=1),
            {"allowed_content_ads": models.ContentAd.objects.all(), "filtered_sources": models.Source.objects.all()},
        )

        self.assertCountEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertCountEqual(loader.status_map, self.loader.status_map)

    def test_objs(self):
        self.assertCountEqual(self.loader.objs_ids, [1, 2, 3])
        self.assertDictEqual(
            self.loader.objs_map,
            {
                1: models.ContentAd.objects.get(pk=1),
                2: models.ContentAd.objects.get(pk=2),
                3: models.ContentAd.objects.get(pk=3),
            },
        )

    def test_objs_count(self):
        self.assertEqual(self.loader.objs_count, len(self.content_ads))

    def test_batch_map(self):
        self.assertDictEqual(
            self.loader.batch_map,
            {
                1: models.UploadBatch.objects.get(pk=1),
                2: models.UploadBatch.objects.get(pk=1),
                3: models.UploadBatch.objects.get(pk=2),
            },
        )

    def test_ad_group_loader(self):
        self.assertDictEqual(self.loader.ad_group_loader.objs_map, {1: models.AdGroup.objects.get(pk=1)})

    def test_ad_group_map(self):
        self.assertDictEqual(
            self.loader.ad_group_map,
            {
                1: models.AdGroup.objects.get(pk=1),
                2: models.AdGroup.objects.get(pk=1),
                3: models.AdGroup.objects.get(pk=1),
            },
        )

    def test_status_map(self):
        self.assertDictEqual(
            self.loader.status_map,
            {
                1: constants.ContentAdSourceState.ACTIVE,
                2: constants.ContentAdSourceState.ACTIVE,
                3: constants.ContentAdSourceState.INACTIVE,
            },
        )

    def test_status_map_filtered_by_sources(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        loader = loaders.ContentAdsLoader(content_ads, sources, self.user)

        self.assertDictEqual(
            loader.status_map,
            {
                1: constants.ContentAdSourceState.ACTIVE,
                2: constants.ContentAdSourceState.INACTIVE,
                3: constants.ContentAdSourceState.INACTIVE,
            },
        )

    def test_content_ads_sources_map(self):
        self.assertEqual(2, len(self.loader.content_ads_sources_map))
        self.assertCountEqual(
            self.loader.content_ads_sources_map[1],
            [models.ContentAdSource.objects.get(pk=1), models.ContentAdSource.objects.get(pk=2)],
        )
        self.assertCountEqual(self.loader.content_ads_sources_map[2], [models.ContentAdSource.objects.get(pk=3)])

    def test_content_ads_sources_map_filtered_by_sources(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        loader = loaders.ContentAdsLoader(content_ads, sources, self.user)

        self.assertDictEqual(loader.content_ads_sources_map, {1: [models.ContentAdSource.objects.get(pk=1)]})

    @mock.patch("utils.sspd_client.get_content_ad_status", mock.MagicMock())
    def test_status_per_source(self):
        self.assertDictEqual(
            self.loader.per_source_status_map,
            {
                1: {
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
                2: {
                    2: {
                        "source_id": 2,
                        "submission_status": 2,
                        "source_name": "Gravity",
                        "source_status": 2,
                        "submission_errors": None,
                    }
                },
            },
        )

    @mock.patch("utils.sspd_client.get_content_ad_status", mock.MagicMock())
    def test_status_per_source_filtered(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        loader = loaders.ContentAdsLoader(content_ads, sources, self.user)
        self.assertDictEqual(
            loader.per_source_status_map,
            {
                1: {
                    1: {
                        "source_id": 1,
                        "submission_status": 1,
                        "source_name": "AdsNative",
                        "source_status": 1,
                        "submission_errors": None,
                    }
                }
            },
        )

    @mock.patch("utils.sspd_client.get_content_ad_status", mock.MagicMock())
    def test_sspd_status_rejected(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        sspd_client.get_content_ad_status.return_value = {
            1: {1: {"status": constants.ContentAdSubmissionStatus.REJECTED, "reason": "Inappropriate content"}}
        }
        loader = loaders.ContentAdsLoader(content_ads, sources, self.user)
        self.assertDictEqual(
            loader.per_source_status_map,
            {
                1: {
                    1: {
                        "source_id": 1,
                        "submission_status": 3,
                        "source_name": "AdsNative",
                        "source_status": 1,
                        "submission_errors": "Inappropriate content",
                    }
                }
            },
        )

    @mock.patch("utils.sspd_client.get_content_ad_status", mock.MagicMock())
    def test_sspd_status_ignored(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        sspd_client.get_content_ad_status.return_value = None
        loader = loaders.ContentAdsLoader(content_ads, sources, self.user)
        self.assertDictEqual(
            loader.per_source_status_map,
            {
                1: {
                    1: {
                        "source_id": 1,
                        "submission_status": 1,
                        "source_name": "AdsNative",
                        "source_status": 1,
                        "submission_errors": None,
                    }
                }
            },
        )

    @mock.patch("utils.sspd_client.get_content_ad_status", mock.MagicMock())
    def test_sspd_status_pending(self):
        content_ads = models.ContentAd.objects.all()
        sources = models.Source.objects.filter(pk=1)

        sspd_client.get_content_ad_status.return_value = {}
        loader = loaders.ContentAdsLoader(content_ads, sources, self.user)
        self.assertDictEqual(
            loader.per_source_status_map,
            {
                1: {
                    1: {
                        "source_id": 1,
                        "submission_status": 1,
                        "source_name": "AdsNative",
                        "source_status": 1,
                        "submission_errors": None,
                    }
                }
            },
        )


class SourcesLoaderTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.sources = models.Source.objects.all()
        self.loader = loaders.SourcesLoader(self.sources, models.AdGroup.objects.all())

    def test_from_constraints(self):
        loader = loaders.SourcesLoader.from_constraints(
            User.objects.get(pk=1),
            {"allowed_ad_groups": models.AdGroup.objects.all(), "filtered_sources": models.Source.objects.all()},
        )

        self.assertCountEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertCountEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertCountEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(
            self.loader.objs_map, {1: models.Source.objects.get(pk=1), 2: models.Source.objects.get(pk=2)}
        )

    def test_objs_count(self):
        self.assertEqual(self.loader.objs_count, len(self.sources))

    def test_settings_map(self):
        self.assertDictEqual(self.loader.settings_map, {1: {}, 2: {}})

    def test_settings_map_filtered_ad_group_sources(self):
        sources = models.Source.objects.filter(pk=2)
        loader = loaders.SourcesLoader(sources, models.AdGroup.objects.all())

        self.assertDictEqual(loader.settings_map, {2: {}})


class AdGroupSourcesLoaderTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.sources = models.Source.objects.all()
        self.loader = loaders.AdGroupSourcesLoader(
            self.sources, models.AdGroup.objects.get(pk=1), User.objects.get(pk=1)
        )

    def test_from_constraints_select_loader_class(self):
        loader = loaders.AdGroupSourcesLoader.from_constraints(
            User.objects.get(pk=1),
            {"ad_group": models.AdGroup.objects.get(pk=1), "filtered_sources": models.Source.objects.all()},
        )

        self.assertCountEqual(loader.objs_ids, self.loader.objs_ids)
        self.assertCountEqual(loader.settings_map, self.loader.settings_map)

    def test_objs(self):
        self.assertCountEqual(self.loader.objs_ids, [1, 2])
        self.assertDictEqual(
            self.loader.objs_map, {1: models.Source.objects.get(pk=1), 2: models.Source.objects.get(pk=2)}
        )

    def test_objs_count(self):
        self.assertEqual(self.loader.objs_count, len(self.sources))

    def test_status_with_blockers(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.blockers = {"test-blocker": "My blocker"}
        ad_group_source.save()
        source = self.loader.settings_map[1]
        self.assertEqual(source["status"], 2)
        self.assertEqual(
            source["notifications"],
            {"important": True, "message": "This media source is enabled but it is not running because: My blocker"},
        )

    def test_settings_map_all_rtb_enabled(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_state = 1

        rtb_source = self.loader.settings_map[1]
        reg_source = self.loader.settings_map[2]

        rtb_source = self.loader.settings_map[1]
        self.assertEqual(rtb_source["state"], 1)
        self.assertEqual(rtb_source["status"], 1)
        self.assertEqual(rtb_source["daily_budget"], None)
        self.assertEqual(rtb_source["editable_fields"]["daily_budget"]["enabled"], False)

        self.assertEqual(reg_source["state"], 2)
        self.assertEqual(reg_source["status"], 2)
        self.assertEqual(reg_source["daily_budget"], Decimal("20.0"))
        self.assertEqual(reg_source["editable_fields"]["daily_budget"]["enabled"], False)

    def test_settings_map_all_rtb_enabled_and_inactive(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_state = 2

        rtb_source = self.loader.settings_map[1]
        self.assertEqual(rtb_source["state"], 1)
        self.assertEqual(rtb_source["status"], 2)
        self.assertEqual(rtb_source["daily_budget"], None)
        self.assertEqual(rtb_source["editable_fields"]["daily_budget"]["enabled"], False)

    def test_settings_map(self):
        self.assertDictEqual(
            self.loader.settings_map,
            {
                1: {
                    "state": 1,
                    "status": 1,
                    "supply_dash_disabled_message": "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
                    "daily_budget": Decimal("10.0000"),
                    "local_daily_budget": Decimal("10.0000"),
                    "bid_cpc": Decimal("0.5010"),
                    "local_bid_cpc": Decimal("0.5010"),
                    "bid_cpm": Decimal("0.4010"),
                    "local_bid_cpm": Decimal("0.4010"),
                    "editable_fields": {
                        "state": {"message": "This source must be managed manually.", "enabled": False},
                        "bid_cpc": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                        "bid_cpm": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                        "bid_modifier": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                        "daily_budget": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                    },
                    "supply_dash_url": None,
                    "notifications": {},
                },
                2: {
                    "state": 2,
                    "status": 2,
                    "supply_dash_disabled_message": "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
                    "daily_budget": Decimal("20.0000"),
                    "local_daily_budget": Decimal("20.0000"),
                    "bid_cpc": Decimal("0.5020"),
                    "local_bid_cpc": Decimal("0.5020"),
                    "bid_cpm": Decimal("0.4020"),
                    "local_bid_cpm": Decimal("0.4020"),
                    "editable_fields": {
                        "state": {"message": None, "enabled": True},
                        "bid_cpc": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                        "bid_cpm": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                        "bid_modifier": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                        "daily_budget": {
                            "message": "This value cannot be edited because the ad group is on Autopilot.",
                            "enabled": False,
                        },
                    },
                    "supply_dash_url": None,
                    "notifications": {},
                },
            },
        )

    def test_settings_map_campaign_autopilot(self):
        self.loader.campaign_settings.autopilot = True

        ap_source = self.loader.settings_map[1]
        self.assertEqual(
            ap_source["editable_fields"]["bid_cpc"],
            {"message": "This value cannot be edited because the campaign is on Autopilot.", "enabled": False},
        )
        self.assertEqual(
            ap_source["editable_fields"]["bid_cpm"],
            {"message": "This value cannot be edited because the campaign is on Autopilot.", "enabled": False},
        )
        self.assertEqual(
            ap_source["editable_fields"]["bid_modifier"],
            {"message": "This value cannot be edited because the campaign is on Autopilot.", "enabled": False},
        )
        self.assertEqual(
            ap_source["editable_fields"]["daily_budget"],
            {"message": "This value cannot be edited because the campaign is on Autopilot.", "enabled": False},
        )

    def test_totals(self):
        # only use active ad group sources
        self.assertDictEqual(
            self.loader.totals,
            {
                "daily_budget": Decimal("10.0000"),
                "local_daily_budget": Decimal("10.0000"),
                "current_daily_budget": Decimal("10.0000"),
                "local_current_daily_budget": Decimal("10.0000"),
            },
        )

    def test_totals_all_rtb_enabled(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_daily_budget = Decimal("100.00")
        self.loader.ad_group_settings.local_b1_sources_group_daily_budget = Decimal("200.00")
        self.loader.ad_group_settings.b1_sources_group_state = 1
        self.assertDictEqual(
            self.loader.totals,
            {
                "daily_budget": Decimal("100.0000"),
                "local_daily_budget": Decimal("200.0000"),
                "current_daily_budget": Decimal("100.0000"),
                "local_current_daily_budget": Decimal("200.0000"),
            },
        )

    def test_totals_all_rtb_enabled_and_inactive(self):
        self.loader.ad_group_settings.b1_sources_group_enabled = True
        self.loader.ad_group_settings.b1_sources_group_daily_budget = Decimal("100.00")
        self.loader.ad_group_settings.local_b1_sources_group_daily_budget = Decimal("200.00")
        self.loader.ad_group_settings.b1_sources_group_state = 2
        self.assertDictEqual(
            self.loader.totals,
            {
                "daily_budget": Decimal("0"),
                "local_daily_budget": Decimal("0"),
                "current_daily_budget": Decimal("0"),
                "local_current_daily_budget": Decimal("0"),
            },
        )


class PublisherBlacklistLoaderTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.publisher_group_targeting = {
            "ad_group": {
                "included": set([7]),
                "excluded": set([6]),
                1: {"included": set([7]), "excluded": set([6])},
                2: {"included": set(), "excluded": set()},
            },
            "campaign": {
                "included": set([5]),
                "excluded": set([4]),
                1: {"included": set([5]), "excluded": set([4])},
                2: {"included": set(), "excluded": set()},
            },
            "account": {
                "included": set([3]),
                "excluded": set([2]),
                1: {"included": set([3]), "excluded": set([2])},
                2: {"included": set(), "excluded": set()},
            },
            "global": {"excluded": set([1])},
        }
        self.loader = loaders.PublisherBlacklistLoader(
            models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 2, 4, 6]),
            models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[3, 5, 7]),
            self.publisher_group_targeting,
            models.Source.objects.all(),
            User.objects.get(pk=1),
        )

    def test_from_constraints(self):
        loader = loaders.PublisherBlacklistLoader.from_constraints(
            User.objects.get(pk=1),
            {
                "publisher_blacklist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 2, 4, 6]),
                "publisher_whitelist": models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[3, 5, 7]),
                "publisher_group_targeting": self.publisher_group_targeting,
                "filtered_sources": models.Source.objects.all(),
            },
        )

        self.assertCountEqual(loader.whitelist_qs, self.loader.whitelist_qs)
        self.assertCountEqual(loader.blacklist_qs, self.loader.blacklist_qs)
        self.assertCountEqual(loader.publisher_group_targeting, self.loader.publisher_group_targeting)
        self.assertCountEqual(loader.filtered_sources_qs, self.loader.filtered_sources_qs)

    def test_status_global_unlisted(self):
        row = {"publisher_id": "pubtest.com__1"}
        self.assertEqual(
            self.loader.find_blacklisted_status_by_subdomain(row),
            {"status": constants.PublisherTargetingStatus.UNLISTED},
        )

    def _subdomain_id_test(self, row, status, id_field):
        self.assertEqual(self.loader.find_blacklisted_status_by_subdomain(row), status)

        row[id_field] = 1
        self.assertEqual(self.loader.find_blacklisted_status_by_subdomain(row), status)

        row[id_field] = 2
        self.assertEqual(
            self.loader.find_blacklisted_status_by_subdomain(row),
            {"status": constants.PublisherTargetingStatus.UNLISTED},
        )
        del row[id_field]

        row["publisher_id"] = "test." + row["publisher_id"]
        self.assertEqual(self.loader.find_blacklisted_status_by_subdomain(row), status)

        row[id_field] = 1
        self.assertEqual(self.loader.find_blacklisted_status_by_subdomain(row), status)

        row[id_field] = 2
        self.assertEqual(
            self.loader.find_blacklisted_status_by_subdomain(row),
            {"status": constants.PublisherTargetingStatus.UNLISTED},
        )

    def test_status_account_blacklist(self):
        row = {"publisher_id": "pub2.com__2"}
        status = {"blacklisted_level": "account", "status": constants.PublisherTargetingStatus.BLACKLISTED}
        self._subdomain_id_test(row, status, "account_id")

    def test_status_account_whitelist(self):
        row = {"publisher_id": "pub3.com__3"}
        status = {"blacklisted_level": "account", "status": constants.PublisherTargetingStatus.WHITELISTED}
        self._subdomain_id_test(row, status, "account_id")

    def test_status_campaign_blacklist(self):
        row = {"publisher_id": "pub4.com__4"}
        status = {"blacklisted_level": "campaign", "status": constants.PublisherTargetingStatus.BLACKLISTED}
        self._subdomain_id_test(row, status, "campaign_id")

    def test_status_campaign_whitelist(self):
        row = {"publisher_id": "pub5.com__2"}
        status = {"blacklisted_level": "campaign", "status": constants.PublisherTargetingStatus.WHITELISTED}
        self._subdomain_id_test(row, status, "campaign_id")

    def test_status_ad_group_blacklist(self):
        row = {"publisher_id": "pub6.com__2"}
        status = {"blacklisted_level": "adgroup", "status": constants.PublisherTargetingStatus.BLACKLISTED}
        self._subdomain_id_test(row, status, "ad_group_id")

    def test_status_ad_group_whitelist(self):
        row = {"publisher_id": "pub7.com__2"}
        status = {"blacklisted_level": "adgroup", "status": constants.PublisherTargetingStatus.WHITELISTED}
        self._subdomain_id_test(row, status, "ad_group_id")


class PublisherBidModifierLoaderTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup, id=1)
        source = magic_mixer.blend(models.Source, id=1)
        add_non_publisher_bid_modifiers(ad_group=ad_group, source=source)
        self.bid_modifier = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            source=source,
            source_slug=source.bidder_slug,
            target="pub3.com",
            modifier=0.5,
            type=bid_modifiers.constants.BidModifierType.PUBLISHER,
        )
        user = magic_mixer.blend_user()

        self.loader = loaders.PublisherBidModifierLoader(
            models.AdGroup.objects.all().first(),
            models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1, 2, 4, 6]),
            models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[3, 5, 7]),
            {},
            models.Source.objects.all(),
            user,
        )

    def test_modifier_map(self):
        modifier_map = self.loader.modifier_map
        self.assertDictEqual(modifier_map, {(1, "pub3.com"): self.bid_modifier})


class DeliveryLoaderTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup, id=1)
        source = magic_mixer.blend(models.Source, id=1)
        self.bid_modifier = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            source=source,
            source_slug=source.bidder_slug,
            target=str(constants.DeviceType.DESKTOP),
            modifier=0.5,
            type=bid_modifiers.constants.BidModifierType.DEVICE,
        )
        self.user = magic_mixer.blend_user()

    def test_modifier_map(self):
        ad_group = models.AdGroup.objects.all().first()
        loader = loaders.DeliveryLoader(ad_group, self.user, breakdown=[stats.constants.DeliveryDimension.DEVICE])
        self.assertDictEqual(loader.objs_map, {constants.DeviceType.DESKTOP: self.bid_modifier})
