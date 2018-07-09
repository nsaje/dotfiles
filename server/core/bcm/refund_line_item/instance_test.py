import datetime
from decimal import Decimal

from django.test import TestCase

import core.bcm

from dash import constants

from utils.magic_mixer import magic_mixer

from . import model
from . import exceptions


class RefundLineItemInstanceMixinTest(TestCase):

    def test_save_history(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.entity.Account)
        start_date = datetime.date(2018, 7, 8)
        end_date = datetime.date(2018, 9, 10)
        refund_start_date = start_date.replace(day=1)
        refund_end_date = start_date.replace(day=31)
        credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=account,
            start_date=start_date,
            end_date=end_date,
            status=constants.CreditLineItemStatus.SIGNED,
            amount=1000,
            license_fee=Decimal('0.2'),
        )

        refund = model.RefundLineItem.objects.create(
            request,
            account=account,
            credit=credit,
            start_date=refund_start_date,
            amount=0,
            comment='test',
        )
        self.assertEqual(1, core.bcm.RefundHistory.objects.count())

        expected_history = {
            'id': refund.id,
            'account': account.id,
            'credit': credit.id,
            'start_date': str(refund_start_date),
            'end_date': str(refund_end_date),
            'amount': 0,
            'comment': 'test',
            'created_by': request.user.id,
        }
        self.assertEqual(expected_history, core.bcm.RefundHistory.objects.latest('created_dt').snapshot)
        self.assertEqual(
            'Created refund. Refund: #{}. Start Date set to "2018-07-01", End Date set to "2018-07-31",'
            ' Amount set to "$0.00", Comment set to "test"'.format(refund.id),
            account.history.latest('created_dt').changes_text,
        )

        refund = model.RefundLineItem.objects.get(id=refund.id)
        refund.update(request, comment='foo')

        self.assertEqual(2, core.bcm.RefundHistory.objects.count())

        expected_history = {
            'id': refund.id,
            'account': account.id,
            'credit': credit.id,
            'start_date': str(refund_start_date),
            'end_date': str(refund_end_date),
            'amount': 0,
            'comment': 'foo',
            'created_by': request.user.id,
        }
        self.assertEqual(expected_history, core.bcm.RefundHistory.objects.latest('created_dt').snapshot)
        self.assertEqual(
            'Refund: #{}. Comment set from "test" to "foo"'.format(refund.id),
            account.history.latest('created_dt').changes_text,
        )

        with self.assertRaises(exceptions.RefundAmountExceededTotalSpend):
            refund.update(request, amount=1000)
