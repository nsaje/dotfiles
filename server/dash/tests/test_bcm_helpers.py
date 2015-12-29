import datetime
from decimal import Decimal

from django.test import TestCase

import dash.models
import dash.bcm_helpers

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
        print 'beee'
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
