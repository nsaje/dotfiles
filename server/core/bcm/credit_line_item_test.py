import datetime
from decimal import Decimal

# from django.core.exceptions import ValidationError
from django.test import TestCase

import zemauth
import dash
from utils.magic_mixer import magic_mixer
from utils import test_helper

from .credit_line_item import CreditLineItem
from .refund_line_item.model import RefundLineItem


class TestCreditLineItemManager(TestCase):
    def setUp(self):
        self.user = magic_mixer.blend(zemauth.models.User)
        self.account = magic_mixer.blend(dash.models.Account, users=[self.user])

    def test_create(self):
        request = magic_mixer.blend_request_user()
        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 2)
        item = CreditLineItem.objects.create(
            request, start_date, end_date, 100, account=self.account, license_fee=Decimal("0.15")
        )
        self.assertEqual(item.account, self.account)
        self.assertEqual(item.start_date, start_date)
        self.assertEqual(item.end_date, end_date)
        self.assertEqual(item.amount, 100)
        self.assertEqual(item.license_fee, Decimal("0.15"))


class TestCreditLineItemValidateLicenseFee(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.account = magic_mixer.blend(dash.models.Account, users=[self.request.user])
        self.item = self._create_credit(Decimal("0.1"), datetime.date(2017, 1, 1), datetime.date(2017, 1, 31))

    def _create_credit(self, license_fee, start_date, end_date):
        return CreditLineItem.objects.create(
            self.request, start_date, end_date, 100, account=self.account, license_fee=license_fee
        )

    def test_valid_same_license_fee(self):
        self._create_credit(Decimal("0.1"), self.item.start_date, self.item.end_date)

    def test_valid_non_overlapping(self):
        self._create_credit(Decimal("0.2"), datetime.date(2017, 2, 1), datetime.date(2017, 2, 28))

    def test_valid_change_single_item(self):
        self.item.license_fee = Decimal("0.2")
        self.item.save()


class TestCreditLineItemQuerySetFilterOverlapping(TestCase):
    def setUp(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(dash.models.Account, users=[request.user])
        self.item = CreditLineItem.objects.create(
            request,
            datetime.date(2017, 1, 1),
            datetime.date(2017, 1, 31),
            100,
            account=account,
            license_fee=Decimal("0.1"),
        )

    def test_filter_overlapping_contains_start_date(self):
        self.assertEqual(
            [self.item],
            test_helper.QuerySetMatcher(
                CreditLineItem.objects.filter_overlapping(datetime.date(2017, 1, 15), datetime.date(2017, 2, 15))
            ),
        )

    def test_filter_overlapping_contains_end_date(self):
        self.assertEqual(
            [self.item],
            test_helper.QuerySetMatcher(
                CreditLineItem.objects.filter_overlapping(datetime.date(2016, 12, 15), datetime.date(2017, 1, 15))
            ),
        )

    def test_filter_overlapping_contained(self):
        self.assertEqual(
            [self.item],
            test_helper.QuerySetMatcher(
                CreditLineItem.objects.filter_overlapping(datetime.date(2017, 1, 15), datetime.date(2017, 1, 15))
            ),
        )

    def test_filter_overlapping_containing(self):
        self.assertEqual(
            [self.item],
            test_helper.QuerySetMatcher(
                CreditLineItem.objects.filter_overlapping(datetime.date(2016, 12, 15), datetime.date(2017, 2, 15))
            ),
        )

    def test_filter_overlapping_before(self):
        self.assertEqual(
            [],
            test_helper.QuerySetMatcher(
                CreditLineItem.objects.filter_overlapping(datetime.date(2016, 12, 15), datetime.date(2016, 12, 31))
            ),
        )

    def test_filter_overlapping_after(self):
        self.assertEqual(
            [],
            test_helper.QuerySetMatcher(
                CreditLineItem.objects.filter_overlapping(datetime.date(2017, 2, 1), datetime.date(2017, 2, 15))
            ),
        )


class TestCreditLineItemAmounts(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(dash.models.Account, users=[self.request.user])
        self.base_amount = 1000
        self.item = CreditLineItem.objects.create(
            self.request,
            datetime.date(2017, 1, 1),
            datetime.date(2017, 1, 31),
            self.base_amount,
            account=account,
            license_fee=Decimal("0.1"),
        )

    def test_refunds_amount(self):
        self.assertEqual(self.item.get_available_amount(), self.base_amount)
        refund = RefundLineItem.objects.create_unsafe(
            account=self.item.account,
            credit=self.item,
            start_date=datetime.date(2017, 1, 1),
            end_date=datetime.date(2017, 1, 2),
            amount=self.base_amount,
        )
        self.assertEqual(self.item.get_available_amount(), self.base_amount + refund.amount)
