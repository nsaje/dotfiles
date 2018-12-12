# -*- coding: utf-8 -*-
import jsonfield
from django.conf import settings
from django.db import models

from dash import constants
from utils.json_helper import JSONFIELD_DUMP_KWARGS

from .history_query_set import HistoryQuerySet
from .history_query_set_manager import HistoryQuerySetManager


class History(models.Model):
    class Meta:
        app_label = "dash"
        verbose_name = "History"
        verbose_name_plural = "History"

    agency = models.ForeignKey("Agency", related_name="history", on_delete=models.PROTECT, null=True)
    account = models.ForeignKey("Account", related_name="history", on_delete=models.PROTECT, null=True)
    campaign = models.ForeignKey("Campaign", related_name="history", on_delete=models.PROTECT, null=True)
    ad_group = models.ForeignKey("AdGroup", related_name="history", on_delete=models.PROTECT, null=True)

    level = models.PositiveSmallIntegerField(choices=constants.HistoryLevel.get_choices(), null=False, blank=False)
    # action type is user initiated action type
    # non user initiated action type is None
    action_type = models.PositiveSmallIntegerField(
        choices=constants.HistoryActionType.get_choices(), null=True, blank=True
    )

    changes_text = models.TextField(blank=False, null=False)
    changes = jsonfield.JSONField(blank=False, null=False, dump_kwargs=JSONFIELD_DUMP_KWARGS)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    system_user = models.PositiveSmallIntegerField(
        choices=constants.SystemUserType.get_choices(), null=True, blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True, blank=True
    )
    stack_trace = models.TextField(blank=True, null=True)

    objects = HistoryQuerySetManager()

    class QuerySet(HistoryQuerySet):
        pass

    def get_changed_by_text(self):
        if self.created_by is None and self.system_user is not None:
            return constants.SystemUserType.get_text(self.system_user)
        elif self.created_by is None and self.system_user is None or self.created_by.is_service:
            return "System User"
        else:
            return self.created_by.email

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise AssertionError("Updating history object not allowed.")

        super(History, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssertionError("Deleting history object not allowed.")
