import logging

import csv

from utils.command_helpers import ExceptionCommand
import dash.regions

import dash.features.geolocation

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

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
