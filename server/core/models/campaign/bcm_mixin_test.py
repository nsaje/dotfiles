import datetime
import decimal

from django.test import TestCase

import core.features.bcm
import core.features.goals
import core.models
from dash import constants
from utils.magic_mixer import magic_mixer


class CampaignBcmMixin(TestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account, agency=self.agency)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)

    def test_get_todays_fee_and_margin(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        today = datetime.date.today()

        magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            start_date=yesterday,
            end_date=today,
            status=constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            flat_fee_cc=0,
            license_fee=decimal.Decimal("0.2121"),
        )

        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            start_date=yesterday,
            end_date=today,
            status=constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            flat_fee_cc=0,
            license_fee=decimal.Decimal("0.3333"),
        )

        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=yesterday,
            end_date=today,
            credit=credit,
            amount=decimal.Decimal("200"),
            margin=decimal.Decimal("0.2200"),
        )

        fee, margin = self.campaign.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal("0.3333"))
        self.assertEqual(margin, decimal.Decimal("0.2200"))

    def test_get_todays_fee_and_margin_no_budget(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        today = datetime.date.today()

        magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=self.agency,
            start_date=yesterday,
            end_date=today,
            status=constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            flat_fee_cc=0,
            license_fee=decimal.Decimal("0.2121"),
        )

        fee, margin = self.campaign.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal("0.2121"))
        self.assertEqual(margin, None)

    def test_get_todays_fee_and_margin_agency_credit(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        today = datetime.date.today()

        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=self.agency,
            start_date=yesterday,
            end_date=today,
            status=constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            flat_fee_cc=0,
            license_fee=decimal.Decimal("0.2121"),
        )

        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=yesterday,
            end_date=today,
            credit=credit,
            amount=decimal.Decimal("200"),
            margin=decimal.Decimal("0.2200"),
        )

        fee, margin = self.campaign.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal("0.2121"))
        self.assertEqual(margin, decimal.Decimal("0.2200"))

    def test_get_todays_fee_and_margin_nothing(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            start_date=yesterday,
            end_date=yesterday,
            status=constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal("1000.0"),
            flat_fee_cc=0,
            license_fee=decimal.Decimal("0.2121"),
        )

        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=yesterday,
            end_date=yesterday,
            credit=credit,
            amount=decimal.Decimal("200"),
            margin=decimal.Decimal("0.2200"),
        )

        fee, margin = self.campaign.get_todays_fee_and_margin()

        self.assertEqual(fee, None)
        self.assertEqual(margin, None)
