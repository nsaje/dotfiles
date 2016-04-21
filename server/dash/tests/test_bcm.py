from mock import patch
import datetime
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError

from dash import models, constants, forms
from zemauth.models import User
from django.http.request import HttpRequest
import reports.models

TODAY = datetime.datetime(2015, 12, 1).date()
YESTERDAY = TODAY - datetime.timedelta(1)

create_credit = models.CreditLineItem.objects.create
create_budget = models.BudgetLineItem.objects.create
create_statement = reports.models.BudgetDailyStatement.objects.create


@patch('dash.forms.dates_helper.local_today', lambda: TODAY)
class CreditsTestCase(TestCase):
    fixtures = ['test_bcm.yaml']

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
        self.assertFalse('start_date' in err.exception.error_dict)  # we check this in form
        self.assertFalse('end_date' in err.exception.error_dict)  # we check this in form
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

    def test_overlap(self):
        d = datetime.date
        c = create_credit(
            account_id=2,
            start_date=d(2016, 3, 1),
            end_date=d(2016, 3, 31),
            amount=2000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.assertEqual(c.get_overlap(d(2016, 1, 1), d(2016, 1, 31)), (None, None, ))
        self.assertEqual(c.get_overlap(d(2016, 5, 1), d(2016, 5, 31)), (None, None, ))
        self.assertEqual(c.get_overlap(d(2016, 1, 1), d(2016, 3, 15)), (d(2016, 3, 1), d(2016, 3, 15)))
        self.assertEqual(c.get_overlap(d(2016, 3, 16), d(2016, 4, 15)), (d(2016, 3, 16), d(2016, 3, 31)))
        self.assertEqual(c.get_overlap(d(2016, 3, 10), d(2016, 3, 20)), (d(2016, 3, 10), d(2016, 3, 20)))
        self.assertEqual(c.get_overlap(d(2016, 1, 10), d(2016, 4, 20)), (d(2016, 3, 1), d(2016, 3, 31)))

    def test_monthly_flat_fee(self):
        def create_simple_credit(start_date, end_date, amount=2000, flat_fee_cc=900000, license_fee=Decimal('0.456')):
            return create_credit(
                account_id=2,
                start_date=start_date,
                end_date=end_date,
                flat_fee_start_date=start_date,
                flat_fee_end_date=end_date,
                amount=amount,
                flat_fee_cc=flat_fee_cc,
                license_fee=license_fee,
                status=constants.CreditLineItemStatus.SIGNED,
                created_by_id=1,
            )

        self.assertEqual(
            create_simple_credit(
                datetime.date(2016, 3, 1), datetime.date(2016, 3, 31)
            ).get_monthly_flat_fee(), Decimal('90.000')
        )

        self.assertEqual(
            create_simple_credit(
                datetime.date(2016, 2, 1), datetime.date(2016, 3, 10)
            ).get_monthly_flat_fee(), Decimal('45.000')
        )

        self.assertEqual(
            create_simple_credit(
                datetime.date(2016, 2, 1), datetime.date(2016, 2, 10)
            ).get_monthly_flat_fee(), Decimal('90.000')
        )

        self.assertEqual(
            create_simple_credit(
                datetime.date(2016, 3, 1), datetime.date(2016, 5, 31)
            ).get_monthly_flat_fee(), Decimal('30.000')
        )

        self.assertEqual(
            create_simple_credit(
                datetime.date(2016, 4, 1), datetime.date(2016, 6, 30)
            ).get_monthly_flat_fee(), Decimal('30.000')
        )

        self.assertEqual(
            create_simple_credit(
                datetime.date(2016, 1, 1), datetime.date(2016, 3, 31)
            ).get_monthly_flat_fee(), Decimal('30.000')
        )

        self.assertEqual(create_credit(
            account_id=2,
            start_date=datetime.date(2016, 2, 10),
            end_date=datetime.date(2016, 5, 20),
            flat_fee_start_date=datetime.date(2016, 3, 1),
            flat_fee_end_date=datetime.date(2016, 5, 1),
            amount=2000,
            flat_fee_cc=900000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        ).get_monthly_flat_fee(), Decimal('30.000'))

    def test_get_flat_fee_on_date_range_full_month(self):
        d = datetime.date
        full_month_credit = create_credit(
            account_id=2,
            start_date=d(2016, 2, 1),
            end_date=d(2016, 2, 29),
            flat_fee_start_date=d(2016, 2, 1),
            flat_fee_end_date=d(2016, 2, 29),
            amount=2000,
            flat_fee_cc=900000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 1, 30), d(2016, 1, 31)),
            Decimal('0.0000')
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 1, 30), d(2016, 3, 31)),
            Decimal('90.0000')
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 2, 1), d(2016, 2, 29)),
            Decimal('90.0000')
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 2, 10), d(2016, 2, 20)),
            Decimal('90.0000')
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 2, 10), d(2016, 2, 20)),
            Decimal('90.0000')
        )

    def test_get_flat_fee_on_date_range_half_month(self):
        d = datetime.date
        half_month_credit = create_credit(
            account_id=2,
            start_date=d(2016, 2, 10),
            end_date=d(2016, 2, 25),
            flat_fee_start_date=d(2016, 2, 10),
            flat_fee_end_date=d(2016, 2, 25),
            amount=2000,
            flat_fee_cc=900000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(
            half_month_credit.get_flat_fee_on_date_range(d(2016, 1, 1), d(2016, 1, 31)),
            Decimal('0.0000')
        )
        self.assertEqual(
            half_month_credit.get_flat_fee_on_date_range(d(2016, 2, 1), d(2016, 2, 29)),
            Decimal('90.0000')
        )
        self.assertEqual(
            half_month_credit.get_flat_fee_on_date_range(d(2016, 3, 1), d(2016, 3, 31)),
            Decimal('0.0000')
        )

    def test_get_flat_fee_on_date_range_yearly_credit(self):
        d = datetime.date
        yearly_credit = create_credit(
            account_id=2,
            start_date=d(2015, 2, 13),
            end_date=d(2016, 2, 13),
            flat_fee_start_date=d(2015, 3, 1),
            flat_fee_end_date=d(2016, 2, 1),
            amount=2000,
            flat_fee_cc=1200000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2015, 1, 1), d(2015, 1, 31)),
            Decimal('0.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2015, 2, 1), d(2015, 2, 28)),
            Decimal('0.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2015, 3, 1), d(2015, 3, 31)),
            Decimal('10.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2015, 4, 1), d(2015, 4, 30)),
            Decimal('10.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2015, 1, 1), d(2015, 4, 30)),
            Decimal('20.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2014, 1, 1), d(2015, 4, 30)),
            Decimal('20.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2014, 1, 1), d(2016, 4, 30)),
            Decimal('120.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2015, 3, 1), d(2015, 10, 31)),
            Decimal('80.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2015, 1, 1), d(2015, 10, 31)),
            Decimal('80.0000')
        )
        self.assertEqual(
            yearly_credit.get_flat_fee_on_date_range(d(2016, 1, 1), d(2016, 1, 31)),
            Decimal('10.0000')
        )

    def test_get_flat_fee_on_date_range_general_credit(self):
        d = datetime.date
        general_credit = create_credit(
            account_id=2,
            start_date=d(2016, 1, 10),
            end_date=d(2016, 5, 31),
            flat_fee_start_date=d(2016, 1, 10),
            flat_fee_end_date=d(2016, 5, 31),
            amount=2000,
            flat_fee_cc=900000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        flat_fee = 0

        amount = general_credit.get_flat_fee_on_date_range(d(2015, 12, 1), d(2015, 12, 31))
        self.assertEqual(
            amount,
            Decimal('0.0000')
        )
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 1, 1), d(2016, 1, 31))
        self.assertEqual(
            amount,
            Decimal('18.0000'),
        )
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 2, 1), d(2016, 2, 29))
        self.assertEqual(
            amount,
            Decimal('18.0000')
        )
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 3, 1), d(2016, 3, 31))
        self.assertEqual(
            amount,
            Decimal('18.0000')
        )
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 4, 1), d(2016, 4, 30))
        self.assertEqual(
            amount,
            Decimal('18.0000')
        )
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 5, 1), d(2016, 5, 31))
        self.assertEqual(
            amount,
            Decimal('18.0000')
        )
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 6, 1), d(2016, 6, 30))
        self.assertEqual(
            amount,
            Decimal('0.0000')
        )
        flat_fee += amount

        self.assertEqual(flat_fee, Decimal('90.0000'))

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

        create_budget(
            credit=c1,
            amount=1000,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
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
                start_date=TODAY + datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(2),
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
        c.save()  # Editing allowed

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()

        with self.assertRaises(ValidationError) as err:
            c.start_date = TODAY + datetime.timedelta(1)
            c.save()
        self.assertTrue('__all__' in err.exception.error_dict)

        request = HttpRequest()
        request.user = User.objects.get(pk=1)

        c.start_date = TODAY
        c.save()
        c.account.save(request)

        with self.assertRaises(ValidationError) as err:
            c.amount = 111
            c.save()
        self.assertTrue('amount' in err.exception.error_dict)  # amount has a minimum (budgets)

        c.amount = 9999999  # but no maximum
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
            c.delete()  # is signed

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
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            campaign_id=1,
        )

        with self.assertRaises(ValidationError) as err:
            c.start_date = TODAY + datetime.timedelta(1)
            c.save()
        self.assertTrue('__all__' in err.exception.error_dict)

        c.start_date = TODAY  # Rollback
        c.end_date = TODAY + datetime.timedelta(11)
        c.save()  # extending end_date allowed

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


