import datetime
from decimal import Decimal

from django.conf import settings

import utils.command_helpers
import utils.email_helper
import analytics.monitor
import analytics.statements
import analytics.users
import analytics.delivery
import utils.csv_utils
import dash.models

RECIPIANTS = (
    'operations@zemanta.com',
    'prodops@zemanta.com',
)

VALID_PACING_ACCOUNT_TYPES = (
    dash.constants.AccountType.ACTIVATED,
    dash.constants.AccountType.MANAGED,
    dash.constants.AccountType.PILOT,
)


class Command(utils.command_helpers.ExceptionCommand):
    help = "Daily audits"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')
        parser.add_argument('--send-emails', dest='send_emails', action='store_true',
                            help='Send emails')

        parser.add_argument('--date', '-d', dest='date',
                            help='Date checked (default yesterday)')
        parser.add_argument('--min-pacing', dest='max_pacing', default=Decimal('50.0'),
                            help='Threshold for alarm (default 0.8)')
        parser.add_argument('--min-ad-group-spend', dest='min_ag_spend', default=Decimal('10.0'),
                            help='Threshold for alarm (default 0.8)')
        parser.add_argument('--max-pacing', dest='min_pacing', default=Decimal('200.0'),
                            help='Threshold for alarm on first of month (default 0.6)')
        parser.add_argument('--days-running', dest='days_running', default=7,
                            help='Minimal number of days that ad groups have to be running')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.send_emails = options['send_emails']
        self.alarms = False
        self.email_body = ''

        self.delivery(options)
        self.wau(options)
        self.audit_autopilot(options)
        self.audit_activated_running_ad_groups(options)
        self.audit_pilot_managed_running_ad_groups(options)
        self.audit_account_credits(options)
        self.audit_click_discrepancy(options)

        if self.alarms and self.send_emails:
            email = utils.email_helper.EmailMultiAlternatives(
                'Daily audit v2',
                self.email_body,
                'Zemanta <{}>'.format(
                    settings.FROM_EMAIL
                ), RECIPIANTS)
            email.attach_alternative(
                utils.email_helper.format_template('Daily audit', self.email_body),
                "text/html"
            )
            email.send()

    def delivery(self, options):
        reports = analytics.delivery.generate_delivery_reports()
        out = [
            'Delivery report',
            ' - campaign level: {}'.format(reports['campaign']),
            ' - ad group level: {}'.format(reports['ad_group']),
        ]
        for line in out:
            self._print(line)
            self.email_body += line + '\n'
        self._print('\n')

    def wau(self, options):
        url = analytics.statements.generate_csv(
            'wau/{}-api.csv'.format(str(datetime.date.today())),
            utils.csv_utils.tuplelist_to_csv(analytics.users.get_wau_api_report())
        )
        lines = ['WAU', ' - API user report: ' + url]
        for line in lines:
            self._print(line)
            self.email_body += line + '\n'

        self.email_body += '\n'

    def audit_click_discrepancy(self, options):
        alarms = analytics.monitor.audit_click_discrepancy()
        if not alarms:
            return
        self.alarms = True
        title = 'Campaigns with increased click discrepancy:'
        self._print(title)
        self.email_body += title + '\n'
        for campaign, base, new in alarms:
            text = ' - {} ({}% -> {}%): {}'.format(
                campaign.get_long_name(),
                base,
                new,
                'https://one.zemanta.com/v2/analytics/campaign/{}'.format(campaign.pk)
            )
            self._print(text)
            self.email_body += text + '\n'
        self.email_body += '\n'

    def audit_account_credits(self, options):
        alarms = analytics.monitor.audit_account_credits()
        if not alarms:
            return
        self.alarms = True
        title = 'Accounts with depleting credits:'
        self._print(title)
        self.email_body += title + '\n'
        for account in alarms:
            self._print('- {} {}'.format(account.name, account.pk))
            self.email_body += u' - {} {}\n'.format(
                account.get_long_name(),
                'https://one.zemanta.com/v2/credit/account/{}'.format(account.pk),
            )
        self.email_body += '\n'

    def audit_activated_running_ad_groups(self, options):
        alarms = analytics.monitor.audit_running_ad_groups(
            options['min_ag_spend'],
            (dash.constants.AccountType.ACTIVATED, )
        )
        if not alarms:
            return
        self.alarms = True
        title = 'Running activated ad groups with spend below ${}:'.format(options['min_ag_spend'])
        self._print(title)
        self.email_body += title + '\n'
        for ad_group in alarms:
            self._print(u'- {} {}'.format(ad_group.name, ad_group.pk))
            self.email_body += u' - {} {}\n'.format(
                ad_group.name,
                u'https://one.zemanta.com/v2/analytics/adgroup/{}'.format(ad_group.pk)
            )
        self.email_body += '\n'

    def audit_pilot_managed_running_ad_groups(self, options):
        alarms = analytics.monitor.audit_running_ad_groups(
            options['min_ag_spend'],
            (dash.constants.AccountType.MANAGED,
             dash.constants.AccountType.PILOT,)
        )
        if not alarms:
            return
        self.alarms = True
        title = 'Running pilot or managed ad groups with spend below ${}:'.format(
            options['min_ag_spend']
        )
        self._print(title)
        self.email_body += title + '\n'
        for ad_group in alarms:
            self._print(u'- {} {}'.format(ad_group.name, ad_group.pk))
            self.email_body += u' - {} {}\n'.format(
                ad_group.name,
                u'https://one.zemanta.com/v2/analytics/adgroup/{}'.format(ad_group.pk)
            )
        self.email_body += '\n'

    def audit_autopilot(self, options):
        ap_alarms = analytics.monitor.audit_autopilot_ad_groups()
        if not ap_alarms:
            return
        self.alarms = True
        self._print('Autopilot did not run on the following ad groups:')
        self.email_body += u'Autopilot did not run on the following ad groups:\n'

        for ad_group in ap_alarms:
            self._print(u'- {} {}'.format(ad_group.name, ad_group.pk))
            self.email_body += u' - {} {}\n'.format(
                ad_group.name,
                u'https://one.zemanta.com/v2/analytics/adgroup/{}'.format(ad_group.pk)
            )
        self.email_body += '\n'
