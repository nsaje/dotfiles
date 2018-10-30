import datetime

import analytics.monitor
import dash.constants
import dash.models
import utils.command_helpers
import utils.slack
from utils import converters

VALID_ACCOUNT_TYPES = (dash.constants.AccountType.ACTIVATED, dash.constants.AccountType.MANAGED)

ALERT_MSG = (
    """Spend column '{col}' on date {date} in table {tbl} is different than in daily statements (off by ${err})."""
)


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit spend pattern"

    def add_arguments(self, parser):
        parser.add_argument("--account_id", "-a", dest="account_id", help="Account ID")
        parser.add_argument("--date", "-d", dest="date", help="Date checked (default yesterday)")
        parser.add_argument("--from-date", dest="from_date", help="From Date checked")
        parser.add_argument("--till-date", dest="till_date", help="End Date checked")
        parser.add_argument("--past-days", dest="past_days", help="Past days to check (including yesterday)")
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        account_id = int(options.get("account_id") or "0") or None
        yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(1)
        dates = [yesterday]
        if options["date"]:
            dates = [datetime.datetime.strptime(options["date"], "%Y-%m-%d").date()]
        if options["from_date"]:
            from_date = datetime.datetime.strptime(options["from_date"], "%Y-%m-%d").date()

            till_date = (
                datetime.datetime.strptime(options["till_date"], "%Y-%m-%d").date()
                if options["till_date"]
                else yesterday
            )
            dates = [from_date]
            while dates[-1] < till_date:
                date = dates[-1] + datetime.timedelta(1)
                dates.append(date)
        if options["past_days"]:
            dates = [yesterday - datetime.timedelta(x) for x in range(int(options["past_days"]), 0, -1)]

        all_issues = []
        for date in dates:
            issues = analytics.monitor.audit_spend_integrity(date, account_id=account_id, max_err=10 ** 9)
            all_issues.extend(issues)

        if not all_issues:
            self._print("OK")
            return

        if account_id:
            account = dash.models.Account.objects.get(pk=account_id)
            self._print("FAIL on account {}".format(account.name))
        else:
            self._print("FAIL")

        for date, table, key, err in issues:
            self._print(" - on {}, table {}: {} (error: {})".format(str(date), table, key, err))
            if options.get("slack"):
                utils.slack.publish(
                    ALERT_MSG.format(
                        date=date.strftime("%b %d %Y"), err=converters.nano_to_decimal(err), tbl=table, col=key
                    ),
                    msg_type=utils.slack.MESSAGE_TYPE_CRITICAL,
                    username="Spend patterns",
                )
