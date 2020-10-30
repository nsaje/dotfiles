from django.db.models.signals import post_save

import core.features.bcm

from . import service


def connect_notify_budgets():
    post_save.connect(_handle_budget_line_item_change, sender=core.features.bcm.BudgetLineItem)


def disconnect_notify_budgets():
    post_save.disconnect(_handle_budget_line_item_change, sender=core.features.bcm.BudgetLineItem)


def _handle_budget_line_item_change(sender, instance, **kwargs):
    if instance.campaign.settings.autopilot:
        service.recalculate_budgets_campaign(instance.campaign)
