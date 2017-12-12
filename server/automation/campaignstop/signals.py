from django.db.models.signals import post_save

import core.bcm
from service import update_campaigns_end_date


def disconnect_update_budgets():
    post_save.disconnect(
        _update_budgets_campaign_end_date,
        sender=core.bcm.BudgetLineItem,
    )


def connect_update_budgets():
    post_save.connect(
        _update_budgets_campaign_end_date,
        sender=core.bcm.BudgetLineItem
    )


def _update_budgets_campaign_end_date(sender, instance, **kwargs):
    if kwargs.get('raw'):
        # prevents triggering when loading fixtures
        return
    update_campaigns_end_date([instance.campaign])


connect_update_budgets()
