import datetime

import utils.command_helpers
import utils.slack
import stats.monitor
import dash.models
import dash.constants
from utils import converters
from stats.constants import SlackMsgTypes

VALID_ACCOUNT_TYPES = (
    dash.constants.AccountType.SELF_MANAGED,
    dash.constants.AccountType.MANAGED,
)

ALERT_MSG = """Spend column '{col}' on date {date} in table {tbl} is different than in daily statements (off by ${err})."""


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit spend pattern"

    def add_arguments(self, parser):
        parser.add_argument('--date', '-d', dest='date',
                            help='Date checked (default yesterday)')
        parser.add_argument('--from-date', dest='from_date',
                            help='From Date checked')
        parser.add_argument('--till-date', dest='till_date',
                            help='End Date checked')
        parser.add_argument('--past-days', dest='past_days',
                            help='Past days to check (including yesterday)')
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write('{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(1)
        dates = [yesterday]
        if options['date']:
            dates = [datetime.datetime.strptime(options['date'], "%Y-%m-%d").date()]
        if options['from_date']:
            from_date = datetime.datetime.strptime(options['from_date'], "%Y-%m-%d").date()

            till_date = datetime.datetime.strptime(
                options['till_date'],
                "%Y-%m-%d"
            ).date() if options['till_date'] else yesterday
            dates = [from_date]
            while dates[-1] < till_date:
                date = dates[-1] + datetime.timedelta(1)
                dates.append(date)
        if options['past_days']:
            dates = [
                yesterday-datetime.timedelta(x) for x in xrange(int(options['past_days']), 0, -1)
            ]

        all_issues = []
        for date in dates:
            issues = stats.monitor.audit_spend_integrity(date)
            all_issues.extend(issues)

        if not all_issues:
            self._print('OK')
            return

        self._print('FAIL')

        for date, table, key, err in issues:
            self._print(' - on {}, table {}: {} (error: {})'.format(str(date), table, key, err))
            utils.slack.publish(ALERT_MSG.format(
                date=date.strftime('%b %d %Y'),
                err=converters.nano_to_decimal(err),
                tbl=table,
                col=key
            ), msg_type=SlackMsgTypes.CRITICAL, username='Spend patterns')
