import datetime
import decimal
import mock

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

        self.today = dates_helper.local_today()
        self.credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(self.today, 7),
            end_date=self.today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=10000,
            license_fee=decimal.Decimal('0.1'),
        )
        self.budget = magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.days_before(self.today, 7),
            end_date=self.today,
            credit=self.credit,
            amount=500,
        )

        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=self.today,
            etfm_spend=decimal.Decimal('100.0'),
        )

        yesterday = dates_helper.local_yesterday()
        magic_mixer.blend(
            core.bcm.BudgetDailyStatement,
            budget=self.budget,
            date=yesterday,
            media_spend_nano=200 * (10**9),
            data_spend_nano=0,
            license_fee_nano=20 * (10**9),
            margin_nano=0,
        )

        magic_mixer.blend(
            RealTimeCampaignDataHistory,
            campaign=self.campaign,
            date=yesterday,
            etfm_spend=decimal.Decimal('220.0'),
        )

    def test_validate_minimum_budget_amount(self):
        validation.validate_minimum_budget_amount(self.budget, 400)

    @mock.patch('utils.dates_helper.utc_now')
    def test_validate_minimum_budget_amount_invalid_daily_statements(self, mock_utc_now):
        pm = datetime.datetime(self.today.year, self.today.month, self.today.day, 16)
        mock_utc_now.return_value = pm

        with self.assertRaises(validation.CampaignStopValidationException):
            validation.validate_minimum_budget_amount(self.budget, 399)

    @mock.patch('utils.dates_helper.utc_now')
    def test_validate_minimum_budget_amount_invalid_real_time_data(self, mock_utc_now):
        am = datetime.datetime(self.today.year, self.today.month, self.today.day, 6)
        mock_utc_now.return_value = am

        with self.assertRaises(validation.CampaignStopValidationException):
            validation.validate_minimum_budget_amount(self.budget, 399)

    def test_validate_without_real_time_campaign_stop(self):
        self.campaign.set_real_time_campaign_stop(is_enabled=False)
        validation.validate_minimum_budget_amount(self.budget, 0)
