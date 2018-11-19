import datetime
import logging
import typing

from django.conf import settings

import croniter
from dcron import constants
from dcron import models
from utils import dates_helper
from utils import pagerduty_helper

logger = logging.getLogger(__name__)

AlertId = typing.NewType("AlertId", int)


def handle_alerts() -> None:
    """
    Check DCronJob records for alerts and trigger or resolve notifications if necessary.
    """

    # First check if there are any DCronJobs that can not be checked dued to missing DCronJobSettings.
    without_settings = models.DCronJob.objects.filter(dcronjobsettings=None).values_list("command_name", flat=True)
    if without_settings:
        logger.error(
            "Found DCronJobs without settings: %s. Please run sync_dcron_jobs command.", ", ".join(without_settings)
        )

    for dcron_job in models.DCronJob.objects.filter(dcronjobsettings__enabled=True).select_related("dcronjobsettings"):
        alert = _check_alert(dcron_job)

        if dcron_job.alert != alert:
            models.DCronJob.objects.filter(id=dcron_job.id).update(alert=alert)
            handle_pagerduty_alert(dcron_job, alert)


def handle_pagerduty_alert(dcron_job: models.DCronJob, alert: AlertId) -> None:
    """
    Handle pagerduty alert - trigger or resolve pagerduty alert based on alert status.
    :param dcron_job: cron management command name
    :param alert: alert id from dcron.constants.Alert
    """

    description = _alert_message(dcron_job.command_name, alert)
    if hasattr(dcron_job, "dcronjobsettings"):
        event_severity = _convert_severity(dcron_job.dcronjobsettings.severity)
    else:
        event_severity = pagerduty_helper.PagerDutyEventSeverity.WARNING

    if alert != constants.Alert.OK:
        pagerduty_helper.trigger(
            pagerduty_helper.PagerDutyEventType.Z1, dcron_job.command_name, description, event_severity=event_severity
        )
    else:
        pagerduty_helper.resolve(
            pagerduty_helper.PagerDutyEventType.Z1, dcron_job.command_name, description, event_severity=event_severity
        )


def _alert_message(command_name: str, alert: int) -> str:
    alert_type = constants.Alert.get_text(alert)
    return "Cron command alert: {} - {}".format(command_name, alert_type)


def _convert_severity(severity: int) -> str:
    if severity is constants.Severity.HIGH:
        return pagerduty_helper.PagerDutyEventSeverity.CRITICAL

    return pagerduty_helper.PagerDutyEventSeverity.WARNING


def _check_alert(dcron_job: models.DCronJob, current_date_time: typing.Optional[datetime.datetime] = None) -> AlertId:
    current_date_time = current_date_time or dates_helper.utc_now()

    if not dcron_job.executed_dt:
        return AlertId(constants.Alert.OK)

    if not hasattr(dcron_job, "dcronjobsettings"):
        # Further checks can not be done in this case.
        return AlertId(constants.Alert.OK)

    if not dcron_job.completed_dt:
        # The job is currently running.

        if current_date_time > dcron_job.executed_dt + datetime.timedelta(
            seconds=dcron_job.dcronjobsettings.max_duration
        ):
            # The job is running for too long.
            return AlertId(constants.Alert.DURATION)

        return AlertId(constants.Alert.OK)

    previous_date_time, next_date_time = _calculate_scheduled_datetimes(
        dcron_job.dcronjobsettings.schedule, date_time=current_date_time
    )

    if next_date_time - current_date_time < settings.DCRON["check_margin"]:
        # The next scheduled iteration is due - don't check this job right now.
        return AlertId(constants.Alert.OK)

    if dcron_job.executed_dt > previous_date_time - settings.DCRON["check_margin"]:
        # The job has executed at previous scheduled iteration.
        return AlertId(constants.Alert.OK)

    if current_date_time < previous_date_time + datetime.timedelta(seconds=dcron_job.dcronjobsettings.warning_wait):
        # Running a little late, wait for warning wait to expire.
        return AlertId(constants.Alert.OK)

    # Execution of the job is too late.
    return AlertId(constants.Alert.EXECUTION)


def _calculate_scheduled_datetimes(
    schedule: str, date_time: typing.Optional[datetime.datetime] = None
) -> typing.Tuple[datetime.datetime, datetime.datetime]:
    date_time = date_time or dates_helper.utc_now()
    iterator = croniter.croniter(schedule, date_time)
    previous_date_time = iterator.get_prev(datetime.datetime)
    next_date_time = iterator.get_next(datetime.datetime)
    return previous_date_time, next_date_time
