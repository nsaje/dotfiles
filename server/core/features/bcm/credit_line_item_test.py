import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

import core.models
import dash.constants
import zemauth
from utils import test_helper
from utils.magic_mixer import magic_mixer

from .credit_line_item import CreditLineItem
from .refund_line_item.model import RefundLineItem


class TestCreditLineItemManager(TestCase):
    def setUp(self):
        self.user = magic_mixer.blend(zemauth.models.User)
        self.account = magic_mixer.blend(core.models.Account, users=[self.user])

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
        self.account = magic_mixer.blend(core.models.Account, users=[self.request.user])
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
        account = magic_mixer.blend(core.models.Account, users=[request.user])
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
        account = magic_mixer.blend(core.models.Account, users=[self.request.user])
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


class TestCreditLineItemAgency(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()

    def test_update_valid_agency(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.request.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, users=[self.request.user])

        credit = magic_mixer.blend(
            CreditLineItem,
            agency=None,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )
        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.request.user,
            amount=10,
            margin=Decimal("0.2500"),
        )

        self.assertEqual(credit.agency, None)
        self.assertEqual(credit.account, account)

        credit.update(self.request, agency=agency, account=None)

        self.assertEqual(credit.agency, agency)
        self.assertEqual(credit.account, None)

    def test_update_invalid_agency(self):
        agency_one = magic_mixer.blend(core.models.Agency, users=[self.request.user])
        agency_two = magic_mixer.blend(core.models.Agency, users=[self.request.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency_one, users=[self.request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account_one, users=[self.request.user])

        credit = magic_mixer.blend(
            CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )
        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.request.user,
            amount=10,
            margin=Decimal("0.2500"),
        )

        self.assertEqual(credit.agency, None)
        self.assertEqual(credit.account, account_one)

        with self.assertRaises(ValidationError):
            credit.update(self.request, agency=agency_two, account=None)


class TestCreditLineItemAccount(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()

    def test_update_valid_account(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.request.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.request.user])
        account_two = magic_mixer.blend(core.models.Account, agency=agency, users=[self.request.user])

        credit = magic_mixer.blend(
            CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        self.assertEqual(credit.agency, None)
        self.assertEqual(credit.account, account_one)

        credit.update(self.request, agency=None, account=account_two)

        self.assertEqual(credit.agency, None)
        self.assertEqual(credit.account, account_two)

    def test_update_invalid_account(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.request.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.request.user])
        account_two = magic_mixer.blend(core.models.Account, agency=agency, users=[self.request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account_one, users=[self.request.user])

        credit = magic_mixer.blend(
            CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )
        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.request.user,
            amount=10,
            margin=Decimal("0.2500"),
        )

        self.assertEqual(credit.agency, None)
        self.assertEqual(credit.account, account_one)

        with self.assertRaises(ValidationError):
            credit.update(self.request, agency=None, account=account_two)
