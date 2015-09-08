import logging

from django.core.management.base import BaseCommand
from optparse import make_option

from convapi import process
import reports.update
from utils import redirector_helper
from utils.command_helpers import parse_date

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--date', help='Iso format.'),
    )

    def handle(self, *args, **options):
        date = parse_date(options, 'date')

        redirects_impressions = redirector_helper.fetch_redirects_impressions(date)
        touchpoint_conversion_pairs = process.process_touchpoint_conversions(redirects_impressions)
        reports.update.update_touchpoint_conversions(date, touchpoint_conversion_pairs)
