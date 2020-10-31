import decimal

from django.test import TestCase
from mock import patch

import core.features.bcm
import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import signals


class NotifyBudgetsTest(TestCase):
    def setUp(self):
        account = magic_mixer.blend(core.models.Account, agency__uses_realtime_autopilot=True)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=account)
        self.campaign.settings.update_unsafe(None, autopilot=True)
        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=1000,
            license_fee=decimal.Decimal("0.3333"),
        )
        self.budget = magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            credit=self.credit,
            amount=decimal.Decimal("200"),
            margin=0,
        )

        signals.connect_notify_budgets()
        self.addCleanup(signals.disconnect_notify_budgets)

    @patch("automation.autopilot.service.service.recalculate_ad_group_budgets")
    def test_recalculate_budget_change(self, mock_recalculate):
        self.budget.amount = self.budget.amount + 1
        self.budget.save()
        mock_recalculate.assert_called_with(self.budget.campaign)

    @patch("automation.autopilot.service.service.recalculate_ad_group_budgets")
    def test_recalculate_budget_create(self, mock_recalculate):
        budget = core.features.bcm.BudgetLineItem(
            campaign=self.campaign,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            credit=self.credit,
            amount=decimal.Decimal("200"),
            margin=0,
        )
        budget.save()
        mock_recalculate.assert_called_with(self.budget.campaign)

    @patch("automation.autopilot.service.service.recalculate_ad_group_budgets")
    def test_recalculate_budget_change_no_autopilot(self, mock_recalculate):
        self.campaign.settings.update_unsafe(None, autopilot=False)
        self.budget.amount = self.budget.amount + 1
        self.budget.save()
        mock_recalculate.assert_not_called()
