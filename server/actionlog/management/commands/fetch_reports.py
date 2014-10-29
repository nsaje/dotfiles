import datetime
import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from utils.command_helpers import last_n_days, parse_date, parse_ad_group_ids, get_ad_groups

from actionlog import sync

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids', help='Comma separated list of group ids. Default is all groups.'),
        make_option('--from_date', help='Iso format. The date is inclusive.'),
        make_option('--till_date', help='Iso format. The date is inclusive. Default is today.')
    )

    def handle(self, *args, **options):
        from_date = parse_date(options, 'from_date')
        till_date = parse_date(options, 'till_date')
        ad_group_ids = parse_ad_group_ids(options)

        if not from_date:
            logger.info('Unable to fetch reports. from_date not specified.')
            return

        if not till_date:
            till_date = datetime.datetime.utcnow().date()

        if from_date > till_date:
            logger.info('Unable to fetch reports. from_date should be less than or equal to till_date.')
            return

        dates = [from_date + datetime.timedelta(days=i) for i in range((till_date - from_date).days + 1)]

        logger.info('Fetching report for dates: %s, ad_groups: %s', dates, ad_group_ids or 'all')

        ad_groups = get_ad_groups(ad_group_ids)
        for ad_group in ad_groups:
            ad_group_sync = sync.AdGroupSync(ad_group)
            for ad_group_source_sync in ad_group_sync.get_components():
                ad_group_source_sync.trigger_reports_for_dates(dates)
