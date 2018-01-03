import utils.command_helpers
import utils.slack
import analytics.monitor

ALERT_MSG_ENTITY = u"""{} {} ({}) is spending ({}) with an unconfirmed hack - *{}*"""
ALERT_MSG_GLOBAL = u"""Unconfirmed global hack *{}* is spending"""


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
            entity = hack.get_entity()
            if not entity:
                message = ALERT_MSG_GLOBAL.format(hack.summary)
            else:
                message = ALERT_MSG_ENTITY.format(
                    hack.get_level(),
                    entity.name,
                    entity.pk,
                    spend,
                    hack,
                )
            self._print(message)
            if options.get('slack'):
                utils.slack.publish(
                    message,
                    msg_type=utils.slack.MESSAGE_TYPE_WARNING,
                    username='Hacks')
