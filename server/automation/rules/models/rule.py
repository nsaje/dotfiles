from django.conf import settings
from django.db import models

import core.models

from .. import constants


class Rule(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    ad_groups_included = models.ManyToManyField(core.models.AdGroup)
    target = models.IntegerField(choices=constants.TargetType.get_choices())
    action_type = models.IntegerField(choices=constants.ActionType.get_choices())
    change_step = models.DecimalField(max_digits=10, decimal_places=4)
    change_limit = models.DecimalField(max_digits=10, decimal_places=4)
    cooldown = models.IntegerField()
    notification_type = models.IntegerField(choices=constants.NotificationType.get_choices())
    notification_recipients = models.TextField(blank=True, null=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.PROTECT
    )
