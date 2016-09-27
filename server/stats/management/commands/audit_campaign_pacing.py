import datetime
from decimal import Decimal

from django.conf import settings

import utils.command_helpers
import utils.slack
import utils.email_helper
import analytics.monitor
import dash.models
import dash.constants

VALID_ACCOUNT_TYPES = (
    dash.constants.AccountType.SELF_MANAGED,
    dash.constants.AccountType.MANAGED,
    dash.constants.AccountType.PILOT,
)

RECIPIANTS = (
    'operations@zemanta.com',
    'prodops@zemanta.com',
)


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit spend pattern"

    def add_arguments(self, parser):
        parser.add_argument('--date', '-d', dest='date',
                            help='Date checked (default yesterday)')
        parser.add_argument('--min-pacing', dest='max_pacing', default=Decimal('50.0'),
                            help='Threshold for alarm (default 0.8)')
        parser.add_argument('--max-pacing', dest='min_pacing', default=Decimal('200.0'),
                            help='Threshold for alarm on first of month (default 0.6)')
        parser.add_argument('--days-running', dest='days_running', default=7,
                            help='Minimal number of days that ad groups have to be running')
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')
        parser.add_argument('--send-emails', dest='send_emails', action='store_true',
                            help='Send emails')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write('{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
        if options['date']:
            date = datetime.datetime.strptime(options['date'], "%Y-%m-%d").date()

        days_running = int(options['days_running'])
        flying_ad_groups = [
            ad_group for ad_group in
            dash.models.AdGroup.objects.all().filter_running().exclude_archived()
            if (date - ad_group.get_current_settings().start_date).days >= days_running
        ]
        flying_campaigns = {
            c.pk: c
            for c in dash.models.Campaign.objects.filter(
                id__in=set(adg.campaign_id for adg in flying_ad_groups)
            ).exclude_landing().select_related('account')
            if c.account.get_current_settings().account_type in VALID_ACCOUNT_TYPES
        }

        alarms = analytics.monitor.audit_pacing(
            date,
            campaign__in=flying_campaigns.values(),
        )

        if not alarms:
            self._print('OK')
            return

        self._print('FAIL')
        email_body = ''
        for campaign_id, pacing, reason in alarms:
            text = ' - Campaign {} is {}pacing ({}%): {}'.format(
                flying_campaigns[campaign_id].name,
                'over' if reason == 'high' else 'under',
                pacing,
                'https://one.zemanta.com/campaigns/{}/ad_groups?page=1'.format(campaign_id)
            )
            self._print(text)
            email_body += text + '\n'
        if options['send_emails']:
            email = utils.email_helper.EmailMessage(
                'Campaign pacing',
                email_body,
                'Zemanta <{}>'.format(
                    settings.FROM_EMAIL
                ), RECIPIANTS)
            email.send()
