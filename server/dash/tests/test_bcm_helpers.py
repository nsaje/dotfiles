from django.test import TestCase

import dash.models
import dash.bcm_helpers

class DeleteCreditTestCase(TestCase):
    fixtures = ['test_io.yaml']

    def test_delete(self):
        self.assertEquals(len(dash.models.BudgetLineItem.objects.filter(credit_id=1)), 1)
        credit = dash.models.CreditLineItem.objects.get(pk=1)
        with self.assertRaises(Exception):
            credit.delete()
        dash.bcm_helpers.delete_credit(credit)
        self.assertEquals(len(dash.models.CreditLineItem.objects.filter(pk=1)), 0)
        self.assertEquals(len(dash.models.BudgetLineItem.objects.filter(credit_id=1)), 0)

class DeleteBudgetTestCase(TestCase):
    fixtures = ['test_io.yaml']

    def test_delete(self):
        budget = dash.models.BudgetLineItem.objects.get(pk=1)
        with self.assertRaises(Exception):
            budget.delete()
        dash.bcm_helpers.delete_budget(budget)
        self.assertEquals(len(dash.models.BudgetLineItem.objects.filter(pk=1)), 0)
