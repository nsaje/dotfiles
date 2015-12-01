import datetime
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from dash import models, constants, forms
from zemauth.models import User
from django.http.request import HttpRequest

TODAY = datetime.datetime.utcnow().date()
YESTERDAY = datetime.datetime.utcnow().date() - datetime.timedelta(1)    

create_credit = models.CreditLineItem.objects.create
create_budget = models.BudgetLineItem.objects.create

class CreditsTestCase(TestCase):
    fixtures = ['test_io.yaml']
    
    def test_creation(self):
        self.assertEqual(models.CreditLineItem.objects.all().count(), 2)
        
        with self.assertRaises(ValidationError) as err:
            create_credit(
                account_id=1,
                start_date=YESTERDAY,
                end_date=YESTERDAY,
                amount=1000,
                license_fee=Decimal('1.2'),
                status=constants.CreditLineItemStatus.SIGNED,
                created_by_id=1,
            )
        self.assertTrue('license_fee' in err.exception.error_dict)
        self.assertFalse('start_date' in err.exception.error_dict) # we check this in form
        self.assertFalse('end_date' in err.exception.error_dict) # we check this in form
        self.assertEqual(models.CreditLineItem.objects.all().count(), 2)

        with self.assertRaises(ValidationError) as err:
            create_credit(
                account_id=1,
                start_date=YESTERDAY,
                end_date=YESTERDAY,
                amount=1000,
                license_fee=Decimal('1.2'),
                status=constants.CreditLineItemStatus.SIGNED,
                created_by_id=1,
            )
        self.assertTrue('license_fee' in err.exception.error_dict)
        self.assertFalse('start_date' in err.exception.error_dict)
        self.assertFalse('end_date' in err.exception.error_dict)
        self.assertEqual(models.CreditLineItem.objects.all().count(), 2)
        
        credit = create_credit(
            account_id=1,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        with self.assertRaises(AssertionError):
            # Cannot delete signed credits
            credit.delete()

        credit = create_credit(
            account_id=1,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )
        credit.delete()


    def test_statuses(self):
        c1 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=2000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c2 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c3 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        b = create_budget(
            credit=c1,
            amount=1000,
            start_date=TODAY+datetime.timedelta(1),
            end_date=TODAY+datetime.timedelta(2),
            campaign_id=1,
        )

        with self.assertRaises(AssertionError):
            c1.delete()
        with self.assertRaises(AssertionError):
            c2.delete()
        with self.assertRaises(AssertionError):
            c3.delete()

        c1.cancel()
        c2.cancel()
        c3.cancel()

        self.assertEqual(c1.status, constants.CreditLineItemStatus.CANCELED)
        self.assertEqual(c2.status, constants.CreditLineItemStatus.CANCELED)
        self.assertEqual(c3.status, constants.CreditLineItemStatus.CANCELED)

        with self.assertRaises(AssertionError):
            models.CreditLineItem.objects.filter(pk__in=(c1.pk, c2.pk, c3.pk)).delete()

        with self.assertRaises(ValidationError):
            create_budget(
                credit=c1,
                amount=500,
                start_date=TODAY+datetime.timedelta(1),
                end_date=TODAY+datetime.timedelta(2),
                campaign_id=1,
            )

    def test_multidelete(self):
        c1 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )
        c2 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c3 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.CANCELED,
            created_by_id=1,
        )
        with self.assertRaises(AssertionError):
            models.CreditLineItem.objects.filter(pk__in=(c1.pk, c2.pk, c3.pk)).delete()
        
        models.CreditLineItem.objects.filter(pk__in=(c1.pk, )).delete()
        


    def test_editing_existing(self):
        c = models.CreditLineItem.objects.get(pk=1)
        c.start_date = TODAY
        c.end_date = TODAY + datetime.timedelta(10)
        c.amount = 1111111
        c.save() # Editing allowed

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()

        with self.assertRaises(ValidationError) as err:
            c.start_date = TODAY + datetime.timedelta(1)
            c.save()
        self.assertTrue('__all__' in err.exception.error_dict)

        c.start_date = TODAY # return to previous value
        
        with self.assertRaises(ValidationError) as err:
            c.amount = 111
            c.save()
        self.assertTrue('amount' in err.exception.error_dict) # amount has a minimum (budgets)

        c.amount = 9999999 # but no maximum
        c.save()

        with self.assertRaises(ValidationError) as err:
            c.end_date = c.budgets.all()[0].end_date - datetime.timedelta(1)
            c.save()
        self.assertTrue('end_date' in err.exception.error_dict)

        c = models.CreditLineItem.objects.get(pk=1)
        with self.assertRaises(ValidationError) as err:
            c.start_date = YESTERDAY
            c.save()
        self.assertTrue('__all__' in err.exception.error_dict)

        c = models.CreditLineItem.objects.get(pk=1)
        c.end_date = c.end_date + datetime.timedelta(1)
        c.save()

        c = models.CreditLineItem.objects.get(pk=1)
        with self.assertRaises(ValidationError) as err:
            c.license_fee = Decimal('1.2')
            c.save()
        self.assertTrue('__all__' in err.exception.error_dict)
        
        with self.assertRaises(AssertionError):
            c.delete() # is signed

        c = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            created_by_id=1,
        )

        c.start_date = TODAY
        c.end_date = TODAY + datetime.timedelta(10)
        c.save()

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()
        
        b = create_budget(
            credit=c,
            amount=1000,
            start_date=TODAY+datetime.timedelta(1),
            end_date=TODAY+datetime.timedelta(2),
            campaign_id=1,
        )

        with self.assertRaises(ValidationError) as err:
            c.start_date = TODAY + datetime.timedelta(1)
            c.save()
        self.assertTrue('__all__' in err.exception.error_dict)

        c.start_date = TODAY # Rollback
        c.end_date = TODAY + datetime.timedelta(11)
        c.save() # extending end_date allowed
        
        
        b.delete()
        c.save()

    def test_form(self):
        credit_form = forms.CreditLineItemForm({
            'account': 2,
            'start_date': str(TODAY - datetime.timedelta(10)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': 100000,
            'license_fee': 0.2,
            'status': 1,
            'comment': 'Test case',
        })
        self.assertFalse(credit_form.is_valid())
        self.assertTrue(credit_form.errors)

        credit_form = forms.CreditLineItemForm({
            'account': 2,
            'start_date': str(TODAY + datetime.timedelta(1)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': 100000,
            'license_fee': 0.2,
            'status': 1,
            'comment': 'Test case',
        })
        self.assertTrue(credit_form.is_valid())
        self.assertFalse(credit_form.errors)

        credit_form = forms.CreditLineItemForm({
            'account': 2,
            'start_date': str(TODAY + datetime.timedelta(1)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': -1000,
            'license_fee': 0.2,
            'status': 1,
            'comment': 'Test case',
        })
        self.assertFalse(credit_form.is_valid())
        self.assertTrue(credit_form.errors)

        # Check if model validation is triggered
        credit_form = forms.CreditLineItemForm({
            'account': 2,
            'start_date': str(TODAY + datetime.timedelta(1)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': 1000,
            'license_fee': 1.2,
            'status': 1,
            'comment': 'Test case',
        })
        self.assertFalse(credit_form.is_valid())
        self.assertTrue(credit_form.errors)
        

    def test_history(self):
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        c = models.CreditLineItem(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )
        c.save(request=request)
        history = models.CreditHistory.objects.filter(credit=c).order_by('created_dt')
        self.assertEqual(history.count(), 1)

        c.license_fee = Decimal('0.5')
        c.save(request=request)
        history = models.CreditHistory.objects.filter(credit=c).order_by('created_dt')
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0].created_by, request.user)

        self.assertEqual(history[0].snapshot['license_fee'], '0.456')
        self.assertEqual(history[1].snapshot['license_fee'], '0.5')
        
        c.license_fee = Decimal('0.1')
        c.save(request=request)

        self.assertEqual(history[0].snapshot['license_fee'], '0.456')
        self.assertEqual(history[1].snapshot['license_fee'], '0.5')
        self.assertEqual(history[2].snapshot['license_fee'], '0.1')


class BudgetsTestCase(TestCase):
    fixtures = ['test_io.yaml']

    def test_creation(self):
        self.assertEqual(models.CreditLineItem.objects.all().count(), 2)
        c = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal('0.456'),
            created_by_id=1,
        )
        
        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=10000,
                start_date=TODAY-datetime.timedelta(1),
                end_date=TODAY+datetime.timedelta(11),
                campaign_id=1,
            )
        self.assertTrue('amount' in err.exception.error_dict)
        self.assertTrue('start_date' in err.exception.error_dict)
        self.assertTrue('end_date' in err.exception.error_dict)
        self.assertTrue('credit' in err.exception.error_dict)

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=-10000,
                start_date=TODAY-datetime.timedelta(1),
                end_date=TODAY+datetime.timedelta(11),
                campaign_id=1,
            )
        self.assertFalse('amount' in err.exception.error_dict)
        self.assertTrue('start_date' in err.exception.error_dict)
        self.assertTrue('end_date' in err.exception.error_dict)
        self.assertTrue('credit' in err.exception.error_dict)

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY-datetime.timedelta(1),
                end_date=TODAY+datetime.timedelta(11),
                campaign_id=1,
            )
        self.assertFalse('amount' in err.exception.error_dict)
        self.assertTrue('start_date' in err.exception.error_dict)
        self.assertTrue('end_date' in err.exception.error_dict)
        self.assertTrue('credit' in err.exception.error_dict)

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY+datetime.timedelta(8),
                end_date=TODAY+datetime.timedelta(4),
                campaign_id=1,
            )
        self.assertFalse('amount' in err.exception.error_dict)
        self.assertFalse('start_date' in err.exception.error_dict)
        self.assertTrue('end_date' in err.exception.error_dict)
        self.assertTrue('credit' in err.exception.error_dict)

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY+datetime.timedelta(4),
                end_date=TODAY+datetime.timedelta(8),
                campaign_id=1,
            )
        self.assertTrue('credit' in err.exception.error_dict)

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()

        b = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY+datetime.timedelta(4),
            end_date=TODAY+datetime.timedelta(8),
            campaign_id=1,
        )

        b.amount = 100000
        with self.assertRaises(ValidationError) as err:
            b.save()
        self.assertTrue('amount' in err.exception.error_dict)
        b.amount = 800 # rollback
        b.save()

        self.assertEqual(b.history.count(), 2)

        b.start_date = TODAY+datetime.timedelta(3)
        b.save()
        self.assertEqual(b.history.count(), 3)

    def test_multiple_budgets(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY+datetime.timedelta(1),
            end_date=TODAY+datetime.timedelta(5),
            campaign_id=1,
        )
        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY+datetime.timedelta(2),
            end_date=TODAY+datetime.timedelta(8),
            campaign_id=1,
        )
        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY+datetime.timedelta(7),
            end_date=TODAY+datetime.timedelta(10),
            campaign_id=1,
        )

        self.assertEqual(c.get_allocated_amount(), 900)

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=101,
                start_date=TODAY+datetime.timedelta(2),
                end_date=TODAY+datetime.timedelta(8),
                campaign_id=1,
            )
        self.assertEqual(err.exception.error_dict['amount'][0][0],
                         'Budget exceeds the total credit amount by $1.00.')

        create_budget(
            credit=c,
            amount=100,
            start_date=TODAY+datetime.timedelta(2),
            end_date=TODAY+datetime.timedelta(8),
            campaign_id=1,
        )
        self.assertEqual(c.get_allocated_amount(), 1000)
            

    def test_editing_inactive(self):
        b = models.BudgetLineItem.objects.get(pk=1)

        b.start_date = TODAY # cannot change inactive budgets
        with self.assertRaises(ValidationError) as err:
            b.save()
        self.assertTrue('__all__' in err.exception.error_dict)
        self.assertNotEqual(b.start_date, models.BudgetLineItem.objects.get(pk=1).start_date)
        

    def test_history(self):
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        c = models.CreditLineItem(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal('0.456'),
            created_by_id=1,
            status=constants.CreditLineItemStatus.SIGNED,
        )
        c.save(request=request)

        b = models.BudgetLineItem(
            credit=c,
            amount=800,
            start_date=TODAY+datetime.timedelta(4),
            end_date=TODAY+datetime.timedelta(7),
            campaign_id=1,
        )
        b.save(request=request)
        history = models.BudgetHistory.objects.filter(budget=b).order_by('-created_dt')
        self.assertEqual(history.count(), 1)
        self.assertEqual(history[0].created_by, request.user)

        self.assertEqual(b.amount, history[0].snapshot['amount'])
        self.assertEqual(str(b.start_date), history[0].snapshot['start_date'])
        self.assertEqual(str(b.end_date), history[0].snapshot['end_date'])

        prev_end_date = str(b.end_date)
        b.end_date = TODAY+datetime.timedelta(7)
        b.save(request=request)
        
        history = models.BudgetHistory.objects.filter(budget=b).order_by('-created_dt')
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0].created_by, request.user)
        self.assertEqual(str(b.end_date), history[0].snapshot['end_date'])
        self.assertEqual(prev_end_date, history[1].snapshot['end_date'])

    def test_unsigned_credit(self):
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )
        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY+datetime.timedelta(4),
                end_date=TODAY+datetime.timedelta(8),
                campaign_id=1,
            )
        self.assertTrue('credit' in err.exception.error_dict)
        
        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()
        b = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY+datetime.timedelta(4),
            end_date=TODAY+datetime.timedelta(8),
            campaign_id=1,
        )
        self.assertEqual(b.credit, c)

    def test_delete(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=10000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b1 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY-datetime.timedelta(4),
            end_date=TODAY+datetime.timedelta(8),
            campaign_id=1,
        )
        b2 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY+datetime.timedelta(4),
            end_date=TODAY+datetime.timedelta(8),
            campaign_id=1,
        )
        b3 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY+datetime.timedelta(4),
            end_date=TODAY+datetime.timedelta(8),
            campaign_id=1,
        )
        with self.assertRaises(AssertionError) as _:
            b1.delete()
        with self.assertRaises(AssertionError) as _:
            models.BudgetLineItem.objects.filter(pk__in=[b1.pk, b2.pk, b3.pk]).delete()

        models.BudgetLineItem.objects.filter(pk__in=[b2.pk]).delete()
        b3.delete()

        self.assertEqual(c.budgets.all().count(), 1)
        
        
    def test_form(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        budget_form = forms.BudgetLineItemForm({
            'credit': c.id,
            'start_date': str(TODAY - datetime.timedelta(10)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': 100,
            'status': 1,
            'campaign': 1, 
            'comment': 'Test case',
        })
        self.assertFalse(budget_form.is_valid())
        self.assertTrue(budget_form.errors)

        budget_form = forms.BudgetLineItemForm({
            'credit': c.id,
            'start_date': str(TODAY + datetime.timedelta(1)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': 100,
            'status': 1,
            'campaign': 1, 
            'comment': 'Test case',
        })
        self.assertTrue(budget_form.is_valid())
        self.assertFalse(budget_form.errors)

        budget_form = forms.BudgetLineItemForm({
            'credit': c.id,            
            'start_date': str(TODAY + datetime.timedelta(1)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': -100,
            'status': 1,
            'campaign': 1, 
            'comment': 'Test case',
        })
        self.assertFalse(budget_form.is_valid())
        self.assertTrue(budget_form.errors)

        # Check if model validation is triggered
        budget_form = forms.BudgetLineItemForm({
            'credit': c.id,            
            'start_date': str(TODAY + datetime.timedelta(1)),
            'end_date': str(TODAY + datetime.timedelta(10)),
            'amount': 1100,
            'status': 1,
            'campaign': 1, 
            'comment': 'Test case',
        })
        self.assertFalse(budget_form.is_valid())
        self.assertTrue(budget_form.errors)

    def test_budget_status(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        b = create_budget(
            credit=c,
            amount=1000,
            start_date=TODAY+datetime.timedelta(1),
            end_date=TODAY+datetime.timedelta(2),
            campaign_id=1,
        )

        self.assertEqual(b.state(), constants.BudgetLineItemState.PENDING)

        b.start_date = TODAY - datetime.timedelta(1)
        b.save()
        self.assertEqual(b.state(), constants.BudgetLineItemState.ACTIVE)

        b.start_date = TODAY - datetime.timedelta(2)
        with self.assertRaises(ValidationError) as _:
            b.save() # status prevents editing more
        b.start_date = TODAY - datetime.timedelta(1) # rollback

        self.assertEqual(b.state(datetime.date(2016, 12, 31)),
                         constants.BudgetLineItemState.INACTIVE)

        backup = b.get_spend_amount
        b.get_spend_amount = lambda: 10000
        self.assertEqual(b.state(),
                         constants.BudgetLineItemState.DEPLETED)

        b.get_spend_amount = backup

    def test_credit_cancel(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(2),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        b1 = create_budget(
            credit=c,
            amount=300,
            start_date=TODAY-datetime.timedelta(2),
            end_date=TODAY-datetime.timedelta(1),
            campaign_id=1,
        )
        b2 = create_budget(
            credit=c,
            amount=300,
            start_date=TODAY,
            end_date=TODAY+datetime.timedelta(1),
            campaign_id=1,
        )

        self.assertEqual(b2.state(),
                         constants.BudgetLineItemState.ACTIVE)
            
        b2.end_date = TODAY
        b2.save()
        self.assertEqual(b2.state(),
                         constants.BudgetLineItemState.ACTIVE)
        self.assertEqual(b1.state(),
                         constants.BudgetLineItemState.INACTIVE)
        c.cancel()
        self.assertEqual(b2.state(),
                         constants.BudgetLineItemState.ACTIVE)
        self.assertEqual(b1.state(),
                         constants.BudgetLineItemState.INACTIVE)

        with self.assertRaises(ValidationError) as err:
            b2 = create_budget(
                credit=c,
                amount=300,
                start_date=TODAY,
                end_date=TODAY+datetime.timedelta(1),
                campaign_id=1,
            )
        self.assertTrue('credit' in err.exception.error_dict)
