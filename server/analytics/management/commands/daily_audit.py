from django.conf import settings

import utils.command_helpers
import utils.email_helper
import analytics.monitor

RECIPIANTS = (
    'operations@zemanta.com',
    'prodops@zemanta.com',
)


class Command(utils.command_helpers.ExceptionCommand):
    help = "Daily audits"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')
        parser.add_argument('--send-emails', dest='send_emails', action='store_true',
                            help='Send emails')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        send_emails = options['send_emails']

        undefined_iab_running_campaigns = analytics.monitor.audit_iab_categories(running_only=True)
        undefined_iab_paused_campaigns = analytics.monitor.audit_iab_categories(paused_only=True)

        email_body = u'Active campaigns with undefined IAB categories:\n'
        self._print('Active campaigns with undefined IAB categories')
        for campaign in undefined_iab_running_campaigns:
            text = u' - {}: {}'.format(
                campaign.get_long_name(),
                u'https://one.zemanta.com/campaigns/{}/ad_groups?page=1'.format(campaign.pk)
            )
            self._print(text)
            email_body += text + u'\n'

        email_body += u'\nPaused campaigns with undefined IAB categories:\n'
        self._print('Paused campaigns with undefined IAB categories')
        for campaign in undefined_iab_paused_campaigns:
            text = u' - {}: {}'.format(
                campaign.get_long_name(),
                u'https://one.zemanta.com/campaigns/{}/ad_groups?page=1'.format(campaign.pk)
            )
            self._print(text)
            email_body += text + u'\n'

        if (undefined_iab_running_campaigns or undefined_iab_paused_campaigns) and send_emails:
            email = utils.email_helper.EmailMessage(
                'Daily audit',
                email_body,
                'Zemanta <{}>'.format(
                    settings.FROM_EMAIL
                ), RECIPIANTS)
            email.send()