@patch('dash.forms.dates_helper.local_today', lambda: TODAY)
class BudgetsTestCase(TestCase):
    fixtures = ['test_bcm.yaml']

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
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(11),
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
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(11),
                campaign_id=1,
            )
        self.assertTrue('amount' in err.exception.error_dict)
        self.assertTrue('start_date' in err.exception.error_dict)
        self.assertTrue('end_date' in err.exception.error_dict)
        self.assertTrue('credit' in err.exception.error_dict)

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(11),
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
                start_date=TODAY + datetime.timedelta(8),
                end_date=TODAY + datetime.timedelta(4),
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
                start_date=TODAY + datetime.timedelta(4),
                end_date=TODAY + datetime.timedelta(8),
                campaign_id=1,
            )
        self.assertTrue('credit' in err.exception.error_dict)

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()

        b = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=1,
        )

        b.amount = 100000
        with self.assertRaises(ValidationError) as err:
            b.save()
        self.assertTrue('amount' in err.exception.error_dict)
        b.amount = 800  # rollback
        b.save()

        self.assertEqual(b.history.count(), 2)

        b.start_date = TODAY + datetime.timedelta(3)
        b.save()
        self.assertEqual(b.history.count(), 3)

    def test_multiple_budgets(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(10),
            amount=1200,
            flat_fee_cc=2000000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(c.effective_amount(), Decimal('1000'))

        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(5),
            campaign_id=1,
        )
        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY + datetime.timedelta(2),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=1,
        )
        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY + datetime.timedelta(7),
            end_date=TODAY + datetime.timedelta(10),
            campaign_id=1,
        )

        self.assertEqual(c.get_allocated_amount(), 900)

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=101,
                start_date=TODAY + datetime.timedelta(2),
                end_date=TODAY + datetime.timedelta(8),
                campaign_id=1,
            )
        self.assertEqual(err.exception.error_dict['amount'][0][0],
                         'Budget exceeds the total credit amount by $1.00.')

        create_budget(
            credit=c,
            amount=100,
            start_date=TODAY + datetime.timedelta(2),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=1,
        )
        self.assertEqual(c.get_allocated_amount(), 1000)

        c.flat_fee_cc = 3000000
        with self.assertRaises(ValidationError) as err:
            # Cannot add flat fee if tehre is no room
            c.save()

    def test_editing_inactive(self):
        b = models.BudgetLineItem.objects.get(pk=1)

        b.start_date = TODAY  # cannot change inactive budgets
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
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(7),
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
        b.end_date = TODAY + datetime.timedelta(7)
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
                start_date=TODAY + datetime.timedelta(4),
                end_date=TODAY + datetime.timedelta(8),
                campaign_id=1,
            )
        self.assertTrue('credit' in err.exception.error_dict)

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()
        b = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
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
            start_date=TODAY - datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=1,
        )
        b2 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=1,
        )
        b3 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
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
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            campaign_id=1,
        )

        self.assertEqual(b.state(), constants.BudgetLineItemState.PENDING)

        b.start_date = TODAY - datetime.timedelta(1)
        b.save()
        self.assertEqual(b.state(), constants.BudgetLineItemState.ACTIVE)

        b.start_date = TODAY - datetime.timedelta(2)
        with self.assertRaises(ValidationError) as _:
            b.save()  # status prevents editing more
        b.start_date = TODAY - datetime.timedelta(1)  # rollback

        self.assertEqual(b.state(datetime.date(2016, 12, 31)),
                         constants.BudgetLineItemState.INACTIVE)

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
            start_date=TODAY - datetime.timedelta(2),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=1,
        )
        b2 = create_budget(
            credit=c,
            amount=300,
            start_date=TODAY,
            end_date=TODAY + datetime.timedelta(1),
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
            b2.amount = b2.amount + 1
            b2.save()
        self.assertTrue('amount' in err.exception.error_dict)  # canceled credit cannot change amount

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=300,
                start_date=TODAY,
                end_date=TODAY + datetime.timedelta(1),
                campaign_id=1,
            )
        self.assertTrue('credit' in err.exception.error_dict)


