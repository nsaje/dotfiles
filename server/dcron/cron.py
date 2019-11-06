import typing

import crontab
from django.conf import settings

from dcron import commands
from dcron import constants
from dcron import exceptions
from dcron import models
from utils import zlogging

logger = zlogging.getLogger(__name__)


def process_crontab_items(file_name: typing.Optional[str] = None, file_contents: typing.Optional[str] = None) -> None:
    """
    Processes crontab items read from an input file or a string.
    It updates the DCronJob and DCronJobSettings records in the DB to reflect the crontab items provided on input.
    :param file_name: the name of the file to read
    :param file_contents: the contents of the file
    """

    removed_command_names = set(models.DCronJob.objects.values_list("command_name", flat=True))

    for cron_item in _crontab_items_iterator(file_name=file_name, file_contents=file_contents):
        try:
            command_name = _process_cron_item(cron_item)  # type: typing.Union[str, None]
        except exceptions.UnregisteredManagementCommand as exc:
            command_name = None
            logger.warning(str(exc))
        except exceptions.DCronException:
            logger.exception("Failed creating or updating dcron job")
            try:
                command_name = commands.extract_management_command_name(cron_item.command)
            except Exception:
                logger.exception("Failed extracting management command name")
                command_name = None

        if command_name:
            removed_command_names.discard(command_name)

    if removed_command_names:
        # There were some commands that were removed.
        logger.warning("Removed commands", removed_commands=sorted(removed_command_names))
        models.DCronJob.objects.filter(command_name__in=removed_command_names).delete()


def _process_cron_item(cron_item: crontab.CronItem) -> str:
    settings_kwargs = _dcron_job_settings_kwargs(cron_item)

    command_name = commands.extract_and_verify_management_command_name(settings_kwargs["full_command"])

    dcron_job, created = models.DCronJob.objects.get_or_create(command_name=command_name)
    if created:
        logger.info("Created DCronJob", command=dcron_job.command_name)

    settings_kwargs["severity"] = settings.DCRON["severities"].get(command_name, constants.Severity.LOW)
    settings_kwargs["warning_wait"] = settings.DCRON["warning_waits"].get(
        command_name, settings.DCRON["default_warning_wait"]
    )
    settings_kwargs["max_duration"] = settings.DCRON["max_durations"].get(
        command_name, settings.DCRON["default_max_duration"]
    )
    settings_kwargs["min_separation"] = settings.DCRON["min_separations"].get(
        command_name, settings.DCRON["default_min_separation"]
    )

    dcron_job_settings = models.DCronJobSettings.objects.filter(job=dcron_job).first()
    if dcron_job_settings:
        # DCronJobSettings already exists.

        if dcron_job_settings.manual_override:
            # Manual override is selected, thus don't update it.
            del settings_kwargs["severity"]
            del settings_kwargs["warning_wait"]
            del settings_kwargs["max_duration"]
            del settings_kwargs["min_separation"]

        if any(getattr(dcron_job_settings, k) != v for k, v in settings_kwargs.items()):
            # There are changes - update DCronJobSettings.
            models.DCronJobSettings.objects.filter(id=dcron_job_settings.id).update(**settings_kwargs)
            logger.info("Updated DCronJobSettings", command=command_name)
        else:
            logger.debug("No need to update DCronJobSettings", command=command_name)

    else:
        # DCronJobSettings has to be created.
        models.DCronJobSettings.objects.create(job=dcron_job, **settings_kwargs)
        logger.info("Created DCronJobSettings", command=command_name)

    return command_name


def _crontab_items_iterator(
    file_name: typing.Optional[str] = None, file_contents: typing.Optional[str] = None
) -> typing.Iterator[crontab.CronItem]:
    if not (bool(file_name) ^ bool(file_contents)):
        raise exceptions.ParameterException("Provide either file_name or file_contents parameter")

    cron = crontab.CronTab(tabfile=file_name) if file_name else crontab.CronTab(tab=file_contents)

    for cron_item in cron.crons:
        if cron_item.is_valid():
            yield cron_item

        else:
            logger.error("Invalid crontab entry", cron_item=cron_item)


def _dcron_job_settings_kwargs(cron_item: crontab.CronItem) -> dict:
    return {
        "schedule": cron_item.slices.clean_render(),
        "full_command": cron_item.command,
        "enabled": cron_item.enabled,
    }
