"""
Script for processing or reprocessing reports

WARNING: This will delete records in the DB tables
"""
import logging

from django.core.management.base import BaseCommand
from optparse import make_option

from convapi import fetch
from reports import update
from utils.command_helpers import parse_date

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--date', help='Iso format.')
    )

    def handle(self, *args, **options):
        date = parse_date(options, 'date')

        conversion_touchpoint_pairs = fetch.fetch_touchpoints_impressions(date)
        update.update_touchpoint_conversions(conversion_touchpoint_pairs)
