from django.db.models.signals import pre_save, post_save
from django.contrib.auth import models as authmodels

from utils import signal_handlers

import dash.models


def add_account_to_groups(sender, instance, created, **kwargs):
    if instance.pk is None or not created:
        return

    perm = authmodels.Permission.objects.get(codename='group_account_automatically_add')
    groups = authmodels.Group.objects.filter(permissions=perm)
    existing_groups = instance.groups.all()
    instance.groups = list(set(existing_groups or [] + [x.pk for x in groups]))

post_save.connect(add_account_to_groups, sender=dash.models.Account)

pre_save.connect(signal_handlers.modified_by_pre_save_signal_handler, sender=dash.models.Account)
pre_save.connect(signal_handlers.modified_by_pre_save_signal_handler, sender=dash.models.Campaign)
pre_save.connect(signal_handlers.modified_by_pre_save_signal_handler, sender=dash.models.AdGroup)
pre_save.connect(signal_handlers.created_by_pre_save_signal_handler, sender=dash.models.AdGroupSettings)
pre_save.connect(signal_handlers.created_by_pre_save_signal_handler, sender=dash.models.CampaignSettings)
pre_save.connect(signal_handlers.created_by_pre_save_signal_handler, sender=dash.models.AdGroupSourceSettings)
