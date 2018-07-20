# flake8: noqa
# -*- coding: utf-8 -*-

from django.db import models

from . import *


class ScheduledExportReportRecipient(models.Model):
    scheduled_report = models.ForeignKey(ScheduledExportReport, related_name="recipients")
    email = models.EmailField()

    class Meta:
        unique_together = ("scheduled_report", "email")
