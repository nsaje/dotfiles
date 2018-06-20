from decimal import Decimal

from django.test import TestCase

import core.bcm
import core.entity

from dash import constants

from . import model

from utils.magic_mixer import magic_mixer
from utils import dates_helper


class TestRefundLineItemManager(TestCase):

    def test_create(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.entity.Account)
        credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=account,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            status=constants.CreditLineItemStatus.SIGNED,
            amount=1000,
            license_fee=Decimal('0.2'),
        )

        refund = model.RefundLineItem.objects.create(
            request,
            account=account,
            credit=credit,
            start_date=dates_helper.local_yesterday(),
            end_date=dates_helper.local_today(),
            amount=100,
            comment='',
        )

        self.assertTrue(refund.id)
        self.assertEqual(request.user, refund.created_by)
