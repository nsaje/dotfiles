import datetime
import typing
import urllib.parse

import croniter
from django.conf import settings
from django.urls import reverse

from dcron import constants
from dcron import models
from utils import dates_helper
from utils import pagerduty_helper
from utils import slack
from utils import zlogging

logger = zlogging.getLogger(__name__)

SLACK_USERNAME = "Dcron Alert"
SLACK_COLOR_OK = "good"
SLACK_COLOR_WARNING = "warning"
SLACK_COLOR_DANGER = "danger"
SLACK_CHANNEL_Z1_LOW_SEVERITY = slack.CHANNEL_RND_Z1_ALERTS_AUX
SLACK_CHANNEL_Z1_HIGH_SEVERITY = slack.CHANNEL_RND_Z1_ALERTS
SLACK_CHANNEL_PRODOPS_LOW_SEVERITY = slack.CHANNEL_ALERTS_RND_PRODOPS
SLACK_CHANNEL_PRODOPS_HIGH_SEVERITY = slack.CHANNEL_ALERTS_RND_PRODOPS


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
            handle_slack_alert(dcron_job, alert)


def update_alert_and_notify(command_name: str, alert: AlertId) -> None:
    """
    Update alert status and notify via PagerDuty and Slack if necessary.
    :param command_name: cron management command name
    :param alert: alert id from dcron.constants.Alert
    """

    dcron_job = models.DCronJob.objects.filter(command_name=command_name).first()
    if dcron_job:
        if dcron_job.alert != alert:
            models.DCronJob.objects.filter(command_name=command_name).update(alert=alert)
            handle_pagerduty_alert(dcron_job, alert)
            handle_slack_alert(dcron_job, alert)
    else:
        logger.error("DCronCommand does not exist - could not set Failure alert.", command_name=command_name)


def handle_pagerduty_alert(dcron_job: models.DCronJob, alert: AlertId) -> None:
    """
    Handle pagerduty alert - trigger or resolve pagerduty alert based on alert status.
    :param dcron_job: DCronJob object
    :param alert: alert id from dcron.constants.Alert
    """

    description = _alert_message(dcron_job.command_name, alert)

    if hasattr(dcron_job, "dcronjobsettings"):
        event_severity = _to_pagerduty_severity(dcron_job.dcronjobsettings.severity)
    else:
        event_severity = pagerduty_helper.PagerDutyEventSeverity.WARNING

    if hasattr(dcron_job, "dcronjobsettings"):
        event_type = _to_pagerduty_event_type(dcron_job.dcronjobsettings.ownership)
    else:
        event_type = pagerduty_helper.PagerDutyEventType.Z1

    if event_type == pagerduty_helper.PagerDutyEventType.PRODOPS:
        # disable PD alerts for ProdOps
        return

    if alert != constants.Alert.OK:
        pagerduty_helper.trigger(event_type, dcron_job.command_name, description, event_severity=event_severity)
    else:
        pagerduty_helper.resolve(event_type, dcron_job.command_name, description, event_severity=event_severity)


def handle_slack_alert(dcron_job: models.DCronJob, alert: AlertId) -> None:
    """
    Handle slack alert - send a message based on alert status.
    :param dcron_job: DCronJob object
    :param alert: alert id from dcron.constants.Alert
    """

    slack_kwargs = _create_slack_publish_params(dcron_job, alert)
    slack.publish("", **slack_kwargs)


def _alert_message(command_name: str, alert: int) -> str:
    alert_type = constants.Alert.get_description(alert)
    return "Cron job alert: {} - {}".format(command_name, alert_type)


def _to_pagerduty_severity(severity: int) -> str:
    if severity is constants.Severity.HIGH:
        return pagerduty_helper.PagerDutyEventSeverity.CRITICAL

    return pagerduty_helper.PagerDutyEventSeverity.WARNING


def _to_pagerduty_event_type(ownership: int) -> str:
    if ownership is constants.Ownership.PRODOPS:
        return pagerduty_helper.PagerDutyEventType.PRODOPS

    return pagerduty_helper.PagerDutyEventType.Z1


def _to_slack_color(alert: AlertId) -> str:
    if alert == constants.Alert.OK:
        return SLACK_COLOR_OK

    if alert == constants.Alert.DURATION:
        return SLACK_COLOR_WARNING

    return SLACK_COLOR_DANGER


