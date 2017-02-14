import datetime
from decimal import Decimal

from django.conf import settings

import utils.command_helpers
import utils.email_helper
import analytics.monitor
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

        self.audit_iab_categories(options)
        self.audit_campaign_pacing(options)
        self.audit_autopilot(options)
        self.audit_activated_running_ad_groups(options)
        self.audit_pilot_managed_running_ad_groups(options)
        self.audit_account_credits(options)

        if self.alarms and self.send_emails:
            email = utils.email_helper.EmailMultiAlternatives(
                'Daily audit',
                self.email_body,
                'Zemanta <{}>'.format(
                    settings.FROM_EMAIL
                ), RECIPIANTS)
            email.attach_alternative(
                utils.email_helper.format_template('Daily audit', self.email_body),
                "text/html"
            )
            email.send()

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
                'https://one.zemanta.com/accounts/{}/credit'.format(account.pk),
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
        title = 'Running activated ad groups with spend bellow ${}:'.format(options['min_ag_spend'])
        self._print(title)
        self.email_body += title + '\n'
        for ad_group in alarms:
            self._print(u'- {} {}'.format(ad_group.name, ad_group.pk))
            self.email_body += u' - {} {}\n'.format(
                ad_group.name,
                u'https://one.zemanta.com/ad_groups/{}/ads'.format(ad_group.pk)
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
        title = 'Running pilot or managed ad groups with spend bellow ${}:'.format(
            options['min_ag_spend']
        )
        self._print(title)
        self.email_body += title + '\n'
        for ad_group in alarms:
            self._print(u'- {} {}'.format(ad_group.name, ad_group.pk))
            self.email_body += u' - {} {}\n'.format(
                ad_group.name,
                u'https://one.zemanta.com/ad_groups/{}/ads'.format(ad_group.pk)
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
                u'https://one.zemanta.com/ad_groups/{}/ads'.format(ad_group.pk)
            )
        self.email_body += '\n'

    def audit_iab_categories(self, options):
        undefined_iab_running_campaigns = analytics.monitor.audit_iab_categories(running_only=True)
        if undefined_iab_running_campaigns:
            self.alarms = True
            self.email_body += u'Active campaigns with undefined IAB categories:\n'
            self._print(u'Active campaigns with undefined IAB categories: ')

        for campaign in undefined_iab_running_campaigns:
            text = u' - {}: {}'.format(
                campaign.get_long_name(),
                u'https://one.zemanta.com/campaigns/{}/ad_groups?page=1'.format(campaign.pk)
            )
            self._print(text)
            self.email_body += text + u'\n'
        self.email_body += '\n'

    def audit_campaign_pacing(self, options):
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
            if c.account.get_current_settings().account_type in VALID_PACING_ACCOUNT_TYPES
        }

        alarms = analytics.monitor.audit_pacing(
            date,
            campaign__in=flying_campaigns.values(),
        )

        if not alarms:
            self._print('Pacing OK')
            return

        self.alarms = True
        self._print('Pacing FAIL')
        overpaced = [
            (flying_campaigns[campaign_id], pacing)
            for campaign_id, pacing, reason in alarms
            if reason == 'high'
        ]

        underpaced = [
            (flying_campaigns[campaign_id], pacing)
            for campaign_id, pacing, reason in alarms
            if reason == 'low'
        ]

        self.email_body += 'Overpacing campaigns:\n'
        for campaign, pacing in overpaced:
            text = ' - {} ({}%): {}'.format(
                campaign.get_long_name(),
                int(pacing),
                'https://one.zemanta.com/campaigns/{}/ad_groups?page=1'.format(campaign.pk)
            )
            self._print(text)
            self.email_body += text + '\n'
        self.email_body += '\n'
        self.email_body += 'Underpacing campaigns:\n'
        for campaign, pacing in underpaced:
            text = ' - {} ({}%): {}'.format(
                campaign.get_long_name(),
                int(pacing),
                'https://one.zemanta.com/campaigns/{}/ad_groups?page=1'.format(campaign.pk)
            )
            self._print(text)
            self.email_body += text + '\n'
        self.email_body += '\n'
