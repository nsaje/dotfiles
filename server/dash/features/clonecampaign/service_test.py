import datetime
import decimal

from django.test import TestCase
from mock import patch

import core.features.bcm
import core.features.goals
import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import service


@patch.object(core.models.ContentAd.objects, "insert_redirects", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
class CloneServiceTest(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()

        account = magic_mixer.blend(core.models.Account, users=[self.request.user])
        self.campaign = magic_mixer.blend(core.models.Campaign, account=account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.content_ads = magic_mixer.cycle(2).blend(core.models.ContentAd, ad_group=self.ad_group, archived=False)

        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=1000000,
            license_fee=decimal.Decimal("0.10"),
        )
        self.budgets = magic_mixer.cycle(5).blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            credit=credit,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            amount=1000,
            margin=decimal.Decimal("0.10"),
        )

        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        self.conversion_goal = magic_mixer.blend(
            core.features.goals.ConversionGoal,
            campaign=self.campaign,
            pixel=pixel,
            goal_id=pixel.id,
            conversion_window=7,
        )
        self.campaign_goal = magic_mixer.blend(
            core.features.goals.CampaignGoal, campaign=self.campaign, conversion_goal=self.conversion_goal
        )
        magic_mixer.blend(
            core.features.goals.CampaignGoalValue, campaign_goal=self.campaign_goal, value="0.30", local_value="0.30"
        )

    def test_clone(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=True
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertNotEqual(self.ad_group, cloned_campaign.adgroup_set.get())

        self.assertEqual(2, core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).count())
        self.assertNotEqual(self.content_ads, core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign))

        self.assertEqual(5, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

    def test_clone_no_ad_group(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        self.ad_group.archive(None)

        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=True
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertFalse(cloned_campaign.adgroup_set.exists())
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).exists())

        self.assertEqual(5, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

    def test_clone_no_content(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        self.ad_group.contentad_set.update(archived=True)

        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=True
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertNotEqual(self.ad_group, cloned_campaign.adgroup_set.get())
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).exists())

        self.assertEqual(5, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

    def test_clone_skip_ad_group(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=False, clone_ads=True
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertFalse(cloned_campaign.adgroup_set.exists())
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).exists())

        self.assertEqual(5, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

    def test_clone_skip_content(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=False
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertNotEqual(self.ad_group, cloned_campaign.adgroup_set.get())
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).exists())

        self.assertEqual(5, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())
