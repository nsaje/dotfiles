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

    ad_group = models.ForeignKey(dash_models.AdGroup)
    network = models.ForeignKey(dash_models.Network)

    payload = jsonfield.JSONField(blank=True, default=[])

    created_datetime = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True
    )
    modified_datetime = models.DateTimeField(
        auto_now=True,
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Created at'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Modified at'
    )
