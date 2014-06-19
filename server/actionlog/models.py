import jsonfield

from django.db import models
from django.conf import settings

from . import constants
from dash import models as dash_models


class ActionLog(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.IntegerField(
        choices=constants.Action.get_choices()
    )
    status = models.IntegerField(
        default=constants.ActionStatus.WAITING,
        choices=constants.ActionStatus.get_choices()
    )
    type = models.IntegerField(
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
        related_name='+'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+'
    )
