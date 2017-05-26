from django.db.models.signals import post_save
from django.contrib.auth import models as authmodels

import dash.models


def add_account_to_groups(sender, instance, created, **kwargs):
    if instance.pk is None or not created:
        return

    perm = authmodels.Permission.objects.get(codename='group_account_automatically_add')
    groups = authmodels.Group.objects.filter(permissions=perm)
    existing_groups = instance.groups.all()
    instance.groups = list(set(existing_groups or [] + [x.pk for x in groups]))


post_save.connect(add_account_to_groups, sender=dash.models.Account)