def _create_slack_publish_params(dcron_job: models.DCronJob, alert: AlertId) -> dict:
    summary = "There is a problem with a command run by cron"
    fallback_message = _alert_message(dcron_job.command_name, alert)

    # determine message color
    slack_color = _to_slack_color(alert)

    # determine channel name based on severity
    if hasattr(dcron_job, "dcronjobsettings"):
        if dcron_job.dcronjobsettings.severity == constants.Severity.HIGH:
            if dcron_job.dcronjobsettings.ownership == constants.Ownership.PRODOPS:
                channel_name = SLACK_CHANNEL_PRODOPS_HIGH_SEVERITY
            else:
                channel_name = SLACK_CHANNEL_Z1_HIGH_SEVERITY
        else:
            if dcron_job.dcronjobsettings.ownership == constants.Ownership.PRODOPS:
                channel_name = SLACK_CHANNEL_PRODOPS_LOW_SEVERITY
            else:
                channel_name = SLACK_CHANNEL_Z1_LOW_SEVERITY
    else:
        channel_name = SLACK_CHANNEL_Z1_LOW_SEVERITY

    if alert is constants.Alert.OK:
        # in case of OK, override severity and summary
        summary = "The problem with a command run by cron has been resolved"

    log_viewer_link = settings.DCRON.get("log_viewer_link", "{command_name}").format(
        command_name=dcron_job.command_name
    )

    return {
        "channel": channel_name,
        "msg_type": None,
        "username": SLACK_USERNAME,
        "attachments": [
            {
                "title": "[%s] Cron Command Alert" % ("OK" if alert is constants.Alert.OK else "Alerting"),
                "title_link": urllib.parse.urljoin(
                    settings.BASE_URL,
                    reverse(
                        "admin:{}_{}_change".format(dcron_job._meta.app_label, dcron_job._meta.model_name),
                        args=(dcron_job.pk,),
                    ),
                ),
                "color": slack_color,
                "fallback": fallback_message,
                "text": summary,
                "fields": [
                    {"title": dcron_job.command_name, "value": constants.Alert.get_description(alert)},
                    {"title": "Log viewer link", "value": log_viewer_link, "short": False},
                ],
            }
        ],
    }


def _check_alert(dcron_job: models.DCronJob, current_date_time: typing.Optional[datetime.datetime] = None) -> AlertId:
    current_date_time = current_date_time or dates_helper.utc_now()

    if not dcron_job.executed_dt:
        return AlertId(constants.Alert.OK)

    if dcron_job.alert == constants.Alert.FAILURE:
        # Only a successful execution can clear failure.
        return AlertId(constants.Alert.FAILURE)

    if not hasattr(dcron_job, "dcronjobsettings"):
        # Further checks can not be done in this case.
        return AlertId(constants.Alert.OK)

    if not dcron_job.completed_dt:
        # The job is currently running.

        if current_date_time > dcron_job.executed_dt + datetime.timedelta(
            seconds=dcron_job.dcronjobsettings.max_duration
        ):
            # The job has been running for too long.
            return AlertId(constants.Alert.DURATION)

        if dcron_job.alert == constants.Alert.OK:
            # To clear execution alert.
            return AlertId(constants.Alert.OK)

    previous_date_time, next_date_time = _calculate_scheduled_datetimes(
        dcron_job.dcronjobsettings.schedule, date_time=current_date_time
    )

    if next_date_time - current_date_time < settings.DCRON["check_margin"]:
        # The next scheduled iteration is due - don't check this job right now.
        return AlertId(dcron_job.alert)

    if dcron_job.executed_dt > previous_date_time - settings.DCRON["check_margin"]:
        # The job has executed at previous scheduled iteration.
        return AlertId(dcron_job.alert)

    if current_date_time < previous_date_time + datetime.timedelta(seconds=dcron_job.dcronjobsettings.warning_wait):
        # Running a little late, wait for warning wait to expire.
        return AlertId(dcron_job.alert)

    # Running late, alert execution.
    return AlertId(constants.Alert.EXECUTION)


def _calculate_scheduled_datetimes(
    schedule: str, date_time: typing.Optional[datetime.datetime] = None
) -> typing.Tuple[datetime.datetime, datetime.datetime]:
    date_time = date_time or dates_helper.utc_now()
    iterator = croniter.croniter(schedule, date_time)
    previous_date_time = iterator.get_prev(datetime.datetime)
    next_date_time = iterator.get_next(datetime.datetime)
    return previous_date_time, next_date_time
