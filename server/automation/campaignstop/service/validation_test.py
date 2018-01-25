import decimal

from django.test import TestCase

import core.entity
import core.bcm
import dash.constants

from . import validation
from .. import RealTimeCampaignDataHistory

from utils.magic_mixer import magic_mixer
from utils import dates_helper


class ValidateMinimumBudgetAmountTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

        today = dates_helper.local_today()
        self.credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(today, 7),
            end_date=today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=10000,
            license_fee=decimal.Decimal('0.1'),
        )
        self.budget = magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.days_before(today, 7),
            end_date=today,
            credit=self.credit,
            amount=500,
        )

        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=today,
            etfm_spend=decimal.Decimal('100.0'),
        )

        magic_mixer.blend(
            core.bcm.BudgetDailyStatement,
            budget=self.budget,
            date=dates_helper.local_yesterday(),
            media_spend_nano=200 * (10**9),
            data_spend_nano=0,
            license_fee_nano=20 * (10**9),
            margin_nano=0,
        )

    def test_validate_minimum_budget_amount(self):
        validation.validate_minimum_budget_amount(self.budget, 400)
        with self.assertRaises(validation.CampaignStopValidationError):
            validation.validate_minimum_budget_amount(self.budget, 399)

    def test_validate_without_real_time_campaign_stop(self):
        self.campaign.set_real_time_campaign_stop(is_enabled=False)
        validation.validate_minimum_budget_amount(self.budget, 0)
