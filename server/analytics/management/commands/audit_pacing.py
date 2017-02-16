import datetime
from decimal import Decimal

import utils.command_helpers
import utils.email_helper

import zemauth.models
import dash.models
import analytics.monitor


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

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        alarms = analytics.monitor.audit_pacing(
            date=options['date'] and datetime.datetime.strptime(options['date'], "%Y-%m-%d").date(),
            max_pacing=Decimal(options['max_pacing']),
            min_pacing=Decimal(options['min_pacing']),
        )
        valid_emails = set(
            user.email for user in zemauth.models.User.objects.all().get_users_with_perm(
                'can_receive_pacing_email'
            )
        )
        campaigns = {c.pk: c for c in dash.models.Campaign.objects.filter(
            pk__in=set(a[0] for a in alarms)
        )}

        for campaign_id, pacing, alert in alarms:
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
                return
            utils.email_helper.send_pacing_notification_email(
                campaign, emails, pacing, alert
            )
