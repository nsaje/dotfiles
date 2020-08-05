import datetime
from decimal import Decimal

import mock
from django import test

import core.features.bcm
import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import service


class CampaignPacingTestCase(test.TestCase):
    def _create_daily_budget_statements(self, budget):
        values = {
            "local_base_media_spend_nano": 4000000000,
            "local_base_data_spend_nano": 3000000000,
            "local_service_fee_nano": 1000000000,
            "local_license_fee_nano": 1000000000,
            "local_margin_nano": 1000000000,
        }
        dates = [
            budget.end_date - datetime.timedelta(days=n) for n in range((budget.end_date - budget.start_date).days + 1)
        ]
        for date in dates:
            magic_mixer.blend(core.features.bcm.BudgetDailyStatement, budget=budget, date=date, **values)

    def setUp(self):
        self.today = dates_helper.local_today()
        self.campaign = magic_mixer.blend(core.models.Campaign)
        self.credit = core.features.bcm.CreditLineItem.objects.create_unsafe(
            account=self.campaign.account,
            start_date=self.today - datetime.timedelta(10),
            end_date=self.today + datetime.timedelta(10),
            amount=1000,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=None,
        )

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_yesterday_data_complete(self):
        self.assertTrue(service.CampaignPacing(self.campaign).yesterday_data_complete)

    def test_yesterday_data_incomplete(self):
        self.assertFalse(service.CampaignPacing(self.campaign).yesterday_data_complete)

    def test_no_budgets(self):
        pacing_data = service.CampaignPacing(self.campaign).data

        for window, data in pacing_data.items():
            self.assertEqual(self.today - datetime.timedelta(window), data.start_date)
            self.assertEqual(self.today - datetime.timedelta(1), data.end_date)
            self.assertEqual(0, data.attributed_spend)
            self.assertEqual(0, data.total_budget)
            self.assertEqual(0, data.pacing)

    def test_no_spend_budget_expired(self):
        core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=100,
            start_date=self.today - datetime.timedelta(10),
            end_date=self.today - datetime.timedelta(1),
        )
        pacing_data = service.CampaignPacing(self.campaign).data

        for window, data in pacing_data.items():
            self.assertEqual(self.today - datetime.timedelta(window), data.start_date)
            self.assertEqual(self.today - datetime.timedelta(1), data.end_date)
            self.assertEqual(100, data.total_budget)
            self.assertEqual(0, data.attributed_spend)
            self.assertEqual(0, data.pacing)

    def test_no_spend_budget_active(self):
        core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=100,
            start_date=self.today - datetime.timedelta(7),
            end_date=self.today + datetime.timedelta(2),
        )
        pacing_data = service.CampaignPacing(self.campaign).data
        total_budget_values = {
            service.PACING_WINDOW_1_DAY: 100 / 4,
            service.PACING_WINDOW_3_DAYS: 100 / 2,
            service.PACING_WINDOW_7_DAYS: 100 * 7 / 10,
        }

        for window, data in pacing_data.items():
            self.assertEqual(self.today - datetime.timedelta(window), data.start_date)
            self.assertEqual(self.today - datetime.timedelta(1), data.end_date)
            self.assertEqual(total_budget_values[window], int(data.total_budget))
            self.assertEqual(0, data.attributed_spend)
            self.assertEqual(0, data.pacing)

    def test_overlap(self):
        enveloping_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=180,
            start_date=self.today - datetime.timedelta(8),
            end_date=self.today,
        )
        self._create_daily_budget_statements(enveloping_budget)

        left_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=80,
            start_date=self.today - datetime.timedelta(9),
            end_date=self.today - datetime.timedelta(2),
        )
        self._create_daily_budget_statements(left_budget)

        right_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=60,
            start_date=self.today - datetime.timedelta(4),
            end_date=self.today + datetime.timedelta(1),
        )
        self._create_daily_budget_statements(right_budget)

        middle_budget = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            amount=40,
            start_date=self.today - datetime.timedelta(6),
            end_date=self.today - datetime.timedelta(3),
        )
        self._create_daily_budget_statements(middle_budget)

        pacing_data = service.CampaignPacing(self.campaign).data
        total_budget_values = {
            service.PACING_WINDOW_1_DAY: (180 - 70) / 2 * 1 + (60 - 30) / 3 * 1,  # 65
            service.PACING_WINDOW_3_DAYS: 157.5,
            service.PACING_WINDOW_7_DAYS: 288.75,
        }
        attributed_spend_values = {
            service.PACING_WINDOW_1_DAY: 20,
            service.PACING_WINDOW_3_DAYS: 90,
            service.PACING_WINDOW_7_DAYS: 210,
        }
        pacing_values = {
            service.PACING_WINDOW_1_DAY: Decimal("30.7692"),
            service.PACING_WINDOW_3_DAYS: Decimal("57.1429"),
            service.PACING_WINDOW_7_DAYS: Decimal("72.7273"),
        }

        for window, data in pacing_data.items():
            self.assertEqual(self.today - datetime.timedelta(window), data.start_date)
            self.assertEqual(self.today - datetime.timedelta(1), data.end_date)
            self.assertEqual(total_budget_values[window], data.total_budget)
            self.assertEqual(attributed_spend_values[window], data.attributed_spend)
            self.assertAlmostEqual(pacing_values[window], data.pacing, delta=Decimal("0.0001"))
