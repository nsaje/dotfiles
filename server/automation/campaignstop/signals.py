from django.db.models.signals import post_save

import core.bcm
import core.entity.settings
from core.signals import settings_change

from .service import update_notifier
from . import CampaignStopState


def connect_notify_budgets():
    post_save.connect(_notify_budget_line_item_change, sender=core.bcm.BudgetLineItem)


def disconnect_notify_budgets():
    post_save.disconnect(_notify_budget_line_item_change, sender=core.bcm.BudgetLineItem)


def _handle_budget_line_item_change(sender, instance, **kwargs):
    _notify_budget_line_item_change(sender, instance, **kwargs)
    campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=instance.campaign)
    campaignstop_state.update_pending_budget_updates(True)


def _notify_budget_line_item_change(sender, instance, **kwargs):
    if kwargs.get('raw'):
        # prevents triggering when loading fixtures
        return
    update_notifier.notify_budget_line_item_change(instance.campaign)


def connect_notify_ad_group_settings_change():
    settings_change.connect(
        _notify_ad_group_settings_change, sender=core.entity.settings.AdGroupSettings)


def disconnect_notify_ad_group_settings_change():
    settings_change.disconnect(
        _notify_ad_group_settings_change, sender=core.entity.settings.AdGroupSettings)


def _notify_ad_group_settings_change(sender, **kwargs):
    ad_group_settings = kwargs['instance']
    changes = kwargs['changes']
    update_notifier.notify_ad_group_settings_change(ad_group_settings, changes)


def connect_notify_ad_group_source_settings_change():
    settings_change.connect(
        _notify_ad_group_source_settings_change, sender=core.entity.settings.AdGroupSourceSettings)


def disconnect_notify_ad_group_source_settings_change():
    settings_change.disconnect(
        _notify_ad_group_source_settings_change, sender=core.entity.settings.AdGroupSourceSettings)


def _notify_ad_group_source_settings_change(sender, **kwargs):
    ad_group_source_settings = kwargs['instance']
    changes = kwargs['changes']
    update_notifier.notify_ad_group_source_settings_change(ad_group_source_settings, changes)
