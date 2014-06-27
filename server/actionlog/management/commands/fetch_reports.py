import logging
import datetime
import dateutil.parser

from optparse import make_option
from django.core.management.base import BaseCommand

from actionlog import api
from dash.models import AdGroup

logger = logging.getLogger(__name__)


def yesterday():
    return datetime.date.today() - datetime.timedelta(days=1)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids', help='Comma separated list of group ids. Default is all groups.'),
        make_option('--date', help='Iso format. Default is yesteday.'),
    )

    def _get_ad_groups(self, ad_group_ids=None):
        if ad_group_ids is None:
            return AdGroup.objects.all()

        ad_groups = AdGroup.objects.filter(id__in=ad_group_ids).all()

        selected_ids = [ag.id for ag in ad_groups]
        if set(selected_ids) != set(ad_group_ids):
            raise Exception('Missing ad groups: {}'.format(set(ad_group_ids) - set(selected_ids)))

        return ad_groups

    def _parse_ad_group_ids(self, options):
        if not options['ad_group_ids']:
            return

        return [int(aid) for aid in options['ad_group_ids'].split(',')]

    def _parse_date(self, options):
        if not options['date']:
            return

        return dateutil.parser.parse(options['date']).date()

    def handle(self, *args, **options):
        date = self._parse_date(options) or yesterday()
        ad_group_ids = self._parse_ad_group_ids(options)

        logger.info('Fetching report for date: %s, ad_groups: %s', date, ad_group_ids or 'all')

        ad_groups = self._get_ad_groups(ad_group_ids)
        for ad_group in ad_groups:
            api.fetch_ad_group_reports(ad_group, date)
