import calendar

from django.db import transaction
from django.forms.models import model_to_dict

import core.features.bcm
import utils.lc_helper


class RefundLineItemInstanceMixin:
    @transaction.atomic
    def update(self, request, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._update_end_date(kwargs)
        self.clean_save(request)

    def _update_end_date(self, kwargs):
        start_date = kwargs.get("start_date")
        if start_date:
            self.end_date = start_date.replace(day=calendar.monthrange(start_date.year, start_date.month)[1])

    def clean_save(self, request=None, *args, **kwargs):
        self.full_clean()
        self.save(request, *args, **kwargs)

    @transaction.atomic
    def save(self, request=None, *args, **kwargs):
        super().save(*args, **kwargs)
        core.features.bcm.RefundHistory.objects.create(
            created_by=request.user if request else None, snapshot=model_to_dict(self), refund=self
        )
        self._add_to_history(request.user if request else None)

    def calculate_cost_splits(self, exchange_rate):
        total_amount = self.amount * exchange_rate
        media_amount = core.features.bcm.calculations.subtract_fee_and_margin(
            total_amount, license_fee=self.credit.license_fee, margin=self.effective_margin
        )
        license_fee_amount = core.features.bcm.calculations.calculate_fee(media_amount, self.credit.license_fee)
        margin_amount = core.features.bcm.calculations.calculate_margin(
            media_amount + license_fee_amount, self.effective_margin
        )
        return media_amount, license_fee_amount, margin_amount

    def _add_to_history(self, user):
        changes = self.get_model_state_changes(model_to_dict(self))

        if not changes and not self.post_init_newly_created:
            return

        if self.post_init_newly_created:
            changes = model_to_dict(self)

        changes, changes_text = self.construct_changes(
            "Created refund.", "Refund: #{}.".format(self.id) if self.id else None, changes
        )

        self.account.write_history(changes_text, changes=changes, action_type=None, user=user)

    def delete(self):
        setattr(self, "amount", 0)
        self.full_clean()
        super().delete()

    @classmethod
    def get_defaults_dict(cls):
        return {}

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {"start_date": "Start Date", "end_date": "End Date", "amount": "Amount", "comment": "Comment"}
        return NAMES.get(prop_name)

    def get_human_value(self, prop_name, value):
        currency_symbol = core.features.multicurrency.get_currency_symbol(self.account.currency)
        if prop_name == "amount" and value is not None:
            value = utils.lc_helper.format_currency(value, places=2, curr=currency_symbol)
        elif prop_name == "comment":
            value = value or ""
        return value
