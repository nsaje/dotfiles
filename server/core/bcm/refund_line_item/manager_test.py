import datetime
from decimal import Decimal

from django.test import TestCase

import core.bcm
import core.models

from dash import constants

from . import model

from utils.magic_mixer import magic_mixer


class TestRefundLineItemManager(TestCase):
    def test_create(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)

        start_date = datetime.date(2018, 7, 8)
        end_date = datetime.date(2018, 9, 10)
        refund_start_date = start_date.replace(day=1)

        credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=account,
            start_date=start_date,
            end_date=end_date,
            status=constants.CreditLineItemStatus.SIGNED,
            amount=1000,
            license_fee=Decimal("0.2"),
        )

        refund = model.RefundLineItem.objects.create(
            request,
            account=account,
            credit=credit,
            start_date=refund_start_date,
            amount=0,
            comment="test",
            effective_margin=Decimal("0.2"),
        )

        self.assertTrue(refund.id)
        self.assertEqual(request.user, refund.created_by)
