from mock import patch
import datetime
import io
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.management import call_command

from utils import converters
import utils.exc
import core.features.bcm.exceptions

from dash import models, constants, forms
from zemauth.models import User
from django.http.request import HttpRequest

TODAY = datetime.datetime(2015, 12, 1).date()
YESTERDAY = TODAY - datetime.timedelta(1)

create_credit = models.CreditLineItem.objects.create_unsafe
create_budget = models.BudgetLineItem.objects.create_unsafe
create_statement = models.BudgetDailyStatement.objects.create


@patch("dash.forms.dates_helper.local_today", lambda: TODAY)
class CreditsTestCase(TestCase):
    fixtures = ["test_bcm.yaml"]

    def test_creation(self):
        starting_num_credits = models.CreditLineItem.objects.all().count()
        self.assertEqual(models.CreditLineItem.objects.all().count(), starting_num_credits)

        with self.assertRaises(ValidationError) as err:
            create_credit(
                account_id=1,
                start_date=YESTERDAY,
                end_date=YESTERDAY,
                amount=1000,
                license_fee=Decimal("1.2"),
                status=constants.CreditLineItemStatus.SIGNED,
                created_by_id=1,
            )
        self.assertTrue("license_fee" in err.exception.error_dict)
        self.assertFalse("start_date" in err.exception.error_dict)  # we check this in form
        self.assertFalse("end_date" in err.exception.error_dict)  # we check this in form
        self.assertEqual(models.CreditLineItem.objects.all().count(), starting_num_credits)

        with self.assertRaises(ValidationError) as err:
            create_credit(
                account_id=1,
                start_date=YESTERDAY,
                end_date=YESTERDAY,
                amount=1000,
                license_fee=Decimal("1.2"),
                status=constants.CreditLineItemStatus.SIGNED,
                created_by_id=1,
            )
        self.assertTrue("license_fee" in err.exception.error_dict)
        self.assertFalse("start_date" in err.exception.error_dict)
        self.assertFalse("end_date" in err.exception.error_dict)
        self.assertEqual(models.CreditLineItem.objects.all().count(), starting_num_credits)

        credit = create_credit(
            account_id=1,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
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
            license_fee=Decimal("0.456"),
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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.assertEqual(c.get_overlap(d(2016, 1, 1), d(2016, 1, 31)), (None, None))
        self.assertEqual(c.get_overlap(d(2016, 5, 1), d(2016, 5, 31)), (None, None))
        self.assertEqual(c.get_overlap(d(2016, 1, 1), d(2016, 3, 15)), (d(2016, 3, 1), d(2016, 3, 15)))
        self.assertEqual(c.get_overlap(d(2016, 3, 16), d(2016, 4, 15)), (d(2016, 3, 16), d(2016, 3, 31)))
        self.assertEqual(c.get_overlap(d(2016, 3, 10), d(2016, 3, 20)), (d(2016, 3, 10), d(2016, 3, 20)))
        self.assertEqual(c.get_overlap(d(2016, 1, 10), d(2016, 4, 20)), (d(2016, 3, 1), d(2016, 3, 31)))

    def test_monthly_flat_fee(self):
        def create_simple_credit(start_date, end_date, amount=2000, flat_fee_cc=900000, license_fee=Decimal("0.456")):
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
            create_simple_credit(datetime.date(2016, 3, 1), datetime.date(2016, 3, 31)).get_monthly_flat_fee(),
            Decimal("90.000"),
        )

        self.assertEqual(
            create_simple_credit(datetime.date(2016, 2, 1), datetime.date(2016, 3, 10)).get_monthly_flat_fee(),
            Decimal("45.000"),
        )

        self.assertEqual(
            create_simple_credit(datetime.date(2016, 2, 1), datetime.date(2016, 2, 10)).get_monthly_flat_fee(),
            Decimal("90.000"),
        )

        self.assertEqual(
            create_simple_credit(datetime.date(2016, 3, 1), datetime.date(2016, 5, 31)).get_monthly_flat_fee(),
            Decimal("30.000"),
        )

        self.assertEqual(
            create_simple_credit(datetime.date(2016, 4, 1), datetime.date(2016, 6, 30)).get_monthly_flat_fee(),
            Decimal("30.000"),
        )

        self.assertEqual(
            create_simple_credit(datetime.date(2016, 1, 1), datetime.date(2016, 3, 31)).get_monthly_flat_fee(),
            Decimal("30.000"),
        )

        self.assertEqual(
            create_credit(
                account_id=2,
                start_date=datetime.date(2016, 2, 10),
                end_date=datetime.date(2016, 5, 20),
                flat_fee_start_date=datetime.date(2016, 3, 1),
                flat_fee_end_date=datetime.date(2016, 5, 1),
                amount=2000,
                flat_fee_cc=900000,
                license_fee=Decimal("0.456"),
                status=constants.CreditLineItemStatus.SIGNED,
                created_by_id=1,
            ).get_monthly_flat_fee(),
            Decimal("30.000"),
        )

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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 1, 30), d(2016, 1, 31)), Decimal("0.0000")
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 1, 30), d(2016, 3, 31)), Decimal("90.0000")
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 2, 1), d(2016, 2, 29)), Decimal("90.0000")
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 2, 10), d(2016, 2, 20)), Decimal("90.0000")
        )
        self.assertEqual(
            full_month_credit.get_flat_fee_on_date_range(d(2016, 2, 10), d(2016, 2, 20)), Decimal("90.0000")
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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(half_month_credit.get_flat_fee_on_date_range(d(2016, 1, 1), d(2016, 1, 31)), Decimal("0.0000"))
        self.assertEqual(
            half_month_credit.get_flat_fee_on_date_range(d(2016, 2, 1), d(2016, 2, 29)), Decimal("90.0000")
        )
        self.assertEqual(half_month_credit.get_flat_fee_on_date_range(d(2016, 3, 1), d(2016, 3, 31)), Decimal("0.0000"))

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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2015, 1, 1), d(2015, 1, 31)), Decimal("0.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2015, 2, 1), d(2015, 2, 28)), Decimal("0.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2015, 3, 1), d(2015, 3, 31)), Decimal("10.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2015, 4, 1), d(2015, 4, 30)), Decimal("10.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2015, 1, 1), d(2015, 4, 30)), Decimal("20.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2014, 1, 1), d(2015, 4, 30)), Decimal("20.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2014, 1, 1), d(2016, 4, 30)), Decimal("120.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2015, 3, 1), d(2015, 10, 31)), Decimal("80.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2015, 1, 1), d(2015, 10, 31)), Decimal("80.0000"))
        self.assertEqual(yearly_credit.get_flat_fee_on_date_range(d(2016, 1, 1), d(2016, 1, 31)), Decimal("10.0000"))

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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        flat_fee = 0

        amount = general_credit.get_flat_fee_on_date_range(d(2015, 12, 1), d(2015, 12, 31))
        self.assertEqual(amount, Decimal("0.0000"))
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 1, 1), d(2016, 1, 31))
        self.assertEqual(amount, Decimal("18.0000"))
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 2, 1), d(2016, 2, 29))
        self.assertEqual(amount, Decimal("18.0000"))
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 3, 1), d(2016, 3, 31))
        self.assertEqual(amount, Decimal("18.0000"))
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 4, 1), d(2016, 4, 30))
        self.assertEqual(amount, Decimal("18.0000"))
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 5, 1), d(2016, 5, 31))
        self.assertEqual(amount, Decimal("18.0000"))
        flat_fee += amount

        amount = general_credit.get_flat_fee_on_date_range(d(2016, 6, 1), d(2016, 6, 30))
        self.assertEqual(amount, Decimal("0.0000"))
        flat_fee += amount

        self.assertEqual(flat_fee, Decimal("90.0000"))

    def test_campaign_credit(self):
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        agency = models.Agency()
        agency.name = "123"
        agency.save(request)

        acc = models.Account.objects.get(pk=10)
        acc.agency = agency
        acc.save(request)

        c1 = create_credit(
            account_id=1,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=2000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c2 = create_credit(
            agency=agency,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c3 = create_credit(
            account_id=10,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        with self.assertRaises(utils.exc.ValidationError) as err:
            create_budget(
                credit=c1,
                amount=10,
                start_date=TODAY + datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(2),
                campaign_id=10,
            )
        self.assertTrue("Campaign" in str(err.exception.errors[0]))
        with self.assertRaises(utils.exc.ValidationError) as err:
            create_budget(
                credit=c2,
                amount=10,
                start_date=TODAY + datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(2),
                campaign_id=1,
            )
        self.assertTrue("Campaign" in str(err.exception.errors[0]))
        with self.assertRaises(utils.exc.ValidationError) as err:
            create_budget(
                credit=c2,
                amount=10,
                start_date=TODAY + datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(2),
                campaign_id=1,
            )
        self.assertTrue("Campaign" in str(err.exception.errors[0]))

        create_budget(
            credit=c1,
            amount=10,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            campaign_id=1,
        )
        create_budget(
            credit=c2,
            amount=10,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            campaign_id=10,
        )
        create_budget(
            credit=c3,
            amount=10,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            campaign_id=10,
        )

    def test_statuses(self):
        c1 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=2000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c2 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c3 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        create_budget(
            credit=c1,
            amount=1000,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            campaign_id=2,
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

        with self.assertRaises(utils.exc.ValidationError):
            create_budget(
                credit=c1,
                amount=500,
                start_date=TODAY + datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(2),
                campaign_id=2,
            )

    def test_multidelete(self):
        c1 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )
        c2 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        c3 = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.CANCELED,
            created_by_id=1,
        )
        with self.assertRaises(AssertionError):
            models.CreditLineItem.objects.filter(pk__in=(c1.pk, c2.pk, c3.pk)).delete()

        models.CreditLineItem.objects.filter(pk__in=(c1.pk,)).delete()

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
        self.assertTrue("__all__" in err.exception.error_dict)

        request = HttpRequest()
        request.user = User.objects.get(pk=1)

        c.start_date = TODAY
        c.save()
        c.account.save(request)

        with self.assertRaises(ValidationError) as err:
            c.amount = 111
            c.save()
        self.assertTrue("amount" in err.exception.error_dict)  # amount has a minimum (budgets)

        c.amount = 9999999  # but no maximum
        c.save()

        with self.assertRaises(ValidationError) as err:
            c.end_date = c.budgets.all()[0].end_date - datetime.timedelta(1)
            c.save()
        self.assertTrue("end_date" in err.exception.error_dict)

        c = models.CreditLineItem.objects.get(pk=1)
        with self.assertRaises(ValidationError) as err:
            c.start_date = YESTERDAY
            c.save()
        self.assertTrue("__all__" in err.exception.error_dict)

        c = models.CreditLineItem.objects.get(pk=1)
        c.end_date = c.end_date + datetime.timedelta(1)
        c.save()

        c = models.CreditLineItem.objects.get(pk=1)
        with self.assertRaises(ValidationError) as err:
            c.license_fee = Decimal("1.2")
            c.save()
        self.assertTrue("__all__" in err.exception.error_dict)

        with self.assertRaises(AssertionError):
            c.delete()  # is signed

        c = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
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
            campaign_id=2,
        )

        with self.assertRaises(ValidationError) as err:
            c.start_date = TODAY + datetime.timedelta(1)
            c.save()
        self.assertTrue("__all__" in err.exception.error_dict)

        c.start_date = TODAY  # Rollback
        c.end_date = TODAY + datetime.timedelta(11)
        c.save()  # extending end_date allowed

        b.delete()
        c.save()

    def test_form(self):
        credit_form = forms.CreditLineItemForm(
            {
                "account": 2,
                "start_date": str(TODAY - datetime.timedelta(10)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": 100000,
                "license_fee": 0.2,
                "status": 1,
                "currency": constants.Currency.USD,
                "comment": "Test case",
            }
        )
        self.assertFalse(credit_form.is_valid())
        self.assertTrue(credit_form.errors)

        credit_form = forms.CreditLineItemForm(
            {
                "account": 2,
                "start_date": str(TODAY + datetime.timedelta(1)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": 100000,
                "license_fee": 0.2,
                "status": 1,
                "currency": constants.Currency.USD,
                "comment": "Test case",
            }
        )
        self.assertTrue(credit_form.is_valid())
        self.assertFalse(credit_form.errors)

        credit_form = forms.CreditLineItemForm(
            {
                "account": 2,
                "start_date": str(TODAY + datetime.timedelta(1)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": -1000,
                "license_fee": 0.2,
                "status": 1,
                "currency": constants.Currency.USD,
                "comment": "Test case",
            }
        )
        self.assertFalse(credit_form.is_valid())
        self.assertTrue(credit_form.errors)

        # Check if model validation is triggered
        credit_form = forms.CreditLineItemForm(
            {
                "account": 2,
                "start_date": str(TODAY + datetime.timedelta(1)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": 1000,
                "license_fee": 1.2,
                "status": 1,
                "currency": constants.Currency.USD,
                "comment": "Test case",
            }
        )
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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )
        c.save(request=request)
        history = models.CreditHistory.objects.filter(credit=c).order_by("created_dt")
        self.assertEqual(history.count(), 1)

        c.license_fee = Decimal("0.5")
        c.save(request=request)
        history = models.CreditHistory.objects.filter(credit=c).order_by("created_dt")
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0].created_by, request.user)

        self.assertEqual(history[0].snapshot["license_fee"], "0.456")
        self.assertEqual(history[1].snapshot["license_fee"], "0.5")

        c.license_fee = Decimal("0.1")
        c.save(request=request)

        self.assertEqual(history[0].snapshot["license_fee"], "0.456")
        self.assertEqual(history[1].snapshot["license_fee"], "0.5")
        self.assertEqual(history[2].snapshot["license_fee"], "0.1")


@patch("dash.forms.dates_helper.local_today", lambda: TODAY)
class BudgetsTestCase(TestCase):
    fixtures = ["test_bcm.yaml"]

    def test_creation(self):
        starting_num_credits = models.CreditLineItem.objects.all().count()
        self.assertEqual(models.CreditLineItem.objects.all().count(), starting_num_credits)
        c = create_credit(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal("0.456"),
            created_by_id=1,
        )

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=10000,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(11),
                campaign_id=2,
            )
        error_classes = (
            core.features.bcm.exceptions.StartDateInvalid,
            core.features.bcm.exceptions.EndDateInvalid,
            core.features.bcm.exceptions.BudgetAmountExceededCreditAmount,
            core.features.bcm.exceptions.CreditPending,
        )
        self.assertTrue(all([isinstance(e, error_classes) for e in err.exception.errors]))

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=-10000,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(11),
                campaign_id=2,
            )
        error_classes = (
            core.features.bcm.exceptions.StartDateInvalid,
            core.features.bcm.exceptions.EndDateInvalid,
            core.features.bcm.exceptions.BudgetAmountNegative,
            core.features.bcm.exceptions.CreditPending,
        )
        self.assertTrue(len(err.exception.errors), 4)
        self.assertTrue(all([isinstance(e, error_classes) for e in err.exception.errors]))

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY + datetime.timedelta(11),
                campaign_id=2,
            )
        error_classes = (
            core.features.bcm.exceptions.StartDateInvalid,
            core.features.bcm.exceptions.EndDateInvalid,
            core.features.bcm.exceptions.CreditPending,
        )
        self.assertTrue(len(err.exception.errors), 3)
        self.assertTrue(all([isinstance(e, error_classes) for e in err.exception.errors]))

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY + datetime.timedelta(8),
                end_date=TODAY + datetime.timedelta(4),
                campaign_id=2,
            )
        error_classes = (
            core.features.bcm.exceptions.StartDateBiggerThanEndDate,
            core.features.bcm.exceptions.CreditPending,
        )
        self.assertTrue(len(err.exception.errors), 2)
        self.assertTrue(all([isinstance(e, error_classes) for e in err.exception.errors]))

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY + datetime.timedelta(4),
                end_date=TODAY + datetime.timedelta(8),
                campaign_id=2,
            )
        self.assertTrue(isinstance(err.exception.errors[0], core.features.bcm.exceptions.CreditPending))

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()

        b = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=2,
        )

        b.amount = 100000
        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            b.save()
        self.assertTrue(
            isinstance(err.exception.errors[0], core.features.bcm.exceptions.BudgetAmountExceededCreditAmount)
        )
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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(c.effective_amount(), Decimal("1000"))

        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(5),
            campaign_id=2,
        )
        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY + datetime.timedelta(2),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=2,
        )
        create_budget(
            credit=c,
            amount=300,
            start_date=TODAY + datetime.timedelta(7),
            end_date=TODAY + datetime.timedelta(10),
            campaign_id=2,
        )

        self.assertEqual(c.get_allocated_amount(), 900)

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=101,
                start_date=TODAY + datetime.timedelta(2),
                end_date=TODAY + datetime.timedelta(8),
                campaign_id=2,
            )
        self.assertEqual(str(err.exception.errors[0]), "Budget exceeds the total credit amount by $1.00.")

        create_budget(
            credit=c,
            amount=100,
            start_date=TODAY + datetime.timedelta(2),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=2,
        )
        self.assertEqual(c.get_allocated_amount(), 1000)

        c.flat_fee_cc = 3000000
        with self.assertRaises(ValidationError) as err:
            # Cannot add flat fee if tehre is no room
            c.save()

    def test_editing_inactive(self):
        b = models.BudgetLineItem.objects.get(pk=1)

        b.start_date = TODAY  # cannot change inactive budgets
        with self.assertRaises(core.features.bcm.exceptions.CanNotChangeStartDate):
            b.save()
        self.assertNotEqual(b.start_date, models.BudgetLineItem.objects.get(pk=1).start_date)

    def test_history(self):
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        c = models.CreditLineItem(
            account_id=2,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal("0.456"),
            created_by_id=1,
            status=constants.CreditLineItemStatus.SIGNED,
        )
        c.save(request=request)

        b = models.BudgetLineItem(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(7),
            campaign_id=2,
        )
        b.save(request=request)
        history = models.BudgetHistory.objects.filter(budget=b).order_by("-created_dt")
        self.assertEqual(history.count(), 1)
        self.assertEqual(history[0].created_by, request.user)

        self.assertEqual(b.amount, history[0].snapshot["amount"])
        self.assertEqual(str(b.start_date), history[0].snapshot["start_date"])
        self.assertEqual(str(b.end_date), history[0].snapshot["end_date"])

        prev_end_date = str(b.end_date)
        b.end_date = TODAY + datetime.timedelta(7)
        b.save(request=request)

        history = models.BudgetHistory.objects.filter(budget=b).order_by("-created_dt")
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0].created_by, request.user)
        self.assertEqual(str(b.end_date), history[0].snapshot["end_date"])
        self.assertEqual(prev_end_date, history[1].snapshot["end_date"])

    def test_unsigned_credit(self):
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )
        with self.assertRaises(utils.exc.ValidationError) as err:
            create_budget(
                credit=c,
                amount=800,
                start_date=TODAY + datetime.timedelta(4),
                end_date=TODAY + datetime.timedelta(8),
                campaign_id=2,
            )
        self.assertTrue("credit" in str(err.exception.errors[0]))

        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()
        b = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=2,
        )
        self.assertEqual(b.credit, c)

    def test_delete(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=10000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b1 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY - datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=2,
        )
        b2 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=2,
        )
        b3 = create_budget(
            credit=c,
            amount=800,
            start_date=TODAY + datetime.timedelta(4),
            end_date=TODAY + datetime.timedelta(8),
            campaign_id=2,
        )
        with self.assertRaises(AssertionError):
            b1.delete()
        with self.assertRaises(AssertionError):
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
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        budget_form = forms.BudgetLineItemForm(
            {
                "credit": c.id,
                "start_date": str(TODAY - datetime.timedelta(10)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": 100,
                "status": 1,
                "campaign": 2,
                "comment": "Test case",
            }
        )
        self.assertFalse(budget_form.is_valid())
        self.assertTrue(budget_form.errors)

        budget_form = forms.BudgetLineItemForm(
            {
                "credit": c.id,
                "start_date": str(TODAY + datetime.timedelta(1)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": 100,
                "status": 1,
                "campaign": 2,
                "comment": "Test case",
            }
        )
        self.assertTrue(budget_form.is_valid())
        self.assertFalse(budget_form.errors)

        budget_form = forms.BudgetLineItemForm(
            {
                "credit": c.id,
                "start_date": str(TODAY + datetime.timedelta(1)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": -100,
                "status": 1,
                "campaign": 2,
                "comment": "Test case",
            }
        )
        with self.assertRaises(utils.exc.ValidationError):
            budget_form.is_valid()

        budget_form = forms.BudgetLineItemForm(
            {
                "credit": c.id,
                "start_date": str(TODAY + datetime.timedelta(1)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": -100,
                "status": 1,
                "campaign": 1,
                "comment": "Test case",
            }
        )
        with self.assertRaises(utils.exc.ValidationError):
            budget_form.is_valid()

        # Check if model validation is triggered
        budget_form = forms.BudgetLineItemForm(
            {
                "credit": c.id,
                "start_date": str(TODAY + datetime.timedelta(1)),
                "end_date": str(TODAY + datetime.timedelta(10)),
                "amount": 1100,
                "status": 1,
                "campaign": 2,
                "comment": "Test case",
            }
        )
        with self.assertRaises(utils.exc.MultipleValidationError):
            budget_form.is_valid()

    def test_budget_status(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        b = create_budget(
            credit=c,
            amount=1000,
            start_date=TODAY + datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(2),
            campaign_id=2,
        )

        self.assertEqual(b.state(), constants.BudgetLineItemState.PENDING)

        b.start_date = TODAY - datetime.timedelta(1)
        b.save()
        self.assertEqual(b.state(), constants.BudgetLineItemState.ACTIVE)

        b.start_date = TODAY - datetime.timedelta(2)
        with self.assertRaises(core.features.bcm.exceptions.CanNotChangeStartDate):
            b.save()  # status prevents editing more
        b.start_date = TODAY - datetime.timedelta(1)  # rollback

        self.assertEqual(b.state(datetime.date(2016, 12, 31)), constants.BudgetLineItemState.INACTIVE)

    def test_credit_cancel(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(2),
            end_date=TODAY + datetime.timedelta(2),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        b1 = create_budget(
            credit=c,
            amount=300,
            start_date=TODAY - datetime.timedelta(2),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=2,
        )
        b2 = create_budget(
            credit=c, amount=300, start_date=TODAY, end_date=TODAY + datetime.timedelta(1), campaign_id=2
        )

        self.assertEqual(b2.state(), constants.BudgetLineItemState.ACTIVE)

        b2.end_date = TODAY
        b2.save()
        self.assertEqual(b2.state(), constants.BudgetLineItemState.ACTIVE)
        self.assertEqual(b1.state(), constants.BudgetLineItemState.INACTIVE)
        c.cancel()
        self.assertEqual(b2.state(), constants.BudgetLineItemState.ACTIVE)
        self.assertEqual(b1.state(), constants.BudgetLineItemState.INACTIVE)

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            b2.amount = b2.amount + 1
            b2.save()

        self.assertTrue(isinstance(err.exception.errors[0], core.features.bcm.exceptions.BudgetAmountCannotChange))
        self.assertEqual(str(err.exception.errors[0]), "Canceled credit's budget amounts cannot change.")

        with self.assertRaises(core.features.bcm.exceptions.CreditCanceled) as err:
            create_budget(credit=c, amount=300, start_date=TODAY, end_date=TODAY + datetime.timedelta(1), campaign_id=2)
        self.assertEqual(str(err.exception), "Canceled credits cannot have new budget items.")


@patch("dash.forms.dates_helper.local_today", lambda: TODAY)
class BudgetSpendTestCase(TestCase):
    fixtures = ["test_bcm.yaml"]

    def setUp(self):
        self.start_date = TODAY - datetime.timedelta(2)
        self.end_date = TODAY + datetime.timedelta(2)
        self.c = create_credit(
            account_id=2,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        self.b = create_budget(
            credit=self.c,
            amount=1000,
            start_date=self.start_date,
            end_date=self.end_date,
            campaign_id=2,
            margin=Decimal("0.123"),
        )

    def test_missing_daily_statements(self):
        self.assertEqual(
            self.b.get_spend_data(),
            {"media": 0, "data": 0, "license_fee": 0, "margin": 0, "et_total": 0, "etf_total": 0, "etfm_total": 0},
        )

    def test_get_spend_margin(self):
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=100 * converters.CURRENCY_TO_NANO,
            license_fee_nano=20 * converters.CURRENCY_TO_NANO,
            margin_nano=33 * converters.CURRENCY_TO_NANO,
        )

        self.assertEqual(
            self.b.get_spend_data(date=self.end_date),
            {
                "media": Decimal("100.0000"),
                "data": Decimal("100.0000"),
                "license_fee": Decimal("20.0000"),
                "margin": Decimal("33.0000"),
                "et_total": Decimal("200.0000"),
                "etf_total": Decimal("220.0000"),
                "etfm_total": Decimal("253.0000"),
            },
        )

    def test_depleted(self):
        self.assertNotEqual(self.b.state(), constants.BudgetLineItemState.DEPLETED)
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=10000 * converters.CURRENCY_TO_NANO,
            data_spend_nano=10000 * converters.CURRENCY_TO_NANO,
            license_fee_nano=1000 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = self.end_date - datetime.timedelta(1)
            self.assertNotEqual(self.b.state(), constants.BudgetLineItemState.DEPLETED)
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = self.end_date
            self.assertEqual(self.b.state(), constants.BudgetLineItemState.DEPLETED)
            self.assertNotEqual(
                self.b.state(date=(self.end_date - datetime.timedelta(1))), constants.BudgetLineItemState.DEPLETED
            )

    def test_fixed_date(self):
        self.assertEqual(
            self.b.get_spend_data(date=self.end_date),
            {key: 0 for key in ("media", "data", "license_fee", "margin", "et_total", "etf_total", "etfm_total")},
        )

        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=101 * converters.CURRENCY_TO_NANO,
            license_fee_nano=20100000000,
            margin_nano=0,
        )
        self.assertEqual(
            self.b.get_spend_data(date=self.end_date),
            {
                "media": Decimal("100.0000"),
                "data": Decimal("101.0000"),
                "license_fee": Decimal("20.1000"),
                "margin": Decimal("0"),
                "et_total": Decimal("201.0000"),
                "etf_total": Decimal("221.1000"),
                "etfm_total": Decimal("221.1000"),
            },
        )

    def test_last_statement(self):
        create_statement(
            budget=self.b,
            date=self.end_date - datetime.timedelta(1),
            media_spend_nano=90 * converters.CURRENCY_TO_NANO,
            data_spend_nano=90 * converters.CURRENCY_TO_NANO,
            license_fee_nano=9 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=101 * converters.CURRENCY_TO_NANO,
            license_fee_nano=20100000000,
            margin_nano=0,
        )
        self.assertEqual(
            self.b.get_spend_data(),
            {
                "media": Decimal("190.0000"),
                "data": Decimal("191.0000"),
                "license_fee": Decimal("29.1000"),
                "margin": Decimal("0"),
                "et_total": Decimal("381.0000"),
                "etf_total": Decimal("410.1000"),
                "etfm_total": Decimal("410.1000"),
            },
        )

    def test_get_daily_spend(self):
        create_statement(
            budget=self.b,
            date=self.end_date - datetime.timedelta(1),
            media_spend_nano=90 * converters.CURRENCY_TO_NANO,
            data_spend_nano=90 * converters.CURRENCY_TO_NANO,
            license_fee_nano=9 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=101 * converters.CURRENCY_TO_NANO,
            license_fee_nano=20100000000,
            margin_nano=0,
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date - datetime.timedelta(2)),
            {"media": 0, "data": 0, "license_fee": 0, "margin": 0, "et_total": 0, "etf_total": 0, "etfm_total": 0},
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date - datetime.timedelta(1)),
            {
                "media": 90,
                "data": 90,
                "license_fee": 9,
                "margin": 0,
                "et_total": 180,
                "etf_total": 189,
                "etfm_total": 189,
            },
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date),
            {
                "media": 100,
                "data": 101,
                "license_fee": Decimal("20.1"),
                "margin": 0,
                "et_total": Decimal("201.0"),
                "etf_total": Decimal("221.1"),
                "etfm_total": Decimal("221.1"),
            },
        )

    def test_get_daily_spend_margin(self):
        create_statement(
            budget=self.b,
            date=self.end_date - datetime.timedelta(1),
            media_spend_nano=90 * converters.CURRENCY_TO_NANO,
            data_spend_nano=90 * converters.CURRENCY_TO_NANO,
            license_fee_nano=9 * converters.CURRENCY_TO_NANO,
            margin_nano=Decimal("28.35") * converters.CURRENCY_TO_NANO,
        )
        create_statement(
            budget=self.b,
            date=self.end_date,
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=101 * converters.CURRENCY_TO_NANO,
            license_fee_nano=20100000000,
            margin_nano=Decimal("33.165") * converters.CURRENCY_TO_NANO,
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date - datetime.timedelta(2)),
            {"media": 0, "data": 0, "license_fee": 0, "margin": 0, "et_total": 0, "etf_total": 0, "etfm_total": 0},
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date - datetime.timedelta(1)),
            {
                "media": 90,
                "data": 90,
                "license_fee": 9,
                "margin": Decimal("28.35"),
                "et_total": Decimal("180.0000"),
                "etf_total": Decimal("189.0000"),
                "etfm_total": Decimal("217.35"),
            },
        )
        self.assertEqual(
            self.b.get_daily_spend(self.end_date),
            {
                "media": 100,
                "data": 101,
                "license_fee": Decimal("20.1"),
                "margin": Decimal("33.165"),
                "et_total": Decimal("201.0000"),
                "etf_total": Decimal("221.1000"),
                "etfm_total": Decimal("254.2650"),
            },
        )