@patch('dash.forms.dates_helper.local_today', lambda: TODAY)
class BudgetSpendTestCase(TestCase):
    fixtures = ['test_bcm.yaml']

    def setUp(self):
        self.start_date = TODAY - datetime.timedelta(2)
        self.end_date = TODAY + datetime.timedelta(2)
        self.c = create_credit(
            account_id=2,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.b = create_budget(
            credit=self.c,
            amount=1000,
            start_date=self.start_date,
            end_date=self.end_date,
            campaign_id=1,
        )

    def test_missing_daily_statements(self):
        self.assertEqual(self.b.get_spend_data(), {
            'media_cc': 0,
            'data_cc': 0,
            'license_fee_cc': 0,
            'total_cc': 0,
        })
        self.assertEqual(self.b.get_spend_data(date=self.end_date), {
            'media_cc': 0,
            'data_cc': 0,
            'license_fee_cc': 0,
            'total_cc': 0,
        })

    def test_depleted(self):
        self.assertNotEqual(self.b.state(), constants.BudgetLineItemState.DEPLETED)
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=10000 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=10000 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=1000 * models.TO_NANO_MULTIPLIER,
        )
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = self.end_date - datetime.timedelta(1)
            self.assertNotEqual(self.b.state(), constants.BudgetLineItemState.DEPLETED)
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = self.end_date
            self.assertEqual(self.b.state(), constants.BudgetLineItemState.DEPLETED)
            self.assertNotEqual(
                self.b.state(date=(self.end_date - datetime.timedelta(1))),
                constants.BudgetLineItemState.DEPLETED)

    def test_fixed_date(self):
        self.assertEqual(self.b.get_spend_data(date=self.end_date), {
            (key + '_cc'): 0 for key in ('media', 'data', 'license_fee', 'total')
        })

        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=101 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=20100000000,
        )

        self.assertEqual(self.b.get_spend_data(date=self.end_date), {
            'media_cc': 100 * models.TO_CC_MULTIPLIER,
            'data_cc': 101 * models.TO_CC_MULTIPLIER,
            'license_fee_cc': 201000,
            'total_cc': 2211000,
        })
        self.assertEqual(self.b.get_spend_data(date=self.end_date, use_decimal=True), {
            'media': Decimal('100.0000'),
            'data': Decimal('101.0000'),
            'license_fee': Decimal('20.1000'),
            'total': Decimal('221.1000'),
        })

    def test_last_statement(self):
        create_statement(
            budget=self.b,
            date=self.end_date - datetime.timedelta(1),
            media_spend_nano=90 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=90 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=9 * models.TO_NANO_MULTIPLIER,
        )
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=101 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=20100000000,
        )
        self.assertEqual(self.b.get_spend_data(), {
            'media_cc': 190 * models.TO_CC_MULTIPLIER,
            'data_cc': 191 * models.TO_CC_MULTIPLIER,
            'license_fee_cc': 291000,
            'total_cc': 4101000,
        })
        self.assertEqual(self.b.get_spend_data(use_decimal=True), {
            'media': Decimal('190.0000'),
            'data': Decimal('191.0000'),
            'license_fee': Decimal('29.1000'),
            'total': Decimal('410.1000'),
        })

    def test_get_daily_spend(self):
        create_statement(
            budget=self.b,
            date=self.end_date - datetime.timedelta(1),
            media_spend_nano=90 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=90 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=9 * models.TO_NANO_MULTIPLIER,
        )
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=101 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=20100000000,
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date - datetime.timedelta(2)),
            {
                'media_cc': 0,
                'data_cc': 0,
                'license_fee_cc': 0,
                'total_cc': 0,
            }
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date - datetime.timedelta(1)),
            {
                'media_cc': 90 * models.TO_CC_MULTIPLIER,
                'data_cc': 90 * models.TO_CC_MULTIPLIER,
                'license_fee_cc': 9 * models.TO_CC_MULTIPLIER,
                'total_cc': 189 * models.TO_CC_MULTIPLIER,
            }
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date),
            {
                'media_cc': 100 * models.TO_CC_MULTIPLIER,
                'data_cc': 101 * models.TO_CC_MULTIPLIER,
                'license_fee_cc': 201000,
                'total_cc': 2211000,
            }
        )


