# flake8: noqa
# -*- coding: utf-8 -*-

from django.db import models

from dash import constants

from . import *


class ScheduledExportReportLog(models.Model):
    scheduled_report = models.ForeignKey(ScheduledExportReport)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    report_filename = models.CharField(max_length=1024, blank=False, null=True)
    recipient_emails = models.CharField(max_length=1024, blank=False, null=True)

    state = models.IntegerField(
        default=constants.ScheduledReportSent.FAILED, choices=constants.ScheduledReportSent.get_choices()
    )

    errors = models.TextField(blank=False, null=True)

    def add_error(self, error_msg):
        if self.errors is None:
            self.errors = error_msg
        else:
            self.errors += "\n\n" + error_msg
