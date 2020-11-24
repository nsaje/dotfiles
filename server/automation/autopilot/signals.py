from django.db.models.signals import post_save

import core.features.bcm

from .service import service


def connect_notify_budgets():
    post_save.connect(_handle_budget_line_item_change, sender=core.features.bcm.BudgetLineItem)


def disconnect_notify_budgets():
    post_save.disconnect(_handle_budget_line_item_change, sender=core.features.bcm.BudgetLineItem)


def _handle_budget_line_item_change(sender, instance, **kwargs):
    if instance.campaign.settings.autopilot and instance.campaign.account.agency_uses_realtime_autopilot(
        ad_group=instance
    ):
        service.recalculate_ad_group_budgets(instance.campaign)
