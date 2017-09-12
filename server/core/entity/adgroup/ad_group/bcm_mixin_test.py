import datetime
import decimal

from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash import constants

import core.entity
import core.bcm


class AdGroupBcmMixin(TestCase):

    def setUp(self):
        self.account = magic_mixer.blend(core.entity.Account)
        self.campaign = magic_mixer.blend(core.entity.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)

    def test_get_todays_fee_and_margin(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        today = datetime.date.today()

        credit = magic_mixer.blend(core.bcm.CreditLineItem,
                                   account=self.account,
                                   start_date=yesterday,
                                   end_date=today,
                                   status=constants.CreditLineItemStatus.SIGNED,
                                   amount=decimal.Decimal('1000.0'),
                                   flat_fee_cc=0,
                                   license_fee=decimal.Decimal('0.2121'))

        magic_mixer.blend(core.bcm.BudgetLineItem,
                          campaign=self.campaign,
                          start_date=yesterday,
                          end_date=today,
                          credit=credit,
                          amount=decimal.Decimal('200'),
                          margin=decimal.Decimal('0.2200'))

        fee, margin = self.ad_group.get_todays_fee_and_margin()

        self.assertEqual(fee, decimal.Decimal('0.2121'))
        self.assertEqual(margin, decimal.Decimal('0.2200'))

    def test_get_todays_fee_and_margin_nothing(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        credit = magic_mixer.blend(core.bcm.CreditLineItem,
                                   account=self.account,
                                   start_date=yesterday,
                                   end_date=yesterday,
                                   status=constants.CreditLineItemStatus.SIGNED,
                                   amount=decimal.Decimal('1000.0'),
                                   flat_fee_cc=0,
                                   license_fee=decimal.Decimal('0.2121'))

        magic_mixer.blend(core.bcm.BudgetLineItem,
                          campaign=self.campaign,
                          start_date=yesterday,
                          end_date=yesterday,
                          credit=credit,
                          amount=decimal.Decimal('200'),
                          margin=decimal.Decimal('0.2200'))

        fee, margin = self.ad_group.get_todays_fee_and_margin()

        self.assertEqual(fee, None)
        self.assertEqual(margin, None)
