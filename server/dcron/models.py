from django.conf import settings
from django.db import models

from dcron import constants


class DCronJob(models.Model):
    """
    Distributed cron job execution details.
    """

    command_name = models.CharField(max_length=150, unique=True)
    executed_dt = models.DateTimeField(null=True, blank=True)
    completed_dt = models.DateTimeField(null=True, blank=True)
    host = models.CharField(max_length=100, null=True, blank=True)
    alert = models.IntegerField(choices=constants.Alert.get_choices(), default=constants.Alert.OK)

    def __str__(self):
        return self.command_name

    class Meta:
        verbose_name = "Distributed Cron Job"
        verbose_name_plural = "Distributed Cron Jobs"


class DCronJobSettings(models.Model):
    """
    Distributed cron job settings metadata used for alerting.
    """

    job = models.OneToOneField(DCronJob, on_delete=models.CASCADE)
    schedule = models.CharField(max_length=250)
    full_command = models.CharField(max_length=250)
    enabled = models.BooleanField(default=True)
    severity = models.IntegerField(choices=constants.Severity.get_choices(), default=constants.Severity.LOW)
    warning_wait = models.FloatField(default=settings.DCRON["default_warning_wait"])
    max_duration = models.FloatField(default=settings.DCRON["default_max_duration"])
    min_separation = models.FloatField(default=settings.DCRON["default_min_separation"])
    manual_override = models.BooleanField(default=False)
    pause_execution = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Distributed Cron Job Settings"
        verbose_name_plural = "Distributed Cron Job Settings"

    def __str__(self):
        return self.job.command_name
