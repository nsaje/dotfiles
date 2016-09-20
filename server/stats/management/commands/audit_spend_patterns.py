import datetime

import utils.command_helpers
import utils.slack
import stats.monitor
from stats.constants import SlackMsgTypes

ALERT_MSG = """Spend change on {d} is bellow threshold ({change}% < {thr}%). Check <https://one.zemanta.com/all_accounts/accounts?start_date={fd}&end_date={td}&page=1|Zemanta one>."""


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit spend pattern"

    def add_arguments(self, parser):
        parser.add_argument('--date', '-d', dest='date',
                            help='Date checked (default yesterday)')
        parser.add_argument('--day-range', dest='day_range', default=5,
                            help='Range of days to check (default 5)')
        parser.add_argument('--threshold', dest='threshold', default=0.8,
                            help='Threshold for alarm (default 0.8)')
        parser.add_argument('--fdm-threshold', dest='fdm_threshold', default=0.6,
                            help='Threshold for alarm on first of month (default 0.6)')
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write('{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
        if options['date']:
            date = datetime.datetime.strptime(options['date'], "%Y-%m-%d").date()

        status, alarming_dates = stats.monitor.audit_spend_patterns(
            date,
            threshold=float(options['threshold']),
            first_in_month_threshold=float(options['fdm_threshold']),
            day_range=int(options['day_range']),
        )

        if not status:
            self._print('FAIL')
            for date, change in alarming_dates:
                thr = float(options['fdm_threshold'] if date.day == 1 else options['threshold'])
                self._print(' - {}: {} < {}'.format(date, change, thr))
                utils.slack.publish(ALERT_MSG.format(
                    d=date.strftime('%b %d %Y'),
                    change=change * 100,
                    thr=thr * 100,
                    fd=str(date - datetime.timedelta(7)),
                    td=str(date + datetime.timedelta(1)),
                ), msg_type=SlackMsgTypes.WARNING, username='Spend patterns')
        else:
            self._print('OK')
