import sys
import logging
import actionlog

from optparse import make_option
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--state', help='Action state.'),
        make_option('--name', help='Action name filter.'),
        make_option('--limit', help='How many action log entries to return.'),
        make_option('--verbose', help='Write out as much information as possible.'),
    )

    def handle(self, *args, **options):

        try:
            state = int(options['state'])
            name = options['name']
            limit = max(int(options.get('limit', 100)), 1)
            verbose = bool(options.get('verbose', False))
        except:
            logging.exception("Failed parsing command line arguments")
            sys.exit(1)

        actions = actionlog.models.ActionLog.objects.filter(state=state, action=name).order_by('-created_dt')[:limit]
        for action in actions:
            if verbose:
                print('{id}\t{payload}\t{created}'.format(id=action.id, payload=action.payload, created=action.created_dt.isoformat()))
            else:
                print(action.id)
