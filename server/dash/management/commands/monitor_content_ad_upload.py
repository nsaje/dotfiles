import datetime
import logging

from django.db.models import Q

from dash import constants
from dash import models
from utils.command_helpers import ExceptionCommand
from utils import dates_helper

import influx

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def add_arguments(self, parser):
        parser.add_argument('--interactive', help='Output the values to stdout', action='store_true')

    def handle(self, *args, **options):

        num_pending = models.ContentAdCandidate.objects.filter(
            Q(image_status=constants.AsyncUploadJobStatus.PENDING_START) |
            Q(url_status=constants.AsyncUploadJobStatus.PENDING_START),
            created_dt__lte=dates_helper.utc_now() - datetime.timedelta(hours=1),
            batch__status=constants.UploadBatchStatus.IN_PROGRESS,
        ).count()

        num_waiting = models.ContentAdCandidate.objects.filter(
            Q(image_status=constants.AsyncUploadJobStatus.WAITING_RESPONSE) |
            Q(url_status=constants.AsyncUploadJobStatus.WAITING_RESPONSE),
            created_dt__lte=dates_helper.utc_now() - datetime.timedelta(hours=1),
            batch__status=constants.UploadBatchStatus.IN_PROGRESS,
        ).count()

        interactive = bool(options.get('interactive', False))

        if interactive:
            print 'Number of candidates pending start: {}'.format(num_pending)
            print 'Number of candidates waiting response: {}'.format(num_waiting)
        else:
            influx.gauge('upload.candidates_num', num_pending, status='pending')
            influx.gauge('upload.candidates_num', num_waiting, status='waiting')
            if num_waiting > 0:
                logger.warning('%s content ad candidates in waiting state.', num_waiting)
