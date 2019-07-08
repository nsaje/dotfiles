import decimal

from django.test import TestCase
from mock import patch

import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import CampaignStopState
from . import config
from . import start_date_check


class UpdateCampaignsStartDateTestCase(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)
        self.today = dates_helper.local_today()
        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(self.today, 30),
            end_date=dates_helper.days_after(self.today, 30),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=10000,
            license_fee=decimal.Decimal("0.1"),
        )

    def test_active_budget(self):
        budget = self._set_up_current_budget()
        start_date_check.update_campaigns_start_date([self.campaign])
        state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(budget.start_date, state.min_allowed_start_date)

    @patch("automation.campaignstop.service.spends_helper.get_budget_spend_estimates")
    def test_depleted_budget(self, mock_spend_estimates):
        budget = self._set_up_current_budget()
        mock_spend_estimates.return_value = {budget: budget.amount - (config.THRESHOLD - 1)}
        start_date_check.update_campaigns_start_date([self.campaign])
        state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(None, state.min_allowed_start_date)

    def test_future_budget(self):
        budget = self._set_up_future_budget()
        start_date_check.update_campaigns_start_date([self.campaign])
        state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(budget.start_date, state.min_allowed_start_date)

    @patch("automation.campaignstop.service.spends_helper.get_budget_spend_estimates")
    def test_depleted_current_and_future_budget(self, mock_spend_estimates):
        current_budget = self._set_up_current_budget()
        future_budget = self._set_up_future_budget()
        mock_spend_estimates.return_value = {current_budget: current_budget.amount - (config.THRESHOLD - 1)}
        start_date_check.update_campaigns_start_date([self.campaign])
        state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(future_budget.start_date, state.min_allowed_start_date)

    def test_past_budget(self):
        self._set_up_past_budget()
        start_date_check.update_campaigns_start_date([self.campaign])
        state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(None, state.min_allowed_start_date)

    def _set_up_current_budget(self):
        return self._set_up_budget(dates_helper.days_before(self.today, 7), self.today)

    def _set_up_future_budget(self):
        return self._set_up_budget(dates_helper.days_after(self.today, 7), dates_helper.days_after(self.today, 14))

    def _set_up_past_budget(self):
        return self._set_up_budget(dates_helper.days_before(self.today, 14), dates_helper.days_before(self.today, 7))

    def _set_up_budget(self, start_date, end_date):
        return magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=start_date,
            end_date=end_date,
            credit=self.credit,
            amount=500,
        )
