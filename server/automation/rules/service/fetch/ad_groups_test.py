import datetime
import decimal

import mock
from django.test import TestCase

import core.features.goals
import core.models
import dash.constants
from utils import dates_helper
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import ad_groups


class PrepareAdGroupSettingsTestCase(TestCase):
    def setUp(self):
        # NOTE: patching the class with a decorator doesn't work because of import timing
        patcher = mock.patch("automation.autopilot.recalculate_budgets_ad_group")
        patcher.start()
        self.addCleanup(patcher.stop)

        now = dates_helper.utc_now()
        self.utc_today = dates_helper.utc_today()
        self.request = magic_mixer.blend_request_user()
        self.user = self.request.user
        with test_helper.disable_auto_now_add(core.models.Account, field_name="created_dt"):
            self.account = magic_mixer.blend(core.models.Account, created_dt=now - datetime.timedelta(days=3))
        with test_helper.disable_auto_now_add(core.models.Campaign, field_name="created_dt"):
            self.campaign = magic_mixer.blend(
                core.models.Campaign, account=self.account, created_dt=now - datetime.timedelta(days=2)
            )
        with test_helper.disable_auto_now_add(core.models.AdGroup, field_name="created_dt"):
            self.ad_group = magic_mixer.blend(
                core.models.AdGroup, campaign=self.campaign, created_dt=now - datetime.timedelta(days=1)
            )
        b1_source_type = magic_mixer.blend(core.models.SourceType, type="b1")
        self.ad_group_sources = magic_mixer.cycle(3).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source__source_type=b1_source_type
        )
        for ad_group_source in self.ad_group_sources:
            ad_group_source.settings.update(
                None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE, daily_budget_cc=decimal.Decimal("10")
            )
        self.campaign.settings.update(None, campaign_manager=self.user)
        self.ad_group.settings.update(None, end_date=self.utc_today + datetime.timedelta(days=7))

    def test_prepare_ad_group_settings(self):
        self.assertEqual(
            ad_groups.prepare_ad_group_settings([self.ad_group]),
            {
                self.ad_group.id: {
                    "account_created_date": self.utc_today - datetime.timedelta(days=3),
                    "account_name": self.account.name,
                    "ad_group_bid": decimal.Decimal("0.4500"),
                    "ad_group_bidding_type": dash.constants.BiddingType.CPC,
                    "ad_group_created_date": self.utc_today - datetime.timedelta(days=1),
                    "ad_group_delivery_type": dash.constants.AdGroupDeliveryType.STANDARD,
                    "ad_group_end_date": self.utc_today + datetime.timedelta(days=7),
                    "ad_group_id": self.ad_group.id,
                    "ad_group_name": self.ad_group.name,
                    "ad_group_start_date": self.utc_today,
                    "campaign_category": dash.constants.IABCategory.IAB24,
                    "campaign_created_date": self.utc_today - datetime.timedelta(days=2),
                    "campaign_language": dash.constants.Language.ENGLISH,
                    "campaign_manager": self.user.email,
                    "campaign_name": self.campaign.name,
                    "campaign_type": dash.constants.CampaignType.CONTENT,
                    "days_since_account_created": 3,
                    "days_since_ad_group_created": 1,
                    "days_since_campaign_created": 2,
                }
            },
        )

    def test_primary_campaign_goal(self):
        core.features.goals.CampaignGoal.objects.create(
            self.request, self.campaign, dash.constants.CampaignGoalKPI.TIME_ON_SITE, 30, primary=False
        )
        primary_goal = core.features.goals.CampaignGoal.objects.create(
            self.request, self.campaign, dash.constants.CampaignGoalKPI.CPC, decimal.Decimal("0.5"), primary=True
        )
        primary_goal.update(self.request, value=decimal.Decimal("0.7"))

        ad_group_settings = ad_groups.prepare_ad_group_settings([self.ad_group], include_campaign_goals=True)[
            self.ad_group.id
        ]
        self.assertEqual(dash.constants.CampaignGoalKPI.CPC, ad_group_settings["campaign_primary_goal"])
        self.assertEqual(decimal.Decimal("0.7"), ad_group_settings["campaign_primary_goal_value"])

    def test_non_primary_campaign_goal(self):
        non_primary_goal = core.features.goals.CampaignGoal.objects.create(
            self.request, self.campaign, dash.constants.CampaignGoalKPI.TIME_ON_SITE, 30, primary=False
        )
        core.features.goals.CampaignGoal.objects.create(
            self.request, self.campaign, dash.constants.CampaignGoalKPI.CPC, decimal.Decimal("0.5"), primary=True
        )
        non_primary_goal.update(self.request, primary=True)

        ad_group_settings = ad_groups.prepare_ad_group_settings([self.ad_group], include_campaign_goals=True)[
            self.ad_group.id
        ]
        self.assertEqual(dash.constants.CampaignGoalKPI.TIME_ON_SITE, ad_group_settings["campaign_primary_goal"])
        self.assertEqual(30, ad_group_settings["campaign_primary_goal_value"])

    def test_ad_group_bid_cpc(self):
        self.ad_group.update(None, bidding_type=dash.constants.BiddingType.CPC)
        self.ad_group.settings.update(None, cpc=decimal.Decimal("0.7"))

        ad_group_settings = ad_groups.prepare_ad_group_settings([self.ad_group])[self.ad_group.id]
        self.assertEqual(decimal.Decimal("0.7"), ad_group_settings["ad_group_bid"])

    def test_ad_group_bid_cpm(self):
        self.ad_group.update(None, bidding_type=dash.constants.BiddingType.CPM)
        self.ad_group.settings.update(None, cpm=decimal.Decimal("1.2"))

        ad_group_settings = ad_groups.prepare_ad_group_settings([self.ad_group])[self.ad_group.id]
        self.assertEqual(decimal.Decimal("1.2"), ad_group_settings["ad_group_bid"])

    def test_ad_group_daily_caps_manual_rtb(self):
        self.ad_group.settings.update(
            None, b1_sources_group_enabled=False, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        ad_group_settings = ad_groups.prepare_ad_group_settings([self.ad_group], include_ad_group_daily_cap=True)[
            self.ad_group.id
        ]
        self.assertEqual(decimal.Decimal("30"), ad_group_settings["ad_group_daily_cap"])

    def test_ad_group_daily_caps_all_rtb(self):
        ad_group_settings = ad_groups.prepare_ad_group_settings([self.ad_group], include_ad_group_daily_cap=True)[
            self.ad_group.id
        ]
        self.assertEqual(decimal.Decimal("50"), ad_group_settings["ad_group_daily_cap"])

    def test_ad_group_daily_caps_all_rtb_api_soures(self):
        non_b1_source_type = magic_mixer.blend(core.models.SourceType, type="notb1")
        non_b1_ad_group_sources = magic_mixer.cycle(2).blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source__source_type=non_b1_source_type
        )
        for ad_group_source in non_b1_ad_group_sources:
            ad_group_source.settings.update(
                None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE, daily_budget_cc=decimal.Decimal("10")
            )

        ad_group_settings = ad_groups.prepare_ad_group_settings([self.ad_group], include_ad_group_daily_cap=True)[
            self.ad_group.id
        ]
        self.assertEqual(decimal.Decimal("70"), ad_group_settings["ad_group_daily_cap"])
