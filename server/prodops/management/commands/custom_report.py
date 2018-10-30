import prodops.helpers
import utils.command_helpers


class Command(utils.command_helpers.ExceptionCommand):
    help = "Create custom report from RS query"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str)
        parser.add_argument("query", type=str)

    def _print(self, msg):
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        download_url = prodops.helpers.generate_report_from_query(options["name"], options["query"])
        self._print("Download URL: " + download_url)
        self._print("S3 command: aws s3 cp s3://z1-custom-reports/custom-csv/{}.csv .".format(options["name"]))
