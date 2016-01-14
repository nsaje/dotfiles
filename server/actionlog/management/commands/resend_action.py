import logging
import actionlog

from django.core.management.base import BaseCommand
from utils.command_helpers import parse_id_list, ExceptionCommand
from optparse import make_option

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    option_list = BaseCommand.option_list + (
        make_option('--ids', help='Comma separated list of action logs'),
    )

    def handle(self, *args, **options):
        ids = parse_id_list(options, 'ids')

        for action_id in ids:
            actions = actionlog.models.ActionLog.objects.filter(pk=action_id)
            logger.info('Sending action log %s' % action_id)
            count_sent = 0
            for action in actions:
                actionlog.zwei_actions.resend(action)
                count_sent += 1
            if count_sent == 0:
                logger.info("Action log %s doesn't exist" % action_id)
