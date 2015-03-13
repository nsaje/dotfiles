import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from actionlog import sync
from utils.command_helpers import parse_id_list, get_ad_group_sources

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids', help='Comma separated list of group ids. Default is all ad groups.'),
        make_option('--source_ids', help='Comma separated list of source ids. Default is all sources.'),
    )

    def handle(self, *args, **options):
        ad_group_ids = parse_id_list(options, 'ad_group_ids')
        source_ids = parse_id_list(options, 'source_ids')

        logger.info('Fetching status and reports for all ad groups.')

        ad_group_sources = get_ad_group_sources(ad_group_ids, source_ids)
        if ad_group_sources:
            for ad_group_source in ad_group_sources:
                sync.AdGroupSourceSync(ad_group_source).trigger_all()
        else:
            sync.GlobalSync().trigger_all()
