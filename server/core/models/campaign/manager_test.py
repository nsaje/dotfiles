import datetime
import decimal

from mock import patch

import core.models
import dash.constants
from utils import exc
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import exceptions
from .model import Campaign


class CampaignManagerTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(user=self.user)
        self.account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])

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
    @patch("utils.dates_helper.local_today", return_value=datetime.date(2017, 1, 1))
    def test_clone(self, mock_today, mock_autopilot):
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
        direct_deal = magic_mixer.blend(core.features.deals.DirectDeal, id=1, account=self.account)
        magic_mixer.cycle(5).blend(core.features.deals.DirectDealConnection, deal=direct_deal, campaign=campaign)

        cloned_campaign = Campaign.objects.clone(self.request, campaign, "Cloned Campaign", clone_budget=True)

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

        self.assertEqual(5, cloned_campaign.directdealconnection_set.filter(deal=direct_deal).count())
        self.assertEqual(5, cloned_campaign.directdealconnection_set.count())

    @patch("automation.autopilot.recalculate_budgets_campaign")
    @patch("utils.dates_helper.local_today", return_value=datetime.date(2017, 1, 1))
    def test_clone_without_budget(self, mock_today, mock_autopilot):
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

        self.assertEqual(0, cloned_campaign.budgets.count())
        self.assertEqual(1, cloned_campaign.campaigngoal_set.count())
        self.assertFalse(cloned_campaign.campaigngoal_set.all().intersection(campaign.campaigngoal_set.all()))
        self.assertEqual(1, cloned_campaign.conversiongoal_set.count())
        self.assertFalse(cloned_campaign.conversiongoal_set.all().intersection(campaign.conversiongoal_set.all()))
