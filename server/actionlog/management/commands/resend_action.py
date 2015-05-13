import logging
import actionlog
import datetime

from django.core.management.base import BaseCommand
from utils.command_helpers import parse_id_list
from optparse import make_option

logger = logging.getLogger(__name__)


class Command(BaseCommand):

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
                modified_date = datetime.datetime.utcnow()
                expiration_date = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                action.payload['expiration_dt'] = expiration_date.isoformat()

                action.modified_dt = modified_date
                action.state = actionlog.constants.ActionState.WAITING
                action.expiration_dt = expiration_date
                action.save()

                actionlog.zwei_actions.send_multiple([action])
                count_sent += 1
            if count_sent == 0:
                logger.info("Action log %s doesn't exist" % action_id)
