import datetime
from decimal import Decimal

from django.conf import settings

import utils.command_helpers
import utils.email_helper
import analytics.monitor
import dash.models


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit credits"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')
        parser.add_argument('--send-emails', dest='send_emails', action='store_true',
                            help='Send emails')

        parser.add_argument('--date', '-d', dest='date',
                            help='Date checked (default today)')
        parser.add_argument('--days', '-n', dest='days',
                            help='Days in the future to check')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        alarms = analytics.monitor.audit_account_credits(
            date=options['date'],
            days=options['days'] and int(options['days'])
        )
        sales = {}
        for account in alarms:
            account_settings = account.get_current_settings()
            if not account_settings.default_sales_representative:
                continue
            sales.setdefault(
                account_settings.default_sales_representative,
                []
            ).append(account)

        if not options['send_emails']:
            return
        for sales_user, accounts in sales.iteritems():
            self._print('{}: {}'.format(sales_user, ', '.join(a.name for a in accounts)))
            utils.email_helper.send_depleting_credits_email(sales_user, accounts)
