import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from utils.command_helpers import yesterday, parse_date, parse_ad_group_ids, get_ad_groups

from actionlog import api

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids', help='Comma separated list of group ids. Default is all groups.'),
        make_option('--date', help='Iso format. Default is yesteday.'),
    )

    def handle(self, *args, **options):
        date = parse_date(options) or yesterday()
        ad_group_ids = parse_ad_group_ids(options)

        logger.info('Fetching report for date: %s, ad_groups: %s', date, ad_group_ids or 'all')

        ad_groups = get_ad_groups(ad_group_ids)
        for ad_group in ad_groups:
            api.fetch_ad_group_reports(ad_group, date)
