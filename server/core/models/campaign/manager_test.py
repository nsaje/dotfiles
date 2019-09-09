import datetime
import decimal

from django.test import TestCase
from mock import patch

import core.models
import dash.constants
from utils import exc
from utils.magic_mixer import magic_mixer

from . import exceptions
from .model import Campaign


class TestCampaignManager(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.account = magic_mixer.blend(core.models.Account, users=[self.request.user])

    @patch("automation.autopilot.recalculate_budgets_campaign")
    def test_create(self, mock_autopilot):
        campaign = Campaign.objects.create(self.request, self.account, "xyz")
        campaign_settings = campaign.get_current_settings()
        self.assertEqual(campaign.account, self.account)
        self.assertEqual(campaign.name, "xyz")
        self.assertEqual(campaign_settings.campaign_manager, self.request.user)
        self.assertEqual(campaign_settings.name, "xyz")

    def test_create_no_currency(self):
        self.account.currency = None
        self.account.save(None)
        with self.assertRaises(exc.ValidationError):
            Campaign.objects.create(self.request, self.account, "xyz")

    def test_create_account_archived(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, archived=True)
        with self.assertRaises(exceptions.AccountIsArchived):
            core.models.Campaign.objects.create(request, account, "test")

    @patch("automation.autopilot.recalculate_budgets_campaign")
    def test_clone(self, mock_autopilot):
        campaign = magic_mixer.blend(
            core.models.Campaign, account=self.account, name="campaign", custom_flags={"flag": True}
        )
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=1000000,
            license_fee=decimal.Decimal("0.10"),
        )
        magic_mixer.cycle(5).blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            amount=1000,
            margin=decimal.Decimal("0.10"),
        )
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=self.account)
        conversion_goal = magic_mixer.blend(
            core.features.goals.ConversionGoal, campaign=campaign, pixel=pixel, goal_id=pixel.id, conversion_window=7
        )
        campaign_goal = magic_mixer.blend(
            core.features.goals.CampaignGoal, campaign=campaign, conversion_goal=conversion_goal
        )
        magic_mixer.blend(
            core.features.goals.CampaignGoalValue, campaign_goal=campaign_goal, value="0.30", local_value="0.30"
        )

        cloned_campaign = Campaign.objects.clone(self.request, campaign, "Cloned Campaign")

        self.assertNotEqual(campaign.id, cloned_campaign.id)
        self.assertEqual("Cloned Campaign", cloned_campaign.name)
        self.assertEqual(campaign.type, cloned_campaign.type)
        self.assertFalse(cloned_campaign.archived)
        self.assertEqual(campaign.default_whitelist, cloned_campaign.default_whitelist)
        self.assertEqual(campaign.default_blacklist, cloned_campaign.default_blacklist)
        self.assertEqual(campaign.custom_flags, cloned_campaign.custom_flags)

        cloned_settings = cloned_campaign.get_current_settings()
        self.assertEqual(cloned_settings.name, "Cloned Campaign")
        self.assertFalse(cloned_settings.archived)

        for field in set(core.models.settings.CampaignSettings._clone_fields) - {"name"}:
            self.assertEqual(getattr(campaign.settings, field), getattr(cloned_settings, field))

        self.assertEqual(5, cloned_campaign.budgets.count())
        self.assertFalse(cloned_campaign.budgets.all().intersection(campaign.budgets.all()))
        self.assertEqual(1, cloned_campaign.campaigngoal_set.count())
        self.assertFalse(cloned_campaign.campaigngoal_set.all().intersection(campaign.campaigngoal_set.all()))
        self.assertEqual(1, cloned_campaign.conversiongoal_set.count())
        self.assertFalse(cloned_campaign.conversiongoal_set.all().intersection(campaign.conversiongoal_set.all()))
