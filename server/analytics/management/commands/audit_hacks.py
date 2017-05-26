import utils.command_helpers
import utils.slack
import analytics.monitor

ALERT_MSG = """{} {} ({}) is spending ({}) with an unconfirmed hack - *{}*"""


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit custom hacks"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')
        parser.add_argument('--slack', dest='slack', action='store_true',
                            help='Notify via slack')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        for hack, spend in analytics.monitor.audit_custom_hacks():
            entity = (hack.agency or hack.account or hack.campaign or hack.ad_group)
            message = ALERT_MSG.format(
                hack.get_level(),
                entity.name,
                entity.pk,
                spend,
                str(hack)
            )
            self._print(message)
            if options.get('slack'):
                utils.slack.publish(
                    message,
                    msg_type=utils.slack.MESSAGE_TYPE_WARNING,
                    username='Hacks')
