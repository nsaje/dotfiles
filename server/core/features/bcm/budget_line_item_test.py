import datetime
from decimal import Decimal

from django.test import TestCase
from mock import patch

import core.models
import dash.constants
import zemauth
from utils.exc import MultipleValidationError
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer

from . import exceptions
from .budget_line_item import BudgetLineItem
from .credit_line_item import CreditLineItem

TODAY = datetime.datetime(2015, 12, 1).date()


@patch("dash.forms.dates_helper.local_today", lambda: TODAY)
class TestBudgetLineItemManager(TestCase):
    def setUp(self):
        self.user = magic_mixer.blend(zemauth.models.User)
        self.account = magic_mixer.blend(core.models.Account, users=[self.user])
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.credit = magic_mixer.blend(
            CreditLineItem,
            account=self.account,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            license_fee=Decimal("0.10"),
        )

    def test_create(self):
        request = magic_mixer.blend_request_user()
        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 2)
        item = BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date, 100, Decimal("0.15"), "test"
        )
        self.assertEqual(item.campaign, self.campaign)
        self.assertEqual(item.credit, self.credit)
        self.assertEqual(item.start_date, start_date)
        self.assertEqual(item.end_date, end_date)
        self.assertEqual(item.amount, 100)
        self.assertEqual(item.margin, Decimal("0.15"))
        self.assertEqual(item.comment, "test")

    def test_create_overlapping_margin_bcm_v2(self):
        self.account.set_uses_bcm_v2(None, True)

        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 5)
        request = magic_mixer.blend_request_user()
        BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date, 100, Decimal("0.15"), "test"
        )
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request,
                self.campaign,
                self.credit,
                start_date - datetime.timedelta(days=1),
                start_date,
                100,
                Decimal("0.20"),
                "test",
            )
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request,
                self.campaign,
                self.credit,
                end_date,
                end_date + datetime.timedelta(days=1),
                100,
                Decimal("0.20"),
                "test",
            )
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request,
                self.campaign,
                self.credit,
                start_date - datetime.timedelta(days=1),
                end_date + datetime.timedelta(days=1),
                100,
                Decimal("0.20"),
                "test",
            )
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request,
                self.campaign,
                self.credit,
                start_date + datetime.timedelta(days=1),
                end_date - datetime.timedelta(days=1),
                100,
                Decimal("0.20"),
                "test",
            )
        BudgetLineItem.objects.create(
            request,
            self.campaign,
            self.credit,
            end_date + datetime.timedelta(days=1),
            end_date + datetime.timedelta(days=2),
            100,
            Decimal("0.20"),
            "test",
        )
        BudgetLineItem.objects.create(
            request,
            self.campaign,
            self.credit,
            start_date - datetime.timedelta(days=2),
            start_date - datetime.timedelta(days=1),
            100,
            Decimal("0.20"),
            "test",
        )

    def test_create_overlapping_license_fee_bcm_v2(self):
        self.account.set_uses_bcm_v2(None, True)
        new_credit = magic_mixer.blend(
            CreditLineItem,
            account=self.account,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            license_fee=Decimal("0.25"),
        )

        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 5)
        request = magic_mixer.blend_request_user()
        BudgetLineItem.objects.create(request, self.campaign, self.credit, start_date, end_date, 100, 0, "test")
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, new_credit, start_date - datetime.timedelta(days=1), start_date, 100, 0, "test"
            )

    def test_date_in_the_past(self):
        self.account.set_uses_bcm_v2(None, True)
        request = magic_mixer.blend_request_user()

        past_date = TODAY - datetime.timedelta(days=1)

        with self.assertRaises(exceptions.StartDateInThePast):
            BudgetLineItem.objects.create(
                request, self.campaign, self.credit, past_date, TODAY, 100, Decimal("0.20"), "test"
            )

        with self.assertRaises(exceptions.EndDateInThePast):
            BudgetLineItem.objects.create(
                request, self.campaign, self.credit, TODAY, past_date, 100, Decimal("0.20"), "test"
            )

        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 5)
        budget = BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date, 100, Decimal("0.15"), "test"
        )
        budget.start_date = past_date
        with self.assertRaises(ValidationError):
            budget.save()

        budget.end_date = past_date
        with self.assertRaises(ValidationError):
            budget.save()

    def test_clone(self):
        request = magic_mixer.blend_request_user()
        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 2)
        item = BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date, 100, Decimal("0.15"), "test"
        )
        destination_campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        cloned_item = BudgetLineItem.objects.clone(request, item, destination_campaign)

        self.assertEqual(item.campaign, self.campaign)
        self.assertEqual(item.credit, self.credit)
        self.assertEqual(item.start_date, start_date)
        self.assertEqual(item.end_date, end_date)
        self.assertEqual(item.amount, 100)
        self.assertEqual(item.margin, Decimal("0.15"))
        self.assertEqual(item.comment, "test")

        self.assertEqual(destination_campaign, cloned_item.campaign)
        self.assertEqual(item.credit, cloned_item.credit)
        self.assertEqual(item.start_date, cloned_item.start_date)
        self.assertEqual(item.end_date, cloned_item.end_date)
        self.assertEqual(item.amount, cloned_item.amount)
        self.assertEqual(item.margin, cloned_item.margin)
        self.assertEqual(item.comment, cloned_item.comment)

    def test_clone_not_enough_credit(self):
        request = magic_mixer.blend_request_user()
        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 2)
        item = BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date, 251, Decimal("0.15"), "test"
        )
        destination_campaign = magic_mixer.blend(core.models.Campaign, account=self.account)

        try:
            BudgetLineItem.objects.clone(request, item, destination_campaign)
        except MultipleValidationError as err:
            error = err

        self.assertEqual("Budget exceeds the total credit amount by $2.00.", str(error.errors[0]))
