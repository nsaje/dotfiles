# flake8: noqa
# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.validators import validate_email
from django.db import models

from dash import constants

from . import *


class ScheduledExportReport(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    report = models.ForeignKey(ExportReport, related_name="scheduled_reports")

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", null=False, blank=False, on_delete=models.PROTECT
    )

    state = models.IntegerField(
        default=constants.ScheduledReportState.ACTIVE, choices=constants.ScheduledReportState.get_choices()
    )

    sending_frequency = models.IntegerField(
        default=constants.ScheduledReportSendingFrequency.DAILY,
        choices=constants.ScheduledReportSendingFrequency.get_choices(),
    )

    day_of_week = models.IntegerField(
        default=constants.ScheduledReportDayOfWeek.MONDAY, choices=constants.ScheduledReportDayOfWeek.get_choices()
    )

    time_period = models.IntegerField(
        default=constants.ScheduledReportTimePeriod.YESTERDAY, choices=constants.ScheduledReportTimePeriod.get_choices()
    )

    def __str__(self):
        return " ".join(
            [
                _f
                for _f in (
                    self.name,
                    "(",
                    self.created_by.email,
                    ") - ",
                    constants.ScheduledReportSendingFrequency.get_text(self.sending_frequency),
                    "-",
                    str(self.report),
                )
                if _f
            ]
        )

    def add_recipient_email(self, email_address):
        validate_email(email_address)
        if self.recipients.filter(email=email_address).count() < 1:
            self.recipients.create(email=email_address)

    def remove_recipient_email(self, email_address):
        self.recipients.filter(email__exact=email_address).delete()

    def get_recipients_emails_list(self):
        return [recipient.email for recipient in self.recipients.all()]

    def set_recipient_emails_list(self, email_list):
        self.recipients.all().delete()
        for email in email_list:
            self.add_recipient_email(email)