@patch('dash.forms.dates_helper.local_today', lambda: TODAY)
class BudgetReserveTestCase(TestCase):
    fixtures = ['test_bcm.yaml']

    def setUp(self):
        self.start_date = TODAY - datetime.timedelta(10)
        self.end_date = TODAY + datetime.timedelta(10)
        self.c = create_credit(
            account_id=2,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=1000,
            license_fee=Decimal('0.456'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.b = create_budget(
            credit=self.c,
            amount=800,
            start_date=self.start_date,
            end_date=self.end_date,
            campaign_id=1,
        )

    def test_editing_budget_amount(self):
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date - datetime.timedelta(1),
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=0,
            license_fee_nano=20 * models.TO_NANO_MULTIPLIER,
        )
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date,
            media_spend_nano=120 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=0,
            license_fee_nano=20 * models.TO_NANO_MULTIPLIER,
        )

        self.b.amount = 900  # can be higher
        self.b.save()
        self.assertEqual(self.b.amount, models.BudgetLineItem.objects.get(pk=self.b.pk).amount)

        self.b.amount = 500  # can be lower, we check this in views
        self.b.save()
        self.assertEqual(self.b.amount, models.BudgetLineItem.objects.get(pk=self.b.pk).amount)

    def test_reserve_calculation(self):
        reports.models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date + datetime.timedelta(0),
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=0,
            license_fee_nano=20 * models.TO_NANO_MULTIPLIER,
        )

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = self.start_date
            self.assertEqual(self.b.get_spend_data(), {
                'license_fee_cc': 20 * models.TO_CC_MULTIPLIER,
                'media_cc': 100 * models.TO_CC_MULTIPLIER,
                'data_cc': 0 * models.TO_CC_MULTIPLIER,
                'total_cc': 120 * models.TO_CC_MULTIPLIER
            })
            self.assertEqual(self.b.get_reserve_amount_cc(), 6 * models.TO_CC_MULTIPLIER)

        reports.models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date + datetime.timedelta(1),
            media_spend_nano=80 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=10 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=20 * models.TO_NANO_MULTIPLIER,
        )

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = self.start_date + datetime.timedelta(1)
            self.assertEqual(self.b.get_spend_data(),
                             {'license_fee_cc': 40 * models.TO_CC_MULTIPLIER, 'media_cc': 180 * models.TO_CC_MULTIPLIER,
                              'data_cc': 10 * models.TO_CC_MULTIPLIER, 'total_cc': 230 * models.TO_CC_MULTIPLIER})
            # Same reserve because we didn't have yesterday's values for the previous statement
            self.assertEqual(self.b.get_reserve_amount_cc(), 6 * models.TO_CC_MULTIPLIER)

        reports.models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date + datetime.timedelta(2),
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=0,
            license_fee_nano=20 * models.TO_NANO_MULTIPLIER,
        )

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = self.start_date + datetime.timedelta(2)
            self.assertEqual(self.b.get_spend_data(),
                             {'license_fee_cc': 60 * models.TO_CC_MULTIPLIER, 'media_cc': 280 * models.TO_CC_MULTIPLIER,
                              'data_cc': 10 * models.TO_CC_MULTIPLIER, 'total_cc': 350 * models.TO_CC_MULTIPLIER})
            self.assertEqual(self.b.get_reserve_amount_cc(), 55000)

    def test_asset_return(self):
        today = datetime.date(2015, 11, 11)
        credit = models.CreditLineItem.objects.create(
            account_id=1,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=1000,
            license_fee=Decimal('0.2'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        budget = models.BudgetLineItem.objects.create(
            credit=credit,
            amount=1000,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 10),
            campaign_id=1,
        )

        reports.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=today - datetime.timedelta(1),
            media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=0,
            license_fee_nano=20 * models.TO_NANO_MULTIPLIER,
        )
        for num in range(0, 5):
            reports.models.BudgetDailyStatement.objects.create(
                budget=budget,
                date=today + datetime.timedelta(num),
                media_spend_nano=100 * models.TO_NANO_MULTIPLIER,
                data_spend_nano=0,
                license_fee_nano=20 * models.TO_NANO_MULTIPLIER,
            )

        self.assertEqual(budget.freed_cc, 0)

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 274 * models.TO_CC_MULTIPLIER)

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 12)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 274 * models.TO_CC_MULTIPLIER)

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 13)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 274 * models.TO_CC_MULTIPLIER)

        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 14)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 280 * models.TO_CC_MULTIPLIER)

    def test_mayfly_budget(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal('0.1'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b = create_budget(
            credit=c,
            amount=1000,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=1,
        )
        create_statement(
            budget=b,
            date=TODAY - datetime.timedelta(1),
            media_spend_nano=700 * models.TO_NANO_MULTIPLIER,
            data_spend_nano=100 * models.TO_NANO_MULTIPLIER,
            license_fee_nano=80 * models.TO_NANO_MULTIPLIER,
        )  # Spend = 880, unused = 120, reserve = 44, free = 10
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = TODAY
            b.free_inactive_allocated_assets()
        self.assertEqual(b.freed_cc, 76 * models.TO_CC_MULTIPLIER)
        with patch('utils.dates_helper.local_today') as mock_now:
            mock_now.return_value = TODAY + datetime.timedelta(5)
            b.free_inactive_allocated_assets()
        self.assertEqual(b.freed_cc, 120 * models.TO_CC_MULTIPLIER)

    def test_freed_budget_validation(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal('0.1'),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b = create_budget(
            credit=c,
            amount=1000,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=1,
        )
        self.assertEqual(len(c.budgets.all()), 1)
        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=500,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY - datetime.timedelta(1),
                campaign_id=1,
            )
        self.assertEqual(err.exception.error_dict['amount'][0][0],
                         u'Budget exceeds the total credit amount by $500.00.')
        self.assertEqual(len(c.budgets.all()), 1)

        b.freed_cc = 200 * models.TO_CC_MULTIPLIER
        b.save()

        with self.assertRaises(ValidationError) as err:
            create_budget(
                credit=c,
                amount=201,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY - datetime.timedelta(1),
                campaign_id=1,
            )
        self.assertEqual(err.exception.error_dict['amount'][0][0],
                         u'Budget exceeds the total credit amount by $1.00.')
        self.assertEqual(len(c.budgets.all()), 1)

        create_budget(
            credit=c,
            amount=200,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=1,
        )
        self.assertEqual(len(c.budgets.all()), 2)
