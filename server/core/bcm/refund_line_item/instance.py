from django.db import transaction
from django.forms.models import model_to_dict

import core.bcm


class RefundLineItemInstanceMixin:

    @transaction.atomic
    def update(self, request, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save(request)

    def save(self, request, *args, **kwargs):
        super().save(*args, **kwargs)
        core.bcm.RefundHistory.objects.create(
            created_by=request.user if request else None,
            snapshot=model_to_dict(self),
            refund=self
        )
