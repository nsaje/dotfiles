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
    @mock.patch.object(core.features.bcm.BudgetLineItem, "get_available_etfm_amount")
    def test_prepare_budgets(self, mock_get_available_amount):
        def _mocked_get_available_amount(budget):
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

        local_today = dates_helper.local_today()
        account = magic_mixer.blend(core.models.Account)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            start_date=local_today - datetime.timedelta(days=30),
            end_date=local_today + datetime.timedelta(days=30),
            amount=100000,
        )
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        past_non_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(  # noqa
            campaign=campaign,
            credit=credit,
            amount=500,
            start_date=local_today - datetime.timedelta(days=30),
            end_date=local_today - datetime.timedelta(days=20),
        )
        past_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=500,
            start_date=local_today - datetime.timedelta(days=10),
            end_date=local_today - datetime.timedelta(days=1),
        )
        current_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=500,
            margin=decimal.Decimal("0.05"),
            start_date=local_today - datetime.timedelta(days=5),
            end_date=local_today + datetime.timedelta(days=5),
        )
        current_budget_2 = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=500,
            margin=decimal.Decimal("0.05"),
            start_date=local_today,
            end_date=local_today + datetime.timedelta(days=10),
        )
        future_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=500,
            start_date=local_today + datetime.timedelta(days=8),
            end_date=local_today + datetime.timedelta(days=15),
        )
        future_non_overlapping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(  # noqa
            campaign=campaign,
            credit=credit,
            amount=500,
            start_date=local_today + datetime.timedelta(days=20),
            end_date=local_today + datetime.timedelta(days=30),
        )
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        self.assertEqual(
            budgets.prepare_budgets([ad_group]),
            {
                campaign: {
                    "campaign_budget_start_date": past_overlapping_budget.start_date,
                    "days_since_campaign_budget_start": 10,
                    "campaign_budget_end_date": future_overlapping_budget.end_date,
                    "days_since_campaign_budget_end_date": 15,
                    "campaign_remaining_budget": decimal.Decimal("50"),
                    "campaign_budget_margin": decimal.Decimal("0.05"),
                }
            },
        )
