import concurrent.futures
import datetime
import time
from decimal import Decimal

from django.test import TransactionTestCase
from mock import patch

import core.models
import dash.constants
from core.features.bcm.exceptions import BudgetAmountExceededCreditAmount
from utils import dates_helper
from utils.base_test_case import BaseTestCase
from utils.exc import MultipleValidationError
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import exceptions
from .budget_line_item import BudgetLineItem
from .credit_line_item import CreditLineItem

TODAY = datetime.datetime(2015, 12, 1).date()


@patch.object(dates_helper, "local_today", lambda: TODAY)
class TestBudgetLineItemManager(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
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

    def test_create_overlapping_margin(self):
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

    def test_create_overlapping_fees(self):
        data = dict(
            account=self.account,
            start_date=datetime.date(2016, 12, 1),
            end_date=datetime.date(2017, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            service_fee=Decimal("0.20"),
            license_fee=Decimal("0.10"),
        )
        new_credit = magic_mixer.blend(CreditLineItem, **data)

        start_date = datetime.date(2017, 1, 1)
        end_date = datetime.date(2017, 1, 5)
        request = magic_mixer.blend_request_user()
        BudgetLineItem.objects.create(request, self.campaign, new_credit, start_date, end_date, 100, 0, "test")

        data["service_fee"] = Decimal("0.30")
        new_credit = magic_mixer.blend(CreditLineItem, **data)
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, new_credit, start_date - datetime.timedelta(days=1), start_date, 100, 0, "test"
            )

        data["service_fee"] = Decimal("0.20")
        data["license_fee"] = Decimal("0.25")
        new_credit = magic_mixer.blend(CreditLineItem, **data)
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, new_credit, start_date - datetime.timedelta(days=1), start_date, 100, 0, "test"
            )

        data["service_fee"] = Decimal("0.50")
        data["license_fee"] = Decimal("0.50")
        new_credit = magic_mixer.blend(CreditLineItem, **data)
        with self.assertRaises(ValidationError):
            BudgetLineItem.objects.create(
                request, self.campaign, new_credit, start_date - datetime.timedelta(days=1), start_date, 100, 0, "test"
            )

    def test_date_in_the_past(self):
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

    def test_clone_start_date_in_the_past(self):
        request = magic_mixer.blend_request_user()
        start_date = TODAY
        end_date = TODAY + datetime.timedelta(days=100)
        self.credit = magic_mixer.blend(
            CreditLineItem,
            account=self.account,
            start_date=TODAY - datetime.timedelta(days=10),
            end_date=TODAY + datetime.timedelta(days=300),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            license_fee=Decimal("0.10"),
        )
        item = BudgetLineItem.objects.create(
            request, self.campaign, self.credit, start_date, end_date, 100, Decimal("0.15"), "test"
        )

        # move 10 days into the future
        new_today = TODAY + datetime.timedelta(days=10)
        dates_helper.local_today = lambda: new_today

        destination_campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        cloned_item = BudgetLineItem.objects.clone(request, item, destination_campaign)

        self.assertTrue(item.start_date < new_today)
        self.assertEqual(item.start_date, start_date)
        self.assertEqual(item.end_date, end_date)

        self.assertEqual(new_today, cloned_item.start_date)
        self.assertEqual(item.end_date, cloned_item.end_date)

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

    def test_filter_present_and_future(self):
        t0 = datetime.date(2017, 1, 1)
        BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0,
            end_date=t0 + datetime.timedelta(days=1),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        item2 = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 + datetime.timedelta(days=1),
            end_date=t0 + datetime.timedelta(days=3),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        item3 = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 + datetime.timedelta(days=3),
            end_date=t0 + datetime.timedelta(days=5),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = t0 + datetime.timedelta(days=2)
            self.assertEqual(
                list(BudgetLineItem.objects.all().filter_present_and_future().order_by("id")), [item2, item3]
            )


