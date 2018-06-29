from django.db import transaction
from django.forms.models import model_to_dict

import core.bcm

import calendar


class RefundLineItemInstanceMixin:

    @transaction.atomic
    def update(self, request, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._update_end_date(kwargs)
        self.clean_save(request)

    def clean_save(self, request=None, *args, **kwargs):
        self.full_clean()
        self.save(request, *args, **kwargs)

    @transaction.atomic
    def save(self, request=None, *args, **kwargs):
        super().save(*args, **kwargs)
        core.bcm.RefundHistory.objects.create(
            created_by=request.user if request else None,
            snapshot=model_to_dict(self),
            refund=self,
        )

    def delete(self):
        setattr(self, 'amount', 0)
        self.full_clean()
        super().delete()

    def _update_end_date(self, kwargs):
        start_date = kwargs.get('start_date')
        if start_date:
            self.end_date = start_date.replace(
                day=calendar.monthrange(start_date.year, start_date.month)[1],
            )
