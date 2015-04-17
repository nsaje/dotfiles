import datetime
import logging

from django.core.management.base import BaseCommand

import dash.constants
import dash.models

from utils import statsd_helper

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Pushing content ad metrics.')

        try:
            cas = dash.models.CotentAdSource.objects.filter(
                submission_state=dash.constants.ContentAdSubmissionStatus.PENDING
            ).earliest('modified_dt')
            hours_since = int((datetime.utcnow() - cas.modified_dt).total_seconds() / 3600)
            statsd_helper.statsd_gauge('dash.oldest_pending_content_ad_source', hours_since)
        except dash.models.ContentAdSource.DoesNotExist:
            statsd_helper.statsd_gauge('dash.oldest_pending_content_ad_source', 0)
