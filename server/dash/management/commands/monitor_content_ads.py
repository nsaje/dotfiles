import logging

from django.core.management.base import BaseCommand

import dash.constants
import dash.models

from utils import statsd_helper

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Pushing content ad metrics.')

        content_ad_sources_pending_num = dash.models.CotentAdSource.objects.filter(
            submission_state=dash.constants.ContentAdSubmissionStatus.PENDING
        ).count()
        statsd_helper.statsd_gauge('dash.content_ad_sources_pending', content_ad_sources_pending_num)
