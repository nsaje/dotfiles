import logging

from django.core.management.base import BaseCommand
from optparse import make_option

from convapi import process
from utils.command_helpers import parse_date

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--date', help='Iso format.'),
    )

    def handle(self, *args, **options):
        date = parse_date(options, 'date')

        process.update_touchpoint_conversions([date])
