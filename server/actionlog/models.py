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
    state = models.IntegerField(
        default=constants.ActionState.WAITING,
        choices=constants.ActionState.get_choices()
    )
    action_type = models.IntegerField(
        choices=constants.ActionType.get_choices()
    )

    ad_group_network = models.ForeignKey('dash.AdGroupNetwork')

    message = models.TextField(blank=True)

    payload = jsonfield.JSONField(blank=True, default=[])

    created_dt = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name='Created at'
    )
    modified_dt = models.DateTimeField(
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

    def __str__(self):
        return '{cn}(action={action}, action_status={status}, ad_group_network={agn}, id={id})'.format(
            cn=self.__class__.__name__,
            action=self.action,
            status=self.action_status,
            agn=self.ad_group_network,
            id=self.id,
        )
