import logging
import sys


from integrations.bizwire.internal import reprocess
from utils import command_helpers

logger = logging.getLogger(__name__)


class Command(command_helpers.ExceptionCommand):
    help = """Start lambdas to process businesswire articles for given parameters.
    Usage: ./manage.py bizwire_process_articles [options]

    Available options:
      --date - date for which to import articles in isoformat
      --key - article s3 key
      --missing - find and reprocess missing articles
    """

    def add_arguments(self, parser):
        parser.add_argument('--key', '-k', dest='key', nargs=1, type=str)
        parser.add_argument('--missing', '-m', dest='missing', action='store_true')
        parser.add_argument('--purge-candidates', '-p', dest='purge_candidates', action='store_true')

    def handle(self, *args, **options):
        self.purge_candidates = options.get('purge_candidates')

        keys = self._get_keys_to_reprocess(options)
        if self.purge_candidates:
            num_removed = reprocess.purge_candidates(keys)
            logger.info('Removed %s candidates.', num_removed)
        reprocess.invoke_lambdas(keys)

    def _get_keys_to_reprocess(self, options):
        if options.get('key'):
            return options['key']

        missing = options.get('missing')
        if missing:
            return reprocess.get_missing_keys()

        logger.info('Specify what to reprocess.')
        sys.exit(1)
