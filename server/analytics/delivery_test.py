import datetime

from django import test

import core.features.bcm
import core.features.goals
import core.features.videoassets.models
import core.models
import dash.constants
from analytics import constants
from analytics import delivery
from utils.magic_mixer import magic_mixer


class CampaignDeliveryTestCase(test.TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.account.Account, name="Account")
        self.campaign = magic_mixer.blend(core.models.campaign.Campaign, name="Campaign 1", account=self.account)
        self.campaign.settings.update(None, iab_category=dash.constants.IABCategory.IAB1_1, enable_ga_tracking=True)

        self.goal = core.features.goals.campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=self.campaign, type=dash.constants.CampaignGoalKPI.TIME_ON_SITE, primary=True
        )
        start_date = datetime.date.today() - datetime.timedelta(1)
        end_date = datetime.date.today() + datetime.timedelta(10)
        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            status=1,
            start_date=start_date,
            end_date=end_date,
            amount=100000,
        )
        self.budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign, credit=self.credit, amount=1000, start_date=start_date, end_date=end_date
        )

        self.stats_now = {"visits": 10}
        self.stats_prev = {"visits": 5}

        self.ad_group = magic_mixer.blend(core.models.ad_group.AdGroup, name="Ad Group 1", campaign=self.campaign)
        self.ad_group_settings = self.ad_group.get_current_settings().copy_settings()
        self.ad_group.settings.start_date = start_date
        self.ad_group.settings.end_date = end_date
        self.ad_group.settings.state = dash.constants.AdGroupSettingsState.ACTIVE
        self.ad_group.settings.update(None)

        self.campaign.campaign_goals = [self.goal]
        self.campaign.ad_groups_active = [self.ad_group]
        self.campaign.ending_budgets = []
        self.campaign.save(None)

    def test_iab(self):
        self.campaign.settings.iab_category = dash.constants.IABCategory.IAB24
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.stats_now, self.stats_prev),
            constants.CampaignDeliveryStatus.IAB_UNDEFINED,
        )

    def test_missing_postclick_stats(self):
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, {}, {}),
            constants.CampaignDeliveryStatus.MISSING_POSTCLICK_STATS,
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, {"visits": 0}, {"visits": 0}),
            constants.CampaignDeliveryStatus.MISSING_POSTCLICK_STATS,
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, {"visits": 10}, {}), constants.CampaignDeliveryStatus.OK
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, {"visits": 0}, {"visits": 5}),
            constants.CampaignDeliveryStatus.OK,
        )

    def test_missing_postclick_setup(self):
        self.campaign.settings.enable_ga_tracking = False
        self.campaign.settings.enable_adobe_tracking = False
        self.campaign.settings.update(None)
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.stats_now, self.stats_prev),
            constants.CampaignDeliveryStatus.MISSING_POSTCLICK_SETUP,
        )

        self.campaign.settings.enable_ga_tracking = False
        self.campaign.settings.enable_adobe_tracking = True
        self.campaign.settings.update(None)
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.stats_now, self.stats_prev),
            constants.CampaignDeliveryStatus.OK,
        )

    def test_active_ad_groups(self):

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.stats_now, self.stats_prev),
            constants.CampaignDeliveryStatus.OK,
        )
        self.campaign.ad_groups_active = []

        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.stats_now, self.stats_prev),
            constants.CampaignDeliveryStatus.NO_ACTIVE_AD_GROUPS,
        )

    def test_campaign_with_ending_budget(self):
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.stats_now, self.stats_prev),
            constants.CampaignDeliveryStatus.OK,
        )
        self.campaign.ending_budgets.append(self.budget)
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, self.stats_now, self.stats_prev),
            constants.CampaignDeliveryStatus.CAMPAIGN_WITH_ENDING_BUDGET,
        )

    def test_campaign_goal_cpa_no_conversions(self):
        goal = core.features.goals.campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=self.campaign, type=dash.constants.CampaignGoalKPI.CPA, primary=True
        )
        self.campaign.campaign_goals = []
        self.campaign.campaign_goals = [goal]
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, {"conversions": 10}, {}),
            constants.CampaignDeliveryStatus.OK,
        )
        self.assertEqual(
            delivery.check_campaign_delivery(self.campaign, {"conversions": 0}, {}),
            constants.CampaignDeliveryStatus.CPA_NO_CONVERSIONS,
        )


