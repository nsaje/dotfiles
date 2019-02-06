import logging
import shlex
import sys

import django_pglocks
import influx
from django.conf import settings
from django.core import management

from dcron import alerts
from dcron import constants
from dcron import exceptions
from dcron import helpers
from dcron import models
from utils import dates_helper

logger = logging.getLogger(__name__)


class DCronCommand(management.base.BaseCommand):
    """
    Base class for management commands scheduled with distributed cron.
    It takes care of advisory locking, updating DCronJob records, sending metrics and logging.
    """

    def handle(self, *args, **options):
        command_name = self._get_command_name()
        start_dt = dates_helper.utc_now()
        host_name = settings.HOSTNAME

        dcron_job = (
            models.DCronJob.objects.filter(command_name=command_name)
            .exclude(dcronjobsettings=None)
            .select_related("dcronjobsettings")
            .first()
        )
        if (
            dcron_job
            and dcron_job.executed_dt
            and dcron_job.completed_dt
            and (start_dt - dcron_job.executed_dt).total_seconds() < dcron_job.dcronjobsettings.min_separation
        ):
            logger.info("Cron job has just completed, not going to run %s on %s", command_name, host_name)
            return

        with django_pglocks.advisory_lock(command_name, wait=False) as acquired:
            if not acquired:
                logger.info("Another process is executing cron job %s - aborting on host %s", command_name, host_name)
                return

            models.DCronJob.objects.update_or_create(
                command_name=command_name, defaults={"executed_dt": start_dt, "completed_dt": None, "host": host_name}
            )

            logger.info("Started cron job %s on host %s", command_name, host_name)

            influx.incr("dcron_command_count", 1, command_name=command_name)

            try:
                self._handle(*args, **options)
            except Exception:
                logger.exception("Exception in DCronCommand %s", command_name)

                dcron_job = models.DCronJob.objects.filter(command_name=command_name).first()
                if dcron_job:
                    if dcron_job.alert != constants.Alert.FAILURE:
                        models.DCronJob.objects.filter(command_name=command_name).update(alert=constants.Alert.FAILURE)
                        alerts.handle_pagerduty_alert(dcron_job, constants.Alert.FAILURE)
                        alerts.handle_slack_alert(dcron_job, constants.Alert.FAILURE)
                else:
                    logger.error("DCronCommand %s does not exist - could not set Failure alert.", command_name)

            finally:
                finish_dt = dates_helper.utc_now()
                models.DCronJob.objects.update_or_create(
                    command_name=command_name, defaults={"completed_dt": finish_dt}
                )

                logger.info(
                    "Finished cron job %s on host %s in %s seconds",
                    command_name,
                    host_name,
                    (finish_dt - start_dt).total_seconds(),
                )

                influx.timing(
                    "dcron_command_duration", (finish_dt - start_dt).total_seconds(), command_name=command_name
                )

    def _handle(self, *args, **options):
        raise NotImplementedError("Not implemented.")

    def _get_command_name(self):
        return helpers.get_command(sys.argv)


def extract_management_command_name(command: str) -> str:  # typing (for mypy check)
    """
    Extract the name of management command.
    :param command: the command
    :return: the name of management command
    """

    if command is None:
        raise exceptions.ParameterException("Command can not be None")

    input_arguments = shlex.split(command)

    if len(input_arguments) <= 1:
        raise exceptions.ParameterException("Command needs at least two arguments")

    if input_arguments[0] != settings.DCRON["base_command"]:
        raise exceptions.ParameterException("Illegal base command: %s" % input_arguments[0])

    return input_arguments[1]


def extract_and_verify_management_command_name(command: str) -> str:  # typing (for mypy check)
    """
    Extract and verify the name of management command.
    It checks if the management command is registered and that it is and instance of DCronCommand.
    :param command: the command
    :return: the name of management command
    """

    command_name = extract_management_command_name(command)

    if command_name not in management.get_commands():
        raise exceptions.UnregisteredManagementCommand("%s is not a registered management command" % command_name)

    return command_name
