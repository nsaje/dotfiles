import datetime
from decimal import Decimal

from django.test import TestCase
from mock import patch

from dash import constants
from dash import models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .campaign import calculate_campaigns_daily_budget


class AutopilotCalculateCampaignDailyBudgetTestCase(TestCase):
    def setUp(self):
        self.today = datetime.date(2018, 2, 20)
        self.campaign = magic_mixer.blend(models.Campaign, account__agency__uses_realtime_autopilot=True)
        self.campaign.settings.update_unsafe(None, autopilot=True)
        self.credit = magic_mixer.blend(
            models.CreditLineItem,
            account=self.campaign.account,
            start_date=dates_helper.days_before(self.today, 10),
            end_date=dates_helper.days_after(self.today, 10),
            status=constants.CreditLineItemStatus.SIGNED,
            amount=1000,
            service_fee=Decimal("0.1"),
            license_fee=Decimal("0.1"),
        )

        utc_now_patcher = patch("utils.dates_helper.utc_now")
        self.mock_utc_now = utc_now_patcher.start()
        self.mock_utc_now.return_value = datetime.datetime(2018, 2, 20, 12, 5)
        self.addCleanup(utc_now_patcher.stop)

    def test_budget_with_spend(self):
        budget = magic_mixer.blend(
            models.BudgetLineItem,
            start_date=dates_helper.days_before(self.today, 5),
            end_date=dates_helper.days_after(self.today, 5),
            amount=100,
            credit=self.credit,
            campaign=self.campaign,
        )
        magic_mixer.blend(
            models.BudgetDailyStatement,
            budget=budget,
            base_media_spend_nano=1.1 * 1e9,
            base_data_spend_nano=2.2 * 1e9,
            service_fee_nano=1.65 * 1e9,
            license_fee_nano=1.65 * 1e9,
            margin_nano=4.4 * 1e9,
            local_base_media_spend_nano=1.1 * 1e9,
            local_base_data_spend_nano=2.2 * 1e9,
            local_service_fee_nano=1.65 * 1e9,
            local_license_fee_nano=1.65 * 1e9,
            local_margin_nano=4.4 * 1e9,
        )

        result = calculate_campaigns_daily_budget()
        # (100 (budget) - 11 (daily statement spend)) / 6 (remaining budget days)
        # = 14.833 (rounded to 1$)
        self.assertEqual(dict(result), {self.campaign: 15})

    def test_multiple_budgets(self):
        magic_mixer.blend(
            models.BudgetLineItem,
            start_date=dates_helper.days_before(self.today, 5),
            end_date=dates_helper.days_after(self.today, 3),
            amount=100,
            credit=self.credit,
            campaign=self.campaign,
        )
        magic_mixer.blend(
            models.BudgetLineItem,
            start_date=self.today,
            end_date=dates_helper.days_after(self.today, 4),
            amount=100,
            credit=self.credit,
            campaign=self.campaign,
        )

        result = calculate_campaigns_daily_budget()
        # 25 from 1st budget that has 4 remaining days
        # 20 from 2nd budget that has 5 remaining days
        self.assertEqual(result, {self.campaign: 45})

    def test_last_day_budget(self):
        magic_mixer.blend(
            models.BudgetLineItem,
            start_date=dates_helper.days_before(self.today, 5),
            end_date=self.today,
            amount=100,
            credit=self.credit,
            campaign=self.campaign,
        )

        result = calculate_campaigns_daily_budget()
        # all budget amount because only 1 day remaining and no spend
        self.assertEqual(result, {self.campaign: 100})

    def test_no_budgets(self):
        result = calculate_campaigns_daily_budget()
        self.assertEqual(result, {})

    def test_past_budgets(self):
        magic_mixer.blend(
            models.BudgetLineItem,
            start_date=dates_helper.days_before(self.today, 5),
            end_date=dates_helper.day_before(self.today),
            amount=100,
            credit=self.credit,
            campaign=self.campaign,
        )

        result = calculate_campaigns_daily_budget()
        self.assertEqual(result, {})

    def test_future_budgets(self):
        magic_mixer.blend(
            models.BudgetLineItem,
            start_date=dates_helper.day_after(self.today),
            end_date=dates_helper.days_after(self.today, 5),
            amount=100,
            credit=self.credit,
            campaign=self.campaign,
        )

        result = calculate_campaigns_daily_budget()
        self.assertEqual(result, {})

    def test_calculate_for_one_campaign(self):
        magic_mixer.blend(
            models.BudgetLineItem,
            start_date=dates_helper.days_before(self.today, 5),
            end_date=dates_helper.days_after(self.today, 5),
            amount=100,
            credit=self.credit,
            campaign=self.campaign,
        )

        campaign2 = magic_mixer.blend(models.Campaign, account__agency__uses_realtime_autopilot=True)
        campaign2.settings.update_unsafe(None, autopilot=True)
        credit2 = magic_mixer.blend(
            models.CreditLineItem,
            account=campaign2.account,
            start_date=dates_helper.days_before(self.today, 10),
            end_date=dates_helper.days_after(self.today, 10),
            status=constants.CreditLineItemStatus.SIGNED,
            amount=1000,
        )
        magic_mixer.blend(
            models.BudgetLineItem,
            start_date=dates_helper.days_before(self.today, 5),
            end_date=self.today,
            amount=100,
            credit=credit2,
            campaign=campaign2,
        )

        result = calculate_campaigns_daily_budget()
        # first campaign 100 (total amount) / 6 (remaining days) rounded to 1$
        # second campaign full 100 for last day
        self.assertEqual(result, {self.campaign: 17, campaign2: 100})

        result_for_campaign = calculate_campaigns_daily_budget(campaign2)
        self.assertEqual(result_for_campaign, {campaign2: 100})
