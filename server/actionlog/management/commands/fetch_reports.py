import datetime
import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from utils.command_helpers import parse_date, parse_id_list, get_ad_group_sources, ExceptionCommand

from actionlog import sync

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids', help='Comma separated list of group ids. Default is all ad groups.'),
        make_option('--source_ids', help='Comma separated list of source ids. Default is all sources.'),
        make_option('--from_date', help='Iso format. The date is inclusive. Default is same as till_date.'),
        make_option('--till_date', help='Iso format. The date is inclusive. Default is yesterday.')
    )

    def handle(self, *args, **options):
        from_date = parse_date(options, 'from_date')
        till_date = parse_date(options, 'till_date')
        ad_group_ids = parse_id_list(options, 'ad_group_ids')
        source_ids = parse_id_list(options, 'source_ids')

        if not till_date:
            till_date = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)

        if not from_date:
            from_date = till_date

        if from_date > till_date:
            logger.info('Unable to fetch reports. from_date should be less than or equal to till_date.')
            return

        dates = [from_date + datetime.timedelta(days=i) for i in range((till_date - from_date).days + 1)]

        logger.info('Fetching report for dates: %s, ad_groups: %s', dates, ad_group_ids or 'all')

        ad_group_sources = get_ad_group_sources(ad_group_ids, source_ids)
        for ad_group_source in ad_group_sources:
            ad_group_source_sync = sync.AdGroupSourceSync(ad_group_source)
            ad_group_source_sync.trigger_reports_for_dates(dates)
