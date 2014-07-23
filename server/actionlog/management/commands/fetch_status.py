import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from utils.command_helpers import parse_ad_group_ids, get_ad_groups

from actionlog import sync

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids', help='Comma separated list of group ids. Default is all groups.'),
    )

    def handle(self, *args, **options):
        ad_group_ids = parse_ad_group_ids(options)

        logger.info('Fetching status for ad_groups: %s', ad_group_ids or 'all')

        ad_groups = get_ad_groups(ad_group_ids)
        for ad_group in ad_groups:
            sync.AdGroupSync(ad_group).trigger_status()
