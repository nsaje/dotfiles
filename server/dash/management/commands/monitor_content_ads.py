# flake8: noqa
import datetime

import structlog

import dash.constants
import dash.models
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    def handle(self, *args, **options):
        logger.info("Pushing content ad metrics.")

        try:
            cas = dash.models.ContentAdSource.objects.filter(
                submission_status=dash.constants.ContentAdSubmissionStatus.PENDING
            ).earliest("modified_dt")
            hours_since = int((datetime.datetime.utcnow() - cas.modified_dt).total_seconds() / 3600)
        except dash.models.ContentAdSource.DoesNotExist:
            pass
