from decimal import Decimal

from django.test import TestCase

import core.bcm

from dash import constants

from utils.magic_mixer import magic_mixer
from utils import dates_helper

from . import model


class RefundLineItemInstanceMixinTest(TestCase):

    def test_save_history(self):
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
        self.assertEqual(1, core.bcm.RefundHistory.objects.count())

        expected_history = {
            'id': refund.id,
            'account': account.id,
            'credit': credit.id,
            'start_date': '2018-06-19',
            'end_date': '2018-06-20',
            'amount': 100,
            'comment': '',
            'created_by': request.user.id,
        }
        self.assertEqual(expected_history, core.bcm.RefundHistory.objects.latest('created_dt').snapshot)

        refund.update(request, amount=200)
        self.assertEqual(2, core.bcm.RefundHistory.objects.count())

        expected_history = {
            'id': refund.id,
            'account': account.id,
            'credit': credit.id,
            'start_date': '2018-06-19',
            'end_date': '2018-06-20',
            'amount': 200,
            'comment': '',
            'created_by': request.user.id,
        }
        self.assertEqual(expected_history, core.bcm.RefundHistory.objects.latest('created_dt').snapshot)
