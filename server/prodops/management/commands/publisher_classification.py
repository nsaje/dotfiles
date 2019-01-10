import argparse

from dash.features import publisher_classification
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    help = """
    Update data to Publisher Classification table, either from OEN or from a csv file. Can also dump table to S3.
    Duplicates are ignored. CSV columns headers must be accordingly to this:
    {}
    """.format(
        ", ".join(publisher_classification.constants.CSV_COLUMNS)
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv", type=str, nargs=argparse.OPTIONAL, help="Path for a CSV file with the headers. as described above."
        )
        parser.add_argument(
            "--update-from-oen",
            default=False,
            action="store_true",
            help="Import new classifications from OEN (Publisher Groups)",
        )
        parser.add_argument(
            "--upload-to-s3", default=False, action="store_true", help="Export publisher classifications from RDS to S3"
        )

    def handle(self, *args, **options):
        if options.get("update_from_oen"):
            self.stdout.write("Will update publisher classifications from OEN, (Publisher Groups)")
            update = publisher_classification.update_publisher_classsifications_from_oen()
            if not update:
                self.stdout.write("Publisher classifications are up-to-date. No new classifications inserted.")
                return
            for d in update:
                self.stdout.write("New publisher classification '{publisher}'/'{category}' added.".format(**d))

        if options.get("csv"):
            self.stdout.write("Will update publisher classifications from CSV file.")
            publisher_classification.update_publisher_classifications_from_csv(options.get("csv"))
        if options.get("upload_to_s3"):
            self.stdout.write("Will dump all RDS Publisher classifications to S3.")
            publisher_classification.upload_publisher_classifications_to_s3()
            self.stdout.write("Publisher classiciations uploaded on S3.")
