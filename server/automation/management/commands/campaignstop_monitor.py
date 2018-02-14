import datetime
import sys

import automation.campaignstop

from utils.command_helpers import ExceptionCommand
from utils import dates_helper
from utils import slack


class Command(ExceptionCommand):

    def add_arguments(self, parser):
        parser.add_argument('--date', '-d', dest='date', default=None,
                            help='Date checked (default yesterday)')
        parser.add_argument('--slack', dest='slack', action='store_true',
                            help='Notify via slack')
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')

    def handle(self, *args, **options):
        self._init_options(options)
        self._audit_stopped_campaigns()

    def _init_options(self, options):
        self.slack = options['slack']
        self.verbose = options['verbose']

        self.date = dates_helper.local_yesterday()
        if options['date']:
            self.date = datetime.datetime.strptime(options['date'], "%Y-%m-%d")

    def _audit_stopped_campaigns(self):
        campaigns = automation.campaignstop.audit_stopped_campaigns(self.date)
        if not campaigns:
            return

        if self.slack:
            slack.publish(
                self._get_slack_message(campaigns),
                msg_type=slack.MESSAGE_TYPE_INFO,
                username='Real-time campaign stop monitor'
            )

        if self.verbose:
            sys.stdout.write(self._get_verbose_message(campaigns))
            sys.stdout.flush()

    def _get_slack_message(self, campaigns):
        message = 'Campaigns stopped yesterday:\n'
        for campaign in campaigns:
            message += '- {}\n'.format(slack.campaign_url(campaign))
        return message

    def _get_verbose_message(self, campaigns):
        message = 'Campaigns stopped yesterday:\n'
        for campaign in campaigns:
            message += '- {} ({})\n'.format(campaign.name, campaign.id)
        return message
