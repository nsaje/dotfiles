import datetime
import decimal

import mock
from django.test import TestCase

import core.features.bcm
import core.features.multicurrency
import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import RealTimeCampaignDataHistory
from . import calculation


class ValidateMinimumBudgetAmountTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)

        self.today = dates_helper.local_today()
        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(self.today, 7),
            end_date=self.today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=10000,
            service_fee=decimal.Decimal("0.25"),
            license_fee=decimal.Decimal("0.1"),
        )
        self.budget = magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=dates_helper.days_before(self.today, 7),
            end_date=self.today,
            credit=self.credit,
            amount=500,
        )

        self.rt_history_today = magic_mixer.blend(
            RealTimeCampaignDataHistory, campaign=self.campaign, date=self.today, etfm_spend=decimal.Decimal("100.0")
        )

        yesterday = dates_helper.local_yesterday()
        magic_mixer.blend(
            core.features.bcm.BudgetDailyStatement,
            budget=self.budget,
            date=yesterday,
            base_media_spend_nano=200 * (10 ** 9),
            base_data_spend_nano=0,
            service_fee_nano=50 * (10 ** 9),
            license_fee_nano=20 * (10 ** 9),
            margin_nano=0,
            local_base_media_spend_nano=200 * (10 ** 9),
            local_base_data_spend_nano=0,
            local_service_fee_nano=50 * (10 ** 9),
            local_license_fee_nano=20 * (10 ** 9),
            local_margin_nano=0,
        )

        self.rt_history_yesterday = magic_mixer.blend(
            RealTimeCampaignDataHistory, campaign=self.campaign, date=yesterday, etfm_spend=decimal.Decimal("220.0")
        )

    """def test_calculate_minimum_budget_amount(self):
        self.assertEqual(500, calculation.calculate_minimum_budget_amount(self.budget))"""

    def test_calculate_minimum_budget_amount_high_rt_spend(self):
        self.rt_history_today.etfm_spend = decimal.Decimal("300.0")
        self.rt_history_today.save()

        self.assertEqual(500, calculation.calculate_minimum_budget_amount(self.budget))

    @mock.patch("utils.dates_helper.utc_now")
    @mock.patch("automation.campaignstop.service.refresh.refresh_if_stale", mock.MagicMock())
    def test_calculate_minimum_budget_amount_invalid_daily_statements(self, mock_utc_now):
        pm = datetime.datetime(self.today.year, self.today.month, self.today.day, 16)
        mock_utc_now.return_value = pm

        self.rt_history_today.created_dt = pm  # prevent refresh logic from triggering
        self.rt_history_today.save()

        self.assertEqual(500, calculation.calculate_minimum_budget_amount(self.budget))

    @mock.patch("utils.dates_helper.utc_now")
    def test_calculate_minimum_budget_amount_invalid_real_time_data(self, mock_utc_now):
        am = datetime.datetime(self.today.year, self.today.month, self.today.day, 6)
        mock_utc_now.return_value = am

        self.rt_history_today.created_dt = am  # prevent refresh logic from triggering
        self.rt_history_today.save()

        self.assertEqual(400, calculation.calculate_minimum_budget_amount(self.budget))

    def test_validate_without_real_time_campaign_stop(self):
        self.campaign.set_real_time_campaign_stop(is_enabled=False)
        self.assertIsNone(calculation.calculate_minimum_budget_amount(self.budget))

    def test_multicurrency(self):
        account = self.campaign.account
        account.currency = dash.constants.Currency.EUR
        account.save(None)

        self.credit.currency = dash.constants.Currency.EUR
        self.credit.save()

        core.features.multicurrency.CurrencyExchangeRate.objects.create(
            currency=self.credit.currency, date=dates_helper.local_today(), exchange_rate=decimal.Decimal("2")
        )
        self.assertEqual(500, calculation.calculate_minimum_budget_amount(self.budget))
