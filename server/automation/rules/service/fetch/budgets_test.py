import datetime
import decimal

import mock
from django.test import TestCase

import core.features.goals
import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import budgets


class PrepareBudgetsTestCase(TestCase):
    def setUp(self):
        self.local_today = dates_helper.local_today()
        self.account = magic_mixer.blend(core.models.Account)
        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            start_date=self.local_today - datetime.timedelta(days=30),
            end_date=self.local_today + datetime.timedelta(days=30),
            amount=100000,
        )
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)

    def test_prepare_budgets(self):
        def _mocked_get_available_amount(budget, date):
            if budget == current_budget:
                return decimal.Decimal(0)
            elif budget == current_budget_2:
                return decimal.Decimal(50)
            return None

        patcher = mock.patch.object(
            core.features.bcm.BudgetLineItem, "get_available_etfm_amount", new=_mocked_get_available_amount
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        past_non_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(  # noqa
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.0"),
            start_date=self.local_today - datetime.timedelta(days=30),
            end_date=self.local_today - datetime.timedelta(days=20),
        )
        past_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.05"),
            start_date=self.local_today - datetime.timedelta(days=10),
            end_date=self.local_today - datetime.timedelta(days=1),
        )
        current_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.05"),
            start_date=self.local_today - datetime.timedelta(days=5),
            end_date=self.local_today + datetime.timedelta(days=5),
        )
        current_budget_2 = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.05"),
            start_date=self.local_today - datetime.timedelta(days=1),
            end_date=self.local_today + datetime.timedelta(days=10),
        )
        future_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.05"),
            start_date=self.local_today + datetime.timedelta(days=8),
            end_date=self.local_today + datetime.timedelta(days=15),
        )
        future_non_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(  # noqa
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.0"),
            start_date=self.local_today + datetime.timedelta(days=20),
            end_date=self.local_today + datetime.timedelta(days=30),
        )
        self.assertEqual(
            budgets.prepare_budgets([self.ad_group]),
            {
                self.campaign.id: {
                    "campaign_budget_start_date": past_overlapping_budget.start_date,
                    "days_since_campaign_budget_start": 10,
                    "campaign_budget_end_date": future_overlapping_budget.end_date,
                    "days_until_campaign_budget_end_date": 15,
                    "campaign_remaining_budget": decimal.Decimal("50"),
                    "campaign_budget_margin": decimal.Decimal("0.05"),
                }
            },
        )

    def test_only_past_budgets(self):
        past_non_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.0"),
            start_date=self.local_today - datetime.timedelta(days=30),
            end_date=self.local_today - datetime.timedelta(days=20),
        )
        self.assertEqual(
            budgets.prepare_budgets([self.ad_group]),
            {
                self.campaign.id: {
                    "campaign_budget_start_date": None,
                    "days_since_campaign_budget_start": None,
                    "campaign_budget_end_date": past_non_overlapping_budget.end_date,
                    "days_until_campaign_budget_end_date": -20,
                    "campaign_remaining_budget": 0,
                    "campaign_budget_margin": 0,
                }
            },
        )

    def test_only_future_budgets(self):
        future_non_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=500,
            margin=decimal.Decimal("0.0"),
            start_date=self.local_today + datetime.timedelta(days=20),
            end_date=self.local_today + datetime.timedelta(days=30),
        )
        self.assertEqual(
            budgets.prepare_budgets([self.ad_group]),
            {
                self.campaign.id: {
                    "campaign_budget_start_date": future_non_overlapping_budget.start_date,
                    "days_since_campaign_budget_start": -20,
                    "campaign_budget_end_date": None,
                    "days_until_campaign_budget_end_date": None,
                    "campaign_remaining_budget": 0,
                    "campaign_budget_margin": 0,
                }
            },
        )