class AdGroupDeliveryTestCase(test.TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.account.Account, name="Account")

        self.campaign = magic_mixer.blend(core.models.campaign.Campaign, name="Campaign 1", account=self.account)

        self.ad_group = magic_mixer.blend(core.models.ad_group.AdGroup, name="Ad Group 1", campaign=self.campaign)
        self.ad_group.settings.update_unsafe(
            None, b1_sources_group_enabled=True, b1_sources_group_state=dash.constants.AdGroupSourceSettingsState.ACTIVE
        )

        self.ad = magic_mixer.blend(
            core.models.content_ad.ContentAd,
            title="Zemanta",
            url="http://www.zemanta.com",
            ad_group=self.ad_group,
            batch__account=self.account,
        )
        self.source_type = magic_mixer.blend(core.models.SourceType, type="b1")
        self.source = magic_mixer.blend(core.models.Source, name="Test Source", source_type=self.source_type)
        self.source.save()
        self.ad_group_source = magic_mixer.blend(
            core.models.ad_group_source.AdGroupSource, ad_group=self.ad_group, source=self.source
        )
        self.ad_source = core.models.content_ad_source.ContentAdSource.objects.create(
            source=self.source, content_ad=self.ad
        )

        self.ad_group.sources_b1_active = []
        self.ad_group.sources_api_active = []
        self.ad_group.content_ads = []
        self.ad_group.content_ads_inactive = []

        self.ad_group.save(None)

    def test_missing_ads(self):
        self.ad_group.content_ads = []
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.MISSING_ADS
        )
        self.ad_group.content_ads = [self.ad]
        self.ad_group.sources_b1_active = [self.ad_group_source]

        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)

    def test_approved_ads(self):
        self.ad_group.content_ads = [self.ad]

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 0), constants.AdGroupDeliveryStatus.NO_ADS_APPROVED
        )
        self.ad_group.sources_b1_active = [self.ad_group_source]
        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)

    def test_active_sources(self):
        self.ad_group.content_ads = [self.ad]
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.NO_ACTIVE_SOURCES
        )
        self.ad_group.sources_b1_active = [self.ad_group_source]
        self.ad_group.sources_api_active = [self.ad_group_source]
        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)

    def test_active_b1_sources(self):
        self.ad_group.content_ads = [self.ad]
        self.ad_group.sources_api_active = [self.ad_group_source]
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.RTB_AS_1_NO_SOURCES
        )
        self.ad_group.sources_api_active = []
        self.ad_group.sources_b1_active = [self.ad_group_source]

        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)

    def test_interest_b1_sources(self):
        self.ad_group.content_ads = [self.ad]
        self.ad_group.sources_b1_active = [self.ad_group_source]
        self.ad_group.settings.interest_targeting = ["finance"]

        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10),
            constants.AdGroupDeliveryStatus.TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING,
        )

        for i in range(6):
            source = magic_mixer.blend(
                core.models.Source, name="Test B1 Source {}".format(i), source_type=self.source_type
            )
            ad_group_source = magic_mixer.blend(
                core.models.ad_group_source.AdGroupSource, ad_group=self.ad_group, source=source
            )
            self.ad_group.sources_b1_active.append(ad_group_source)
        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)

    def test_interest_targeting_and_data(self):
        self.ad_group.content_ads = [self.ad]
        self.ad_group.sources_api_active = [self.ad_group_source]
        for i in range(6):
            source = magic_mixer.blend(
                core.models.Source, name="Test B1 Source {}".format(i), source_type=self.source_type
            )
            ad_group_source = magic_mixer.blend(
                core.models.ad_group_source.AdGroupSource, ad_group=self.ad_group, source=source
            )
            self.ad_group.sources_b1_active.append(ad_group_source)
        self.ad_group.settings.interest_targeting = ["finance"]
        self.ad_group.settings.bluekai_targeting = ["cars"]
        self.ad_group.settings.update(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10),
            constants.AdGroupDeliveryStatus.INTEREST_TARGETING_AND_BLUEKAI,
        )
        self.ad_group.settings.interest_targeting = []
        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)

    def test_whitelist_publisher_groups(self):
        self.ad_group.content_ads = [self.ad]
        self.ad_group.sources_b1_active = [self.ad_group_source]
        self.ad_group.settings.whitelist_publisher_groups = [1]
        self.ad_group.settings.interest_targeting = []
        self.ad_group.settings.update(None)
        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)

        self.ad_group.settings.interest_targeting = ["finance"]
        self.ad_group.settings.bluekai_targeting = []
        self.ad_group.settings.update(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.WHITELIST_AND_INTERESTS
        )

        self.ad_group.settings.interest_targeting = []
        self.ad_group.settings.bluekai_targeting = ["OR", "bluekai:123"]
        self.ad_group.settings.update(None)
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.WHITELIST_AND_DATA
        )

    def test_no_active_ads(self):
        self.ad_group.content_ads = [self.ad]
        self.ad_group.sources_b1_active = [self.ad_group_source]

        self.assertEqual(delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.OK)
        self.ad.state = dash.constants.ContentAdSourceState.INACTIVE

        self.ad_group.content_ads_inactive.append(self.ad)
        self.assertEqual(len(self.ad_group.content_ads), len(self.ad_group.content_ads_inactive))
        self.assertEqual(
            delivery.check_ad_group_delivery(self.ad_group, 10), constants.AdGroupDeliveryStatus.NO_ACTIVE_ADS
        )
