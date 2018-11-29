import datetime

from dash.features.native_server import constants
from dash.features.native_server import native_server_billing
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):
    help = "Calculate billing cost for CPC goal bidding agencies."

    def add_arguments(self, parser):
        parser.add_argument("agency_id", type=int, help="An ID from a agency running NAS with CPC billing.")
        parser.add_argument(
            "--from",
            type=str,
            default=3,
            help="Start of the billing period to process. " "Date or number of daays to process.",
        )
        parser.add_argument("--until", type=str, help="End date of the billing period to process.")

    def handle(self, *args, **options):

        if options.get("until"):
            until = datetime.datetime.strptime(options["until"], "%Y-%m-%d").date()
        else:
            until = datetime.datetime.today()
        try:
            since = datetime.datetime.strptime(options["from"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            delta = int(options["from"])
            since = until - datetime.timedelta(days=delta)

        if since > until:
            raise ValueError("Starting date '{}' must be before the end date '{}'".format(since, until))
        agency_id = options.get("agency_id")
        if agency_id not in constants.CPC_GOAL_TO_BID_AGENCIES:
            raise ValueError(
                "'{}' is not a Native Ad Server CPC billing customer. Valid IDs are : {}".format(
                    agency_id, constants.CPC_GOAL_TO_BID_AGENCIES
                )
            )
        native_server_billing.process_cpc_billing(since, until, agency_id)
