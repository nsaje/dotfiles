import jsonfield

from django.db import models
from django.conf import settings

from . import constants


class ActionLog(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.CharField(
        max_length=100,
        choices=constants.Action.get_choices()
    )
    action_status = models.IntegerField(
        default=constants.ActionStatus.WAITING,
        choices=constants.ActionStatus.get_choices()
    )
    action_type = models.IntegerField(
        choices=constants.ActionType.get_choices()
    )

    ad_group = models.ForeignKey('dash.AdGroup')
    network = models.ForeignKey('dash.Network')

    payload = jsonfield.JSONField(blank=True, default=[])

    created_datetime = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name='Created at'
    )
    modified_datetime = models.DateTimeField(
        auto_now=True,
        blank=True,
        null=True,
        verbose_name='Modified at'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=True,
        blank=True,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=True,
        blank=True,
    )
