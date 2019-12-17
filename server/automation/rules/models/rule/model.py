from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

import core.models

from ... import constants
from . import instance
from . import manager


class Rule(instance.RuleInstanceMixin, models.Model):

    objects = manager.RuleManager()

    _update_fields = [
        "name",
        "state",
        "target_type",
        "action_type",
        "change_step",
        "change_limit",
        "cooldown",
        "window",
        "notification_type",
        "notification_recipients",
    ]

    id = models.AutoField(primary_key=True)
    agency = models.ForeignKey(core.models.Agency, on_delete=models.CASCADE)

    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    state = models.IntegerField(default=constants.RuleState.ENABLED, choices=constants.RuleState.get_choices())

    ad_groups_included = models.ManyToManyField(core.models.AdGroup)

    target_type = models.IntegerField(choices=constants.TargetType.get_choices())

    action_type = models.IntegerField(choices=constants.ActionType.get_choices())
    change_step = models.FloatField()
    change_limit = models.FloatField()
    cooldown = models.IntegerField()
    window = models.IntegerField(choices=constants.MetricWindow.get_choices(), default=constants.MetricWindow.LIFETIME)

    notification_type = models.IntegerField(choices=constants.NotificationType.get_choices())
    notification_recipients = ArrayField(models.TextField(), null=True, blank=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.PROTECT
    )

    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.PROTECT
    )
