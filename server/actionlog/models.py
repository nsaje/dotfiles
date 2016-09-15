import jsonfield

from datetime import datetime, timedelta

from django.db import models
from django.conf import settings

from . import constants

ACTION_TIMEOUT_MINUTES = 30
MAX_SIMILAR_WAITING_ACTIONS = 1


def _due_date_default():
    return datetime.utcnow() + timedelta(minutes=ACTION_TIMEOUT_MINUTES)


class ActionLogOrder(models.Model):
    id = models.AutoField(primary_key=True)

    order_type = models.IntegerField(
        choices=constants.ActionLogOrderType.get_choices()
    )

    created_dt = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name='Created at'
    )


class ActionLog(models.Model):
    id = models.AutoField(primary_key=True)
    action = models.CharField(
        max_length=100,
        choices=constants.Action.get_choices(),
        db_index=True,
    )
    state = models.IntegerField(
        default=constants.ActionState.WAITING,
        choices=constants.ActionState.get_choices(),
        db_index=True,
    )
    action_type = models.IntegerField(
        choices=constants.ActionType.get_choices(),
        db_index=True,
    )

    ad_group_source = models.ForeignKey('dash.AdGroupSource', on_delete=models.PROTECT, null=True)
    content_ad_source = models.ForeignKey('dash.ContentAdSource', on_delete=models.PROTECT, null=True)

    message = models.TextField(blank=True)

    payload = jsonfield.JSONField(blank=True, default={})

    order = models.ForeignKey(
        ActionLogOrder,
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )

    expiration_dt = models.DateTimeField(
        null=True,
        blank=True,
        default=_due_date_default,
    )

    created_dt = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name='Created at',
        db_index=True
    )
    modified_dt = models.DateTimeField(
        auto_now=True,
        blank=True,
        null=True,
        verbose_name='Modified at',
        db_index=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return '{cn}(action={action}, state={state}, ad_group_source={ags}, id={id})'.format(
            cn=self.__class__.__name__,
            action=self.action,
            state=self.state,
            ags=self.ad_group_source,
            id=self.id,
        )

    def save(self, request=None, *args, **kwargs):
        if request is not None:
            self.modified_by = request.user

            if self.pk is None:
                self.created_by = request.user

        super(ActionLog, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created_dt',)

        index_together = [
            ['id', 'created_dt']
        ]

        permissions = (
            ("manual_view", "Can view manual ActionLog actions"),
            ("manual_acknowledge", "Can acknowledge manual ActionLog actions"),
        )
