import csv
import logging

import dash.features.geolocation
import dash.regions
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


class Command(Z1Command):

    help = "Export Eins supported geolocations into a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("output", type=str, help="output.csv")

    def handle(self, *args, **options):
        locs = (
            dash.features.geolocation.Geolocation.objects.all()
            .exclude(type="zip")
            .order_by("type", "key", "name")
            .values("key", "name", "type")
        )

        with open(options["output"], "w") as f:
            csv_writer = csv.DictWriter(f, fieldnames=["key", "type", "name"])
            csv_writer.writerows(locs)
