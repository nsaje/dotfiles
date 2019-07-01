import datetime

import analytics.monitor
import utils.command_helpers
import utils.email_helper


class Command(utils.command_helpers.Z1Command):
    help = "Audit credits"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")
        parser.add_argument("--send-emails", dest="send_emails", action="store_true", help="Send emails")

        parser.add_argument("--date", "-d", dest="date", default=None, help="Date checked (default today)")
        parser.add_argument("--days", "-n", dest="days", default="14", help="Days in the future to check")

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        alarms = analytics.monitor.audit_account_credits(
            date=options["date"] and datetime.datetime.strptime(options["date"], "%Y-%m-%d").date(),
            days=options["days"] and int(options["days"]) or 14,
        )
        sales = {}
        for account in alarms:
            account_settings = account.get_current_settings()
            if not account_settings.default_sales_representative:
                continue
            sales.setdefault(account_settings.default_sales_representative, []).append(account)

        for sales_user, accounts in sales.items():
            has_permissions = sales_user.has_perm("zemauth.can_receive_sales_credit_email")
            self._print("{}: {}".format(sales_user, ", ".join(a.name for a in accounts)))
            if options["send_emails"] and has_permissions:
                utils.email_helper.send_depleting_credits_email(sales_user, accounts)
