import datetime
import decimal

import mock
from django.core.exceptions import ValidationError
from mock import patch

import core.features.bcm
import core.features.goals
import core.models
import dash.constants
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import exceptions
from . import service


@patch("automation.autopilot_legacy.recalculate_budgets_ad_group", autospec=True)
@patch("utils.dates_helper.local_today", return_value=datetime.date(2017, 1, 1))
class CloneServiceTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)

        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.campaign = magic_mixer.blend(core.models.Campaign, account=account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        icon = magic_mixer.blend(core.models.ImageAsset, width=200, height=200)
        self.content_ads = magic_mixer.cycle(2).blend(
            core.models.ContentAd, ad_group=self.ad_group, archived=False, icon=icon
        )

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

    def test_clone(self, mock_today, mock_autopilot):
        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=True
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertNotEqual(self.ad_group, cloned_campaign.adgroup_set.get())

        self.assertEqual(2, core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).count())
        cloned_ads = core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign)
        self.assertNotEqual(self.content_ads, cloned_ads)
        self.assertEqual(self.content_ads[0].icon, cloned_ads[0].icon)

        self.assertEqual(0, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

        self.assertEqual(
            self.campaign.adgroup_set.get().settings.state, cloned_campaign.adgroup_set.get().settings.state
        )
        self.assertEqual(
            [content_ad.state for content_ad in self.campaign.adgroup_set.get().contentad_set.all()],
            [cloned_content_ad.state for cloned_content_ad in cloned_campaign.adgroup_set.get().contentad_set.all()],
        )

    def test_clone_no_ad_group(self, mock_today, mock_autopilot):
        self.ad_group.archive(None)

        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=True
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertFalse(cloned_campaign.adgroup_set.exists())
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).exists())

        self.assertEqual(0, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

    def test_clone_no_content(self, mock_today, mock_autopilot):
        self.ad_group.contentad_set.update(archived=True)

        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=True
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertNotEqual(self.ad_group, cloned_campaign.adgroup_set.get())
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).exists())

        self.assertEqual(0, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

    def test_clone_skip_ad_group(self, mock_today, mock_autopilot):
        self.assertRaises(
            exceptions.CanNotCloneAds,
            service.clone,
            self.request,
            self.campaign.id,
            "Cloned Campaign",
            clone_ad_groups=False,
            clone_ads=True,
        )

    def test_clone_skip_content(self, mock_today, mock_autopilot):
        cloned_campaign = service.clone(
            self.request, self.campaign, "Cloned Campaign", clone_ad_groups=True, clone_ads=False
        )

        self.assertNotEqual(self.campaign, cloned_campaign)
        self.assertNotEqual(self.ad_group, cloned_campaign.adgroup_set.get())
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group__campaign=cloned_campaign).exists())

        self.assertEqual(0, cloned_campaign.budgets.count())
        self.assertNotEqual(self.budgets, cloned_campaign.budgets.all())

        self.assertTrue(cloned_campaign.campaigngoal_set.exists())
        self.assertNotEqual(self.campaign_goal, cloned_campaign.campaigngoal_set.get())

        self.assertTrue(cloned_campaign.conversiongoal_set.exists())
        self.assertNotEqual(self.conversion_goal, cloned_campaign.conversiongoal_set.get())

    def test_clone_set_adgroup_state_override(self, mock_today, mock_autopilot):
        self.assertEqual(self.campaign.adgroup_set.get().settings.state, dash.constants.AdGroupSettingsState.INACTIVE)

        cloned_campaign = service.clone(
            self.request,
            self.campaign,
            "Cloned Campaign",
            clone_ad_groups=True,
            clone_ads=False,
            ad_group_state_override=dash.constants.AdGroupSettingsState.ACTIVE,
        )

        self.assertEqual(cloned_campaign.adgroup_set.get().settings.state, dash.constants.AdGroupSettingsState.ACTIVE)

    def test_clone_set_ads_state_override(self, mock_today, mock_autopilot):
        for contend_ad in self.campaign.adgroup_set.get().contentad_set.all():
            self.assertEqual(contend_ad.state, dash.constants.AdGroupSettingsState.ACTIVE)

        cloned_campaign = service.clone(
            self.request,
            self.campaign,
            "Cloned Campaign",
            clone_ad_groups=True,
            clone_ads=True,
            ad_group_state_override=None,
            ad_state_override=dash.constants.AdGroupSettingsState.INACTIVE,
        )

        for contend_ad in cloned_campaign.adgroup_set.get().contentad_set.all():
            self.assertEqual(contend_ad.state, dash.constants.AdGroupSettingsState.INACTIVE)


@patch.object(dash.features.clonecampaign.service, "clone", autospec=True)
class CloneAsyncServiceTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.campaign = magic_mixer.blend(core.models.Campaign, account=account, name="Test campaign")
        self.mocked_cloned_campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign (copy)"
        )

    @patch("utils.email_helper.send_campaign_cloned_success_email")
    def test_clone_async_success(self, mock_success_email, mock_clone):
        mock_clone.return_value = self.mocked_cloned_campaign
        cloned_campaign_id = service.clone_async(
            self.request.user,
            self.campaign.id,
            self.campaign.name,
            "Test campaign (copy)",
            clone_ad_groups=True,
            clone_ads=True,
            send_email=True,
        )

        mock_clone.assert_called_with(mock.ANY, self.campaign, "Test campaign (copy)", True, True, None, None)
        self.assertEqual(self.mocked_cloned_campaign.id, cloned_campaign_id)
        mock_success_email.assert_called_with(mock.ANY, self.campaign.name, self.mocked_cloned_campaign.name)

    @patch("utils.email_helper.send_campaign_cloned_error_email")
    def test_clone_async_validation_error(self, mock_error_email, mock_clone):
        mock_clone.side_effect = ValidationError("Validation error")
        service.clone_async(
            self.request.user,
            self.campaign.id,
            self.campaign.name,
            "Test campaign (copy)",
            clone_ad_groups=True,
            clone_ads=True,
            send_email=True,
        )

        mock_clone.assert_called_with(mock.ANY, self.campaign, "Test campaign (copy)", True, True, None, None)
        mock_error_email.assert_called_with(
            mock.ANY, self.campaign.name, self.mocked_cloned_campaign.name, "Validation error"
        )

    @patch("utils.email_helper.send_campaign_cloned_error_email")
    def test_clone_async_exception(self, mock_error_email, mock_clone):
        mock_clone.side_effect = Exception("test-error")
        with self.assertRaises(Exception):
            service.clone_async(
                self.request.user,
                self.campaign.id,
                self.campaign.name,
                "Test campaign (copy)",
                clone_ad_groups=True,
                clone_ads=True,
                send_email=True,
            )

            mock_clone.assert_called_with(mock.ANY, self.campaign, "Test campaign (copy)", True, True, None, None)
            mock_error_email.assert_called_with(mock.ANY, self.campaign.name, self.mocked_cloned_campaign.name)
