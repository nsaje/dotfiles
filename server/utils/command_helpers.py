import datetime
import logging
import os
import sys

import dateutil.parser
import newrelic.agent
import structlog
from django.conf import settings
from django.core.management.base import BaseCommand

import dash.models
import swinfra.metrics
from dcron import helpers
from utils import profiler

logger = structlog.get_logger(__name__)


class Z1Command(BaseCommand):
    # execute in BaseCommand calls handle()
    # this is extended here to catch exceptions

    def execute(self, *args, **options):
        if int(options["verbosity"]) > 1:
            root_logger = structlog.get_logger("")
            root_logger.setLevel(structlog.stdlib.DEBUG)

        job_name = helpers.get_command(sys.argv)
        swinfra.metrics.start_push_mode(
            gateway_addr=settings.METRICS_PUSH_GATEWAY,
            push_period_seconds=settings.METRICS_PUSH_PERIOD_SECONDS,
            job=job_name,
        )

        if os.environ.get("PROFILER"):
            profiler.start()
        try:
            application = newrelic.agent.application()
            with newrelic.agent.BackgroundTask(application, name=job_name):
                return super(Z1Command, self).execute(*args, **options)
        except SystemExit as err:
            raise err
        except Exception as err:
            structlog.get_logger(self.__class__.__module__).exception("Uncaught exception in command")
            raise err
        finally:
            swinfra.metrics.flush_push_metrics()
            if profiler.is_running():
                profiler.stop_and_dump(job_name)


def last_n_days(n):
    """
    Returns last n days including today.
    """
    today = datetime.datetime.utcnow().date()
    return [today - datetime.timedelta(days=x) for x in range(n)]


def get_ad_group_sources(ad_group_ids=None, source_ids=None, include_archived=False):
    ad_group_sources = dash.models.AdGroupSource.objects.all()

    if not include_archived:
        archived_ad_group_ids = []
        for ad_group in dash.models.AdGroup.objects.all():
            if ad_group.is_archived():
                archived_ad_group_ids.append(ad_group.id)
        ad_group_sources = ad_group_sources.exclude(ad_group_id__in=archived_ad_group_ids)

    if ad_group_ids is not None:
        ad_group_sources = ad_group_sources.filter(ad_group__in=ad_group_ids)

    if source_ids is not None:
        ad_group_sources = ad_group_sources.filter(source__in=source_ids)

    return ad_group_sources


def parse_id_list(options, field_name):
    if not options[field_name]:
        return

    return [int(aid) for aid in options[field_name].split(",")]


def parse_date(options, field_name="date", default=None):
    if not options[field_name]:
        return default

    return dateutil.parser.parse(options[field_name]).date()


def set_logger_verbosity(logger_, options):
    verbosity = int(options["verbosity"])
    if verbosity == 0:
        logger_.setLevel(logging.CRITICAL)
    elif verbosity == 1:  # default
        logger_.setLevel(structlog.stdlib.INFO)
    elif verbosity == 2:
        logger_.setLevel(structlog.stdlib.DEBUG)
    elif verbosity > 2:
        logger_.setLevel(logging.NOTSET)