@patch("utils.dates_helper.local_today", return_value=TODAY)
class BudgetReserveTestCase(TestCase):
    fixtures = ["test_bcm.yaml"]

    def setUp(self):
        self.start_date = TODAY + datetime.timedelta(10)
        self.end_date = TODAY + datetime.timedelta(20)
        self.c = create_credit(
            account_id=2,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        with patch("dash.forms.dates_helper.local_today", return_value=TODAY):
            self.b = create_budget(
                credit=self.c, amount=800, start_date=self.start_date, end_date=self.end_date, campaign_id=2
            )

    def test_editing_budget_amount(self, mock_local_today):
        mock_local_today.return_value = TODAY
        models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date - datetime.timedelta(1),
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=0,
            license_fee_nano=20 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )
        models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date,
            media_spend_nano=120 * converters.CURRENCY_TO_NANO,
            data_spend_nano=0,
            license_fee_nano=20 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )

        self.b.amount = 900  # can be higher
        self.b.save()
        self.assertEqual(self.b.amount, models.BudgetLineItem.objects.get(pk=self.b.pk).amount)

        self.b.campaign.real_time_campaign_stop = True
        self.b.amount = 500  # can be lower, we check this in views
        self.b.save()
        self.assertEqual(self.b.amount, models.BudgetLineItem.objects.get(pk=self.b.pk).amount)

    def test_reserve_calculation(self, mock_local_today):
        models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date + datetime.timedelta(0),
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=0,
            license_fee_nano=20 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = self.start_date
            self.assertEqual(
                self.b.get_spend_data(),
                {
                    "license_fee": 20,
                    "media": 100,
                    "data": 0,
                    "et_total": 100,
                    "etf_total": 120,
                    "etfm_total": 120,
                    "margin": 0,
                },
            )
            self.assertEqual(self.b.get_reserve_amount_cc(), 6 * converters.CURRENCY_TO_CC)

        models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date + datetime.timedelta(1),
            media_spend_nano=80 * converters.CURRENCY_TO_NANO,
            data_spend_nano=10 * converters.CURRENCY_TO_NANO,
            license_fee_nano=20 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = self.start_date + datetime.timedelta(1)
            self.assertEqual(
                self.b.get_spend_data(),
                {
                    "license_fee": 40,
                    "media": 180,
                    "data": 10,
                    "margin": 0,
                    "et_total": 190,
                    "etf_total": 230,
                    "etfm_total": 230,
                },
            )
            # Same reserve because we didn't have yesterday's values for the previous statement
            self.assertEqual(self.b.get_reserve_amount_cc(), 6 * converters.CURRENCY_TO_CC)

        models.BudgetDailyStatement.objects.create(
            budget=self.b,
            date=self.start_date + datetime.timedelta(2),
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=0,
            license_fee_nano=20 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = self.start_date + datetime.timedelta(2)
            self.assertEqual(
                self.b.get_spend_data(),
                {
                    "license_fee": 60,
                    "media": 280,
                    "data": 10,
                    "margin": 0,
                    "et_total": 290,
                    "etf_total": 350,
                    "etfm_total": 350,
                },
            )
            self.assertEqual(self.b.get_reserve_amount_cc(), 55000)

    def test_asset_return(self, mock_local_today):
        today = datetime.date(2015, 11, 11)
        credit = create_credit(
            account_id=1,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=1000,
            license_fee=Decimal("0.2"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        budget = create_budget(
            credit=credit,
            amount=1000,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 10),
            campaign_id=1,
        )

        create_statement(
            budget=budget,
            date=today - datetime.timedelta(1),
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=0,
            license_fee_nano=20 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )
        for num in range(0, 5):
            models.BudgetDailyStatement.objects.create(
                budget=budget,
                date=today + datetime.timedelta(num),
                media_spend_nano=100 * converters.CURRENCY_TO_NANO,
                data_spend_nano=0,
                license_fee_nano=20 * converters.CURRENCY_TO_NANO,
                margin_nano=0,
            )

        self.assertEqual(budget.freed_cc, 0)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 274 * converters.CURRENCY_TO_CC)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 12)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 274 * converters.CURRENCY_TO_CC)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 13)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 274 * converters.CURRENCY_TO_CC)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 14)
            budget.free_inactive_allocated_assets()

        self.assertEqual(budget.freed_cc, 280 * converters.CURRENCY_TO_CC)

    def test_asset_return_overlaping_budgets(self, mock_local_today):
        today = datetime.date(2015, 11, 11)
        credit = create_credit(
            account_id=1,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=1000,
            license_fee=Decimal("0.2"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        budget1 = create_budget(
            credit=credit,
            amount=500,
            freed_cc=1000000,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 10),
            campaign_id=1,
        )
        create_budget(
            credit=credit,
            amount=600,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 10),
            campaign_id=1,
        )

        create_statement(
            budget=budget1,
            date=today - datetime.timedelta(1),
            media_spend_nano=300 * converters.CURRENCY_TO_NANO,
            data_spend_nano=0,
            license_fee_nano=0 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 14)
            budget1.free_inactive_allocated_assets()

        self.assertEqual(budget1.freed_cc, 200 * converters.CURRENCY_TO_CC)

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=credit,
                amount=200,
                start_date=datetime.date(2015, 11, 1),
                end_date=datetime.date(2015, 11, 10),
                campaign_id=1,
            )
        self.assertTrue(
            isinstance(err.exception.errors[0], core.features.bcm.exceptions.BudgetAmountExceededCreditAmount)
        )
        self.assertEqual(
            str(err.exception.errors[0]),
            "Budget exceeds the total credit amount by $100.00.",  # isn't really testing overlapping?
        )

    def test_mayfly_budget(self, mock_local_today):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b = create_budget(
            credit=c,
            amount=1000,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=2,
        )
        create_statement(
            budget=b,
            date=TODAY - datetime.timedelta(1),
            media_spend_nano=700 * converters.CURRENCY_TO_NANO,
            data_spend_nano=100 * converters.CURRENCY_TO_NANO,
            license_fee_nano=80 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )  # Spend = 880, unused = 120, reserve = 44, free = 10
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = TODAY
            b.free_inactive_allocated_assets()
        self.assertEqual(b.freed_cc, 76 * converters.CURRENCY_TO_CC)
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = TODAY + datetime.timedelta(5)
            b.free_inactive_allocated_assets()
        self.assertEqual(b.freed_cc, 120 * converters.CURRENCY_TO_CC)

    def test_freed_budget_validation(self, mock_local_today):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal("0.456"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b = create_budget(
            credit=c,
            amount=1000,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=2,
        )
        self.assertEqual(len(c.budgets.all()), 1)
        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=500,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY - datetime.timedelta(1),
                campaign_id=2,
            )
        self.assertTrue(
            isinstance(err.exception.errors[0], core.features.bcm.exceptions.BudgetAmountExceededCreditAmount)
        )
        self.assertEqual(str(err.exception.errors[0]), "Budget exceeds the total credit amount by $500.00.")
        self.assertEqual(len(c.budgets.all()), 1)

        b.freed_cc = 200 * converters.CURRENCY_TO_CC
        b.save()

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            create_budget(
                credit=c,
                amount=201,
                start_date=TODAY - datetime.timedelta(1),
                end_date=TODAY - datetime.timedelta(1),
                campaign_id=2,
            )
        self.assertTrue(
            isinstance(err.exception.errors[0], core.features.bcm.exceptions.BudgetAmountExceededCreditAmount)
        )
        self.assertEqual(str(err.exception.errors[0]), "Budget exceeds the total credit amount by $1.00.")
        self.assertEqual(len(c.budgets.all()), 1)

        create_budget(
            credit=c,
            amount=200,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY - datetime.timedelta(1),
            campaign_id=2,
        )
        self.assertEqual(len(c.budgets.all()), 2)


