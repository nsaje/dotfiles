import datetime

import prodops.audience_report
import prodops.helpers
import utils.command_helpers


class Command(utils.command_helpers.Z1Command):
    help = "Create audience report"

    def add_arguments(self, parser):
        parser.add_argument("--account", dest="account", default=None, help="Account ID")
        parser.add_argument("--campaign", dest="campaign", default=None, help="Campaign ID")
        parser.add_argument("--ad-group", dest="ad_group", default=None, help="Ad group ID")
        parser.add_argument(
            "--start-date", "-s", dest="start_date", default=None, help="Start date (default: start of current month)"
        )
        parser.add_argument(
            "--end-date", "-e", dest="end_date", default=None, help="End date (excluded, default: today)"
        )

    def _print(self, msg):
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        lookup, lookup_id = None, None
        for key in ("account", "campaign", "ad_group"):
            if options[key]:
                lookup, lookup_id = "{}_id".format(key), int(options[key])
                break
        if not lookup:
            self._print("Missing lookup. Specify account, campaign or ad group.")
            return
        today = datetime.date.today()
        start_date = (
            options["start_date"]
            and datetime.datetime.strptime(options["start_date"], "%Y-%m-%d").date()
            or datetime.date(today.year, today.month, 1)
        )
        end_date = options["end_date"] and datetime.datetime.strptime(options["end_date"], "%Y-%m-%d").date() or today
        filepath = prodops.audience_report.create_report(lookup, lookup_id, gte=start_date, lt=end_date)
        self._print(
            "Report generated: {}".format(
                prodops.helpers.upload_report_from_fs("ar/{}".format(filepath.split("/")[-1]), filepath)
            )
        )
