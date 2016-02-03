import datetime
from decimal import Decimal

from django.test import TestCase

import dash.models
import dash.constants
import dash.bcm_helpers
import reports.models

create_credit = dash.models.CreditLineItem.objects.create
create_budget = dash.models.BudgetLineItem.objects.create
create_statement = reports.models.BudgetDailyStatement.objects.create


class AccountCampaignBudgetData(TestCase):
    fixtures = ['test_io.yaml']

    def setUp(self):
        self.start_date = datetime.date.today() - datetime.timedelta(2)
        self.end_date = datetime.date.today() + datetime.timedelta(2)
        self.c = create_credit(
            account_id=2,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=1000,
            flat_fee_cc=1000000,
            license_fee=Decimal('0.1'),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.b = create_budget(
            credit=self.c,
            amount=900,
            start_date=self.start_date,
            end_date=self.end_date,
            campaign_id=1,
        )

        create_statement(
            budget=self.b,
            date=self.end_date - datetime.timedelta(1),
            media_spend_nano=200 * dash.models.TO_NANO_MULTIPLIER,
            data_spend_nano=50 * dash.models.TO_NANO_MULTIPLIER,
            license_fee_nano=25 * dash.models.TO_NANO_MULTIPLIER,
        )

        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=200 * dash.models.TO_NANO_MULTIPLIER,
            data_spend_nano=50 * dash.models.TO_NANO_MULTIPLIER,
            license_fee_nano=25 * dash.models.TO_NANO_MULTIPLIER,
        )

    def test_campaign_budget_data(self):
        budget, spend = dash.bcm_helpers.get_campaign_media_budget_data([1])
        self.assertEqual(budget, {1: Decimal('810.0000')})
        self.assertEqual(spend, {1: Decimal('400.0000')})

    def test_account_budget_data(self):
        budget, spend = dash.bcm_helpers.get_account_media_budget_data([1, 2, 3])
        self.assertEqual(budget, {1: Decimal('80000.00000000'), 2: Decimal('810.00000000')})
        self.assertEqual(spend, {2: Decimal('400.0000')})


class CreditImportTestCase(TestCase):
    fixtures = ['test_io.yaml']

    def test_clean_credit_input(self):
        self.assertEqual(
            dash.bcm_helpers.clean_credit_input(
                account='1',
                valid_from='8/11/2014',
                amount='$5,000.00',
                total_license_fee='$652.17'
            ),
            (1, datetime.date(2014, 8, 11), datetime.date(2015, 8, 11), 5000, Decimal('0.13'), ''),
        )
        self.assertEqual(
            dash.bcm_helpers.clean_credit_input(
                account='1',
                valid_from='8/11/2014',
                valid_to='8/30/2014',
                amount='$5,000.00',
                total_license_fee='$652.17'
            ),
            (1, datetime.date(2014, 8, 11), datetime.date(2014, 8, 30), 5000, Decimal('0.13'), ''),
        )
        self.assertEqual(
            dash.bcm_helpers.clean_credit_input(
                account='1',
                valid_from='8/11/2014',
                valid_to='8/30/2014',
                amount='$5,000.00',
                license_fee='0.20'
            ),
            (1, datetime.date(2014, 8, 11), datetime.date(2014, 8, 30), 5000, Decimal('0.20'), ''),
        )
        self.assertEqual(
            dash.bcm_helpers.clean_credit_input(
                account='1',
                valid_from='8/11/2014',
                valid_to='8/30/2014',
                amount='$5,000.00',
                license_fee='30%'
            ),
            (1, datetime.date(2014, 8, 11), datetime.date(2014, 8, 30), 5000, Decimal('0.30'), ''),
        )

    def test_credit_import(self):
        self.assertEqual(len(dash.models.CreditLineItem.objects.filter(account_id=1)), 1)
        credit = dash.bcm_helpers.import_credit(
            *(1, datetime.date(2015, 1, 1), datetime.date(2015, 12, 31), 10000, Decimal('0.01'), 'Test note')
        )
        self.assertEqual(len(dash.models.CreditLineItem.objects.filter(account_id=1)), 2)
        self.assertEqual(credit.start_date, datetime.date(2015, 1, 1))
        self.assertEqual(credit.end_date, datetime.date(2015, 12, 31))
        self.assertEqual(credit.amount, 10000)


class DeleteCreditTestCase(TestCase):
    fixtures = ['test_io.yaml']

    def test_delete(self):
        self.assertEqual(len(dash.models.BudgetLineItem.objects.filter(credit_id=1)), 1)
        credit = dash.models.CreditLineItem.objects.get(pk=1)
        with self.assertRaises(Exception):
            credit.delete()
        dash.bcm_helpers.delete_credit(credit)
        self.assertEqual(len(dash.models.CreditLineItem.objects.filter(pk=1)), 0)
        self.assertEqual(len(dash.models.BudgetLineItem.objects.filter(credit_id=1)), 0)


class DeleteBudgetTestCase(TestCase):
    fixtures = ['test_io.yaml']

    def test_delete(self):
        budget = dash.models.BudgetLineItem.objects.get(pk=1)
        with self.assertRaises(Exception):
            budget.delete()
        dash.bcm_helpers.delete_budget(budget)
        self.assertEqual(len(dash.models.BudgetLineItem.objects.filter(pk=1)), 0)
