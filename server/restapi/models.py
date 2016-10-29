from __future__ import unicode_literals
import jsonfield

from django.db import models
from django.conf import settings

from dash import constants


class ReportJob(models.Model):
    id = models.AutoField(primary_key=True)
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT, null=True)
    status = models.IntegerField(
        default=constants.ReportJobStatus.IN_PROGRESS,
        choices=constants.ReportJobStatus.get_choices()
    )
    query = jsonfield.JSONField()
    result = jsonfield.JSONField(null=True, blank=True)
