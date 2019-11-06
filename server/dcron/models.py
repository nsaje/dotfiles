from django.conf import settings
from django.db import models
from django.db import transaction

from dcron import constants
from utils import zlogging

logger = zlogging.getLogger(__name__)


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


class DCronJobHistory(models.Model):
    _STATUS_CHOICES = [
        (constants.Alert.OK, constants.Alert.get_name(constants.Alert.OK)),
        (constants.Alert.FAILURE, constants.Alert.get_name(constants.Alert.FAILURE)),
    ]

    command_name = models.CharField(max_length=150, db_index=True)
    status = models.IntegerField(choices=_STATUS_CHOICES)
    host = models.CharField(max_length=100)
    executed_dt = models.DateTimeField()
    completed_dt = models.DateTimeField()
    expected_max_duration = models.FloatField()

    def __str__(self):
        return "{}: {} ({} @ {})".format(
            self.command_name, constants.Alert.get_name(self.status), self.host, self.executed_dt
        )

    class Meta:
        verbose_name = "Distributed Cron Job History"
        verbose_name_plural = "Distributed Cron Job History Entries"

    @staticmethod
    def create_history_record(command_name):
        with transaction.atomic():
            try:
                dcron_job = DCronJob.objects.select_for_update().get(command_name=command_name)

                if dcron_job.alert not in (constants.Alert.OK, constants.Alert.FAILURE):
                    logger.error(
                        "DCronJobHistory can not be created due to wrong alert status",
                        command_name=command_name,
                        alert=dcron_job.alert,
                    )
                    return

                expected_max_duration = settings.DCRON["default_max_duration"]
                if hasattr(dcron_job, "dcronjobsettings"):
                    expected_max_duration = dcron_job.dcronjobsettings.max_duration
                else:
                    logger.warning("Using default max duration for DCronJob", command_name=command_name)

                DCronJobHistory.objects.create(
                    command_name=command_name,
                    status=dcron_job.alert,
                    host=dcron_job.host,
                    executed_dt=dcron_job.executed_dt,
                    completed_dt=dcron_job.completed_dt,
                    expected_max_duration=expected_max_duration,
                )

            except DCronJob.DoesNotExist:
                logger.exception("DCronJob does not exist", command_name=command_name)
            except Exception:
                logger.exception("DCronJobHistroy can not be created", command_name=command_name)
