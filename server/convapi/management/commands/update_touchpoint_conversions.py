import datetime
import logging

from django.core.management.base import BaseCommand
from optparse import make_option

from convapi import process
from dash import models
from utils.command_helpers import parse_date, parse_id_list, ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    option_list = BaseCommand.option_list + (
        make_option('--from_date', help='Iso format.'),
        make_option('--to_date', help='Iso format.'),
        make_option('--account_ids', help='Comma separated list of account id. Default is all non archived accounts.'),
    )

    def handle(self, *args, **options):
        from_date = parse_date(options, 'from_date')
        to_date = parse_date(options, 'to_date')
        account_ids = parse_id_list(options, 'account_ids')

        if not from_date:
            from_date = datetime.date.today()

        if not to_date:
            to_date = datetime.date.today()

        conversion_pixels = models.ConversionPixel.objects.filter(archived=False)
        if account_ids is not None:
            conversion_pixels = conversion_pixels.filter(account_id__in=account_ids)

        pairs = []
        while from_date <= to_date:
            pairs.append((from_date, conversion_pixels))
            from_date = from_date + datetime.timedelta(days=1)

        process.update_touchpoint_conversions(pairs)
