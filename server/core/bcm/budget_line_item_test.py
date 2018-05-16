from decimal import Decimal
import datetime

from django.test import TestCase
from django.core.exceptions import ValidationError

import zemauth
import dash
from utils.magic_mixer import magic_mixer

from .budget_line_item import BudgetLineItem


class TestBudgetLineItemManager(TestCase):

    def setUp(self):
        self.user = magic_mixer.blend(zemauth.models.User)
        self.account = magic_mixer.blend(dash.models.Account, users=[self.user])
        self.campaign = magic_mixer.blend(dash.models.Campaign, account=self.account)
        self.credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=self.account,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            license_fee=Decimal('0.10'),
        )

    def test_create(self):
        request = magic_mixer.blend_request_user()
        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 2)
        item = BudgetLineItem.objects.create(request, self.campaign, self.credit, start_date, end_date, 100, Decimal('0.15'), 'test')
        self.assertEqual(item.campaign, self.campaign)
        self.assertEqual(item.credit, self.credit)
        self.assertEqual(item.start_date, start_date)
        self.assertEqual(item.end_date, end_date)
        self.assertEqual(item.amount, 100)
        self.assertEqual(item.margin, Decimal('0.15'))
        self.assertEqual(item.comment, 'test')

    def test_create_overlapping_margin_bcm_v2(self):
        self.account.set_uses_bcm_v2(None, True)

        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 5)
        request = magic_mixer.blend_request_user()
        BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date,
            100, Decimal('0.15'), 'test')
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, self.credit, start_date-datetime.timedelta(days=1), start_date,
                100, Decimal('0.20'), 'test')
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, self.credit, end_date, end_date+datetime.timedelta(days=1),
                100, Decimal('0.20'), 'test')
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, self.credit,
                start_date-datetime.timedelta(days=1), end_date+datetime.timedelta(days=1),
                100, Decimal('0.20'), 'test')
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, self.credit,
                start_date+datetime.timedelta(days=1), end_date-datetime.timedelta(days=1),
                100, Decimal('0.20'), 'test')
        BudgetLineItem.objects.create(
            request, self.campaign, self.credit,
            end_date+datetime.timedelta(days=1), end_date+datetime.timedelta(days=2),
            100, Decimal('0.20'), 'test')
        BudgetLineItem.objects.create(
            request, self.campaign, self.credit,
            start_date-datetime.timedelta(days=2), start_date-datetime.timedelta(days=1),
            100, Decimal('0.20'), 'test')

    def test_create_overlapping_license_fee_bcm_v2(self):
        self.account.set_uses_bcm_v2(None, True)
        new_credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=self.account,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            license_fee=Decimal('0.25'),
        )

        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 5)
        request = magic_mixer.blend_request_user()
        BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date,
            100, 0, 'test')
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, new_credit, start_date-datetime.timedelta(days=1), start_date,
                100, 0, 'test')
