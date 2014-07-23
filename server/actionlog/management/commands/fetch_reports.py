import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from utils.command_helpers import last_n_days, parse_date, parse_ad_group_ids, get_ad_groups

from actionlog import sync

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids', help='Comma separated list of group ids. Default is all groups.'),
        make_option('--date', help='Iso format. Default is last 3 days.'),
    )

    def handle(self, *args, **options):
        selected_date = parse_date(options)
        ad_group_ids = parse_ad_group_ids(options)

        if selected_date:
            dates = [selected_date]
        else:
            dates = last_n_days(3)

        logger.info('Fetching report for dates: %s, ad_groups: %s', dates, ad_group_ids or 'all')

        ad_groups = get_ad_groups(ad_group_ids)
        for ad_group in ad_groups:
            sync.AdGroupSync(ad_group).trigger_reports(dates)
