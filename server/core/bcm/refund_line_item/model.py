from django.db import models
from django.conf import settings

import core.common
import utils.demo_anonymizer

from . import instance
from . import manager


class RefundLineItem(instance.RefundLineItemInstanceMixin, core.common.FootprintModel):

    class Meta:
        app_label = 'dash'

    _demo_fields = {
        'comment': utils.demo_anonymizer.fake_io,
    }

    account = models.ForeignKey('Account', related_name='refunds', on_delete=models.PROTECT, blank=True, null=True)
    credit = models.ForeignKey('CreditLineItem', related_name='refunds', on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.IntegerField()
    comment = models.TextField(default='Unchecked credit refund')

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', verbose_name='Created by',
                                   on_delete=models.PROTECT, null=True, blank=True)

    objects = manager.RefundLineItemManager()
