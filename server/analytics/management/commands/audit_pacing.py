import datetime
from decimal import Decimal

import utils.command_helpers
import utils.email_helper

import zemauth.models
import dash.models
import analytics.monitor

VALID_PACING_ACCOUNT_TYPES = (
    dash.constants.AccountType.ACTIVATED,
    dash.constants.AccountType.MANAGED,
    dash.constants.AccountType.PILOT,
)


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit pacing"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')
        parser.add_argument('--send-emails', dest='send_emails', action='store_true',
                            help='Send emails')
        parser.add_argument('--min-pacing', dest='min_pacing', default='50.0',
                            help='Min pacing threshold (default 50%)')
        parser.add_argument('--max-pacing', dest='max_pacing', default='150.0',
                            help='Max pacing threshold (default 150%)')
        parser.add_argument('--date', '-d', dest='date',
                            help='Date checked (default today)')
        parser.add_argument('--days-running', dest='days_running', default=7,
                            help='Minimal number of days that ad groups have to be running')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write('{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        date = (options['date'] and
                datetime.datetime.strptime(options['date'], "%Y-%m-%d").date() or
                datetime.date.today())
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
            date=date,
            max_pacing=Decimal(options['max_pacing']),
            min_pacing=Decimal(options['min_pacing']),
            campaign__in=list(flying_campaigns.values()),
        )
        valid_emails = set(
            user.email for user in zemauth.models.User.objects.get_users_with_perm(
                'can_receive_pacing_email'
            )
        )
        campaigns = {c.pk: c for c in dash.models.Campaign.objects.filter(
            pk__in=set(a[0] for a in alarms)
        )}

        for campaign_id, pacing, alert, projections in alarms:
            campaign = campaigns[campaign_id]
            emails = set(utils.email_helper.email_manager_list(campaign)) & valid_emails
            self._print('Campaign {} ({}) has {} pacing {}: send to {}'.format(
                campaign.pk,
                campaign.name,
                alert,
                pacing,
                ', '.join(emails) if emails else 'none'
            ))
            if not options['send_emails']:
                continue
            utils.email_helper.send_pacing_notification_email(
                campaign, emails, pacing, alert, projections
            )
