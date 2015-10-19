import logging

from django.core.management.base import BaseCommand
from optparse import make_option

from convapi import process
from dash import models
from utils.command_helpers import parse_date, parse_id_list

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--date', help='Iso format.'),
        make_option('--account_ids', help='Comma separated list of account id. Default is all non archived accounts.'),
    )

    def handle(self, *args, **options):
        date = parse_date(options, 'date')
        account_ids = parse_id_list(options, 'account_id')

        if account_ids is not None:
            accounts = models.Account.objects.filter(id__in=account_ids)
        else:
            accounts = [acc for acc in models.Account.objects.all() if not acc.is_archived()]

        process.update_touchpoint_conversions([date], accounts)
