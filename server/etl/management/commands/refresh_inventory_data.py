import datetime

import dateutil.parser

from etl.inventory.service import refresh_inventory_data
from utils.command_helpers import Z1Command


class Command(Z1Command):
    help = (
        "Aggregate inventory data for last 30 days from supply_stats table and save processed data to inventory table"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--date_from", help="Iso formatted date. Date from which supply stats should be aggregated."
        )
        parser.add_argument("--date_to", help="Iso formatted date. Date to which supply stats should be aggregated.")

    def handle(self, *args, **options):
        date_from = datetime.datetime.utcnow().date() - datetime.timedelta(days=31)
        if options.get("date_from") is not None:
            date_from = dateutil.parser.parse(options["date_from"]).date()

        date_to = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
        if options.get("date_to") is not None:
            date_to = dateutil.parser.parse(options["date_to"]).date()

        refresh_inventory_data(date_from, date_to)