@patch.object(dates_helper, "local_today", lambda: TODAY)
class TestMinimizeAmountEndToday(BaseTestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account, real_time_campaign_stop=True)
        self.credit = magic_mixer.blend(
            CreditLineItem,
            account=self.account,
            start_date=datetime.date(2014, 12, 1),
            end_date=datetime.date(2016, 3, 3),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            license_fee=Decimal("0.10"),
            margin=Decimal("0.10"),
        )

    @patch("automation.campaignstop.calculate_minimum_budget_amount")
    def test_large_budget_ending_in_future(self, mock_min_amount):
        t0 = dates_helper.local_today()
        budget = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 - datetime.timedelta(days=5),
            end_date=t0 + datetime.timedelta(days=5),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        mock_min_amount.return_value = 20.0

        budget.minimize_amount_and_end_today()

        self.assertEqual(budget.amount, 20.0)
        self.assertEqual(budget.end_date, dates_helper.local_today())

    @patch("automation.campaignstop.calculate_minimum_budget_amount")
    def test_large_budget_ending_in_past(self, mock_min_amount):
        t0 = dates_helper.local_today()
        budget = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 - datetime.timedelta(days=5),
            end_date=t0 - datetime.timedelta(days=2),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        mock_min_amount.return_value = 0.0

        budget.minimize_amount_and_end_today()

        self.assertEqual(budget.amount, 100.0)
        self.assertEqual(budget.end_date, dates_helper.local_today() - datetime.timedelta(days=2))

    @patch("automation.campaignstop.calculate_minimum_budget_amount")
    def test_budget_starting_in_future(self, mock_min_amount):
        t0 = dates_helper.local_today()
        budget = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 + datetime.timedelta(days=5),
            end_date=t0 + datetime.timedelta(days=10),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        mock_min_amount.return_value = 0.0

        budget.minimize_amount_and_end_today()

        self.assertEqual(budget.amount, 0.0)
        self.assertEqual(budget.end_date, budget.start_date)

    @patch("automation.campaignstop.calculate_minimum_budget_amount")
    def test_depleted(self, mock_min_amount):
        t0 = dates_helper.local_today()
        original_end_date = t0 + datetime.timedelta(days=5)
        budget = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 - datetime.timedelta(days=5),
            end_date=original_end_date,
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        bds = core.features.bcm.BudgetDailyStatement(
            date=t0,
            budget=budget,
            base_media_spend_nano=100e9,
            base_data_spend_nano=0,
            media_spend_nano=100e9,
            data_spend_nano=0,
            service_fee_nano=0,
            license_fee_nano=0,
            margin_nano=0,
            local_base_media_spend_nano=100e9,
            local_base_data_spend_nano=0,
            local_media_spend_nano=100e9,
            local_data_spend_nano=0,
            local_service_fee_nano=0,
            local_license_fee_nano=0,
            local_margin_nano=0,
        )
        bds.save()
        mock_min_amount.return_value = 0

        budget.minimize_amount_and_end_today()

        self.assertEqual(budget.amount, 100.0)
        self.assertEqual(budget.end_date, original_end_date)

    @patch("automation.campaignstop.calculate_minimum_budget_amount")
    def test_overspend(self, mock_min_amount):
        t0 = dates_helper.local_today()
        budget = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 - datetime.timedelta(days=5),
            end_date=t0 + datetime.timedelta(days=5),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )
        mock_min_amount.return_value = 120.0

        budget.minimize_amount_and_end_today()

        self.assertEqual(budget.amount, 100.0)
        self.assertEqual(budget.end_date, dates_helper.local_today())

    def test_no_realtime_campaignstop(self):
        self.campaign.real_time_campaign_stop = False
        t0 = dates_helper.local_today()
        budget = BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign,
            credit=self.credit,
            start_date=t0 - datetime.timedelta(days=5),
            end_date=t0 + datetime.timedelta(days=5),
            amount=100,
            margin=Decimal("0.15"),
            comment="test",
        )

        budget.minimize_amount_and_end_today()

        self.assertEqual(budget.amount, 100.0)
        self.assertEqual(budget.end_date, dates_helper.local_today())


@patch.object(dates_helper, "local_today", lambda: TODAY)
class TestBudgetLineItemManagerTransactional(TransactionTestCase):
    def test_create_race_condition(self):
        self.account = magic_mixer.blend(core.models.Account)
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

        def sleep_wrapper(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                time.sleep(0.5)

            return wrapper

        def create_budget():
            request = magic_mixer.blend_request_user()
            start_date = datetime.date(2017, 1, 1)
            end_date = datetime.date(2017, 1, 2)
            return BudgetLineItem.objects.create(
                request, self.campaign, self.credit, start_date, end_date, self.credit.amount, Decimal("0.15"), "test"
            )

        BudgetLineItem.objects.all().delete()
        with patch.object(BudgetLineItem, "full_clean", sleep_wrapper(BudgetLineItem.full_clean)):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(create_budget)
                time.sleep(0.1)
                try:
                    create_budget()
                    raise Exception("not raised")
                except MultipleValidationError as e:
                    self.assertIsInstance(e.errors[0], BudgetAmountExceededCreditAmount)
                except Exception as e:
                    raise Exception("incorrect exception raised", e)

                async_budget = future.result()
                self.assertEqual(async_budget.amount, self.credit.amount)
                self.assertEqual(list(BudgetLineItem.objects.all()), [async_budget])
