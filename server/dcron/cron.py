import logging
import typing

from django.conf import settings

import crontab
from dcron import commands
from dcron import exceptions
from dcron import models

logger = logging.getLogger(__name__)


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
        except exceptions.UnregisteredManagementCommand:
            command_name = None
        except exceptions.DCronException as exc:
            logger.error("Failed creating or updating dcron job: %s", exc)
            try:
                command_name = commands.extract_management_command_name(cron_item.command)
            except Exception as exc:
                logger.error("Failed extracting management command name: %s", exc)
                command_name = None

        if command_name:
            removed_command_names.discard(command_name)

    if removed_command_names:
        # There were some commands that were removed.
        logger.warning("Removed commands: %s", ", ".join(sorted(removed_command_names)))
        models.DCronJob.objects.filter(command_name__in=removed_command_names).delete()


def _process_cron_item(cron_item: crontab.CronItem) -> str:
    settings_kwargs = _dcron_job_settings_kwargs(cron_item)

    command_name = commands.extract_and_verify_management_command_name(settings_kwargs["full_command"])

    dcron_job, created = models.DCronJob.objects.get_or_create(command_name=command_name)
    if created:
        logger.info("Created DCronJob for: %s", dcron_job.command_name)

    settings_kwargs["warning_wait"] = settings.DCRON["warning_waits"].get(
        command_name, settings.DCRON["default_warning_wait"]
    )
    settings_kwargs["max_duration"] = settings.DCRON["max_durations"].get(
        command_name, settings.DCRON["default_max_duration"]
    )

    dcron_job_settings = models.DCronJobSettings.objects.filter(job=dcron_job).first()
    if dcron_job_settings:
        # DCronJobSettings already exists.

        if dcron_job_settings.manual_override:
            # Manual override is selected, thus don't update it.
            del settings_kwargs["warning_wait"]
            del settings_kwargs["max_duration"]

        if any(getattr(dcron_job_settings, k) != v for k, v in settings_kwargs.items()):
            # There are changes - update DCronJobSettings.
            models.DCronJobSettings.objects.filter(id=dcron_job_settings.id).update(**settings_kwargs)
            logger.info("Updated DCronJobSettings for: %s", command_name)
        else:
            logger.debug("No need to update DCronJobSettings for: %s", command_name)

    else:
        # DCronJobSettings has to be created.
        models.DCronJobSettings.objects.create(job=dcron_job, **settings_kwargs)
        logger.info("Created DCronJobSettings for: %s", command_name)

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
            logger.error("Invalid crontab entry: %s", cron_item)


def _dcron_job_settings_kwargs(cron_item: crontab.CronItem) -> dict:
    return {
        "schedule": cron_item.slices.clean_render(),
        "full_command": cron_item.command,
        "enabled": cron_item.enabled,
    }