@patch("utils.dates_helper.local_today", lambda: TODAY)
class BCMCommandTestCase(TestCase):
    fixtures = ["test_bcm.yaml"]

    def setUp(self):
        self.c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal("0.1"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.b1 = create_budget(
            credit=self.c,
            amount=200,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(1),
            campaign_id=2,
        )
        self.b2 = create_budget(
            credit=self.c,
            amount=500,
            start_date=TODAY - datetime.timedelta(1),
            end_date=TODAY + datetime.timedelta(1),
            campaign_id=2,
        )

    def _call_command(self, *args, **kwargs):
        output = io.StringIO()
        if "stdout" not in kwargs:
            kwargs["stdout"] = output
        call_command(*args, **kwargs)
        return output.getvalue()

    def test_list_budget(self):
        self.assertEqual(
            self._call_command("bcm", "list", "budgets", str(self.b1.pk), str(self.b2.pk)),
            """ - #22 test account 2, test campaign 2, 2015-11-30 - 2015-12-02 ($200, freed $0.0000, margin 0.0000)
 - #23 test account 2, test campaign 2, 2015-11-30 - 2015-12-02 ($500, freed $0.0000, margin 0.0000)\n""".format(
                self.b1.pk, self.b2.pk
            ),
        )

    def test_list_credit(self):
        self.assertEqual(
            self._call_command("bcm", "list", "credits", str(self.c.pk)),
            """ - #{} test account 2, 2015-11-30 - 2015-12-02 ($1000, fee 0.1000%, flat $0.0000)
""".format(
                self.c.pk
            ),
        )

    def test_update_budget_amount(self):
        self._call_command("bcm", "update", "budgets", str(self.b1.pk), "--amount", "300", "--no-confirm")
        self.b1.refresh_from_db()
        self.b2.refresh_from_db()
        self.assertEqual(self.b1.amount, 300)
        self.assertEqual(self.b2.amount, 500)

    def test_update_budget_start_date(self):
        self._call_command("bcm", "update", "budgets", str(self.b1.pk), "--start_date", str(TODAY), "--no-confirm")
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.start_date, TODAY)

    def test_update_budget_end_date(self):
        self._call_command("bcm", "update", "budgets", str(self.b1.pk), "--end_date", str(TODAY), "--no-confirm")
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.end_date, TODAY)

    def test_update_budget_freed_cc(self):
        self._call_command("bcm", "update", "budgets", str(self.b1.pk), "--freed_cc", "1234", "--no-confirm")
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.freed_cc, 1234)

    def test_update_budget_margin(self):
        self.assertEqual(self.b1.margin, Decimal("0"))
        self._call_command("bcm", "update", "budgets", str(self.b1.pk), "--margin", "0.15", "--no-confirm")
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.margin, Decimal("0.15"))

    def test_update_budget_multiple_fields(self):
        self._call_command(
            "bcm", "update", "budgets", str(self.b1.pk), "--freed_cc", "100000", "--amount", "150", "--no-confirm"
        )
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.freed_cc, 100000)
        self.assertEqual(self.b1.amount, 150)

    def test_update_budget_freed_cc_too_large_value(self):
        with self.assertRaises(SystemExit):
            self._call_command("bcm", "update", "budgets", str(self.b1.pk), "--freed_cc", "2000001", "--no-confirm")
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.freed_cc, 0)
        self._call_command(
            "bcm",
            "update",
            "budgets",
            str(self.b1.pk),
            "--freed_cc",
            "2000001",
            "--no-confirm",
            "--skip-spend-validation",
        )
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.freed_cc, 2000001)

    def test_update_multiple_budget_freed_cc(self):
        self._call_command(
            "bcm", "update", "budgets", "--credits", str(self.c.pk), "--freed_cc", "4321", "--no-confirm"
        )
        self.b1.refresh_from_db()
        self.b2.refresh_from_db()
        self.assertEqual(self.b1.freed_cc, 4321)
        self.assertEqual(self.b2.freed_cc, 4321)

    def test_update_budget_amount_with_too_large_value(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "budgets", str(self.b1.pk), "--amount", "800", "--no-confirm", stderr=err
            )
        self.b1.refresh_from_db()
        self.b2.refresh_from_db()
        self.assertEqual(err.getvalue(), "Validation failed.\n")
        self.assertEqual(self.b1.amount, 200)

    def test_update_budget_start_date_with_too_early_date(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm",
                "update",
                "budgets",
                str(self.b1.pk),
                "--start_date",
                str(TODAY - datetime.timedelta(2)),
                "--no-confirm",
                stderr=err,
            )
        self.assertEqual(err.getvalue(), "Validation failed.\n")
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.start_date, TODAY - datetime.timedelta(1))

    def test_update_budget_end_date_with_invalid_date(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm",
                "update",
                "budgets",
                str(self.b1.pk),
                "--end_date",
                str(TODAY - datetime.timedelta(100)),
                "--no-confirm",
                stderr=err,
            )
        self.assertEqual(err.getvalue(), "Validation failed.\n")
        self.b1.refresh_from_db()

    def test_update_budget_with_nonexisting_fields(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "budgets", str(self.b1.pk), "--flat_fee_cc", "1500", "--no-confirm", stderr=err
            )
        self.assertEqual(err.getvalue(), "Wrong fields.\n")

        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "budgets", str(self.b1.pk), "--license_fee", "0.20", "--no-confirm", stderr=err
            )
        self.assertEqual(err.getvalue(), "Wrong fields.\n")

    def test_update_credit_amount(self):
        self._call_command("bcm", "update", "credits", str(self.c.pk), "--amount", "1500", "--no-confirm")
        self.c.refresh_from_db()
        self.assertEqual(self.c.amount, 1500)

    def test_update_credit_start_date(self):
        date = TODAY - datetime.timedelta(2)
        self._call_command("bcm", "update", "credits", str(self.c.pk), "--start_date", str(date), "--no-confirm")
        self.c.refresh_from_db()
        self.assertEqual(self.c.start_date, date)

    def test_update_credit_end_date(self):
        date = TODAY + datetime.timedelta(2)
        self._call_command("bcm", "update", "credits", str(self.c.pk), "--end_date", str(date), "--no-confirm")
        self.c.refresh_from_db()
        self.assertEqual(self.c.end_date, date)

    def test_update_credit_license_fee(self):
        msg = io.StringIO()
        self._call_command(
            "bcm", "update", "credits", str(self.c.pk), "--license_fee", "0.3", "--no-confirm", stdout=msg
        )
        self.c.refresh_from_db()
        self.assertEqual(self.c.license_fee, Decimal("0.3"))
        self.assertIn("WARNING: Daily statements", msg.getvalue())

    def test_update_credit_flat_fee(self):
        self._call_command("bcm", "update", "credits", str(self.c.pk), "--flat_fee_cc", "1234", "--no-confirm")
        self.c.refresh_from_db()
        self.assertEqual(self.c.flat_fee_cc, 1234)

    def test_update_credit_with_nonexisting_fields(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "credits", str(self.c.pk), "--freed_cc", "1234", "--no-confirm", stderr=err
            )
        self.c.refresh_from_db()
        self.assertEqual(err.getvalue(), "Wrong fields.\n")

    def test_update_credit_with_too_little_amount(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command("bcm", "update", "credits", str(self.c.pk), "--amount", "50", "--no-confirm", stderr=err)
        self.c.refresh_from_db()
        self.assertEqual(self.c.amount, 1000)
        self.assertEqual(err.getvalue(), "Validation failed.\n")

    def test_update_credit_with_too_large_flat_fee(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "credits", str(self.c.pk), "--flat_fee_cc", "15000000", "--no-confirm", stderr=err
            )
        self.c.refresh_from_db()
        self.assertEqual(err.getvalue(), "Validation failed.\n")

    def test_update_credit_with_too_early_end_date(self):
        err = io.StringIO()
        date = TODAY - datetime.timedelta(100)
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "credits", str(self.c.pk), "--end_date", str(date), "--no-confirm", stderr=err
            )
        self.c.refresh_from_db()
        self.assertEqual(err.getvalue(), "Validation failed.\n")

        err = io.StringIO()
        date = TODAY
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "credits", str(self.c.pk), "--end_date", str(date), "--no-confirm", stderr=err
            )
        self.c.refresh_from_db()
        self.assertEqual(err.getvalue(), "Validation failed.\n")

    def test_update_credit_with_late_start_date(self):
        err = io.StringIO()
        date = TODAY
        with self.assertRaises(SystemExit):
            self._call_command(
                "bcm", "update", "credits", str(self.c.pk), "--start_date", str(date), "--no-confirm", stderr=err
            )
        self.c.refresh_from_db()
        self.assertEqual(err.getvalue(), "Validation failed.\n")

    def test_release_credit(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command("bcm", "release", "credits", str(self.c.pk), "--no-confirm", stderr=err)
        self.assertEqual(err.getvalue(), "Cannot manage credits with action release\n")

    def test_release_active_budget(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit):
            self._call_command("bcm", "release", "budgets", str(self.b1.pk), "--no-confirm", stderr=err)
        self.assertEqual(err.getvalue(), "Could not free assets. Budget status is Active\n")

    def test_transfer_budget(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY + datetime.timedelta(10),
            amount=1000,
            license_fee=Decimal("0.1"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(models.BudgetLineItem.objects.get(pk=self.b1.pk).amount, 200)
        self._call_command(
            "bcm",
            "transfer",
            "budgets",
            str(self.b1.pk),
            "--no-confirm",
            "--transfer-amount",
            100,
            "--transfer-credit",
            c.pk,
        )
        self.assertEqual(models.BudgetLineItem.objects.get(pk=self.b1.pk).amount, 100)
        self.assertEqual(models.BudgetLineItem.objects.get(credit=c).amount, 100)

    def test_release_nonactive_budget(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY - datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal("0.1"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b = create_budget(
            credit=c,
            amount=200,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY - datetime.timedelta(5),
            campaign_id=2,
        )
        self._call_command("bcm", "release", "budgets", str(b.pk), "--no-confirm")

    def test_delete_credit(self):
        self.assertTrue(models.CreditLineItem.objects.filter(pk__in=[self.c.pk]))
        self._call_command("bcm", "delete", "credits", str(self.c.pk), "--no-confirm")
        self.assertFalse(models.CreditLineItem.objects.filter(pk__in=[self.c.pk]))

    def test_delete_budgets(self):
        self.assertEqual(len(self.c.budgets.all()), 2)
        self._call_command("bcm", "delete", "budgets", str(self.b1.pk), str(self.b2.pk), "--no-confirm")
        self.assertEqual(len(self.c.budgets.all()), 0)

    def test_delete_budgets_with_credit_id(self):
        self.assertEqual(len(self.c.budgets.all()), 2)
        self._call_command("bcm", "delete", "budgets", "--credits", str(self.c.pk), "--no-confirm")
        self.assertEqual(len(self.c.budgets.all()), 0)

    def test_budget_constraints(self):
        c = create_credit(
            account_id=2,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY - datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal("0.1"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        b = create_budget(
            credit=c,
            amount=200,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY - datetime.timedelta(5),
            campaign_id=2,
        )

        out = self._call_command("bcm", "list", "budgets", "--credits", str(self.c.pk))
        self.assertIn("#" + str(self.b1.pk), out)
        self.assertIn("#" + str(self.b2.pk), out)
        self.assertNotIn("#" + str(b.pk), out)

        out = self._call_command("bcm", "list", "budgets", "--campaigns", "2")
        self.assertIn("#" + str(self.b1.pk), out)
        self.assertIn("#" + str(self.b2.pk), out)
        self.assertIn("#" + str(b.pk), out)

        with self.assertRaises(SystemExit):
            self._call_command("bcm", "list", "budgets", "--accounts", "1")

        with self.assertRaises(SystemExit):
            self._call_command("bcm", "list", "budgets", "--agencies", "1")

    def test_credit_constraints(self):
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        agency = models.Agency()
        agency.name = "123"
        agency.save(request)

        c = create_credit(
            agency_id=agency.pk,
            start_date=TODAY - datetime.timedelta(10),
            end_date=TODAY - datetime.timedelta(1),
            amount=1000,
            license_fee=Decimal("0.1"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )

        out = self._call_command("bcm", "list", "credits", "--accounts", "2")
        self.assertIn("#" + str(self.c.pk), out)
        self.assertNotIn("#" + str(c.pk), out)

        out = self._call_command("bcm", "list", "credits", "--agencies", str(agency.pk))
        self.assertNotIn("#" + str(self.c.pk), out)
        self.assertIn("#" + str(c.pk), out)

        with self.assertRaises(SystemExit):
            self._call_command("bcm", "list", "credits", "--campaigns", "1")

        with self.assertRaises(SystemExit):
            self._call_command("bcm", "list", "credits", "--credits", "1")
