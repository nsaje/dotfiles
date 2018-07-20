import unicodecsv as csv

from django.db.models import Q

import utils.command_helpers
import dash.features.submission_filters
import core.source


class Command(utils.command_helpers.ExceptionCommand):
    help = "Create inventory report"

    def add_arguments(self, parser):
        parser.add_argument("--column", dest="column", default="content_ad_id", help="Lookup column in CSV")
        parser.add_argument(
            "--level", dest="level", default="content_ad", help='Lookup level ("content_ad", "ad_group", ...)'
        )
        parser.add_argument("--verbose", dest="verbose", default=False, action="store_true")
        parser.add_argument("source", type=str, help="Source slug")
        parser.add_argument(
            "state",
            type=str,
            default="block",
            help="Filter state",
            choices=dash.features.submission_filters.SubmissionFilterState.get_all_names(),
        )
        parser.add_argument("filter_csv", type=str)

    def handle(self, *args, **options):
        source = core.source.Source.objects.get(
            Q(bidder_slug="b1_{}".format(options["source"])) | Q(bidder_slug=options["source"])
        )
        state = getattr(dash.features.submission_filters.SubmissionFilterState, options["state"])
        values = []
        with open(options["filter_csv"]) as fd:
            for row in csv.DictReader(fd):
                values.append(int(row[options["column"]]))
        new_submission_filters = dash.features.submission_filters.SubmissionFilter.objects.bulk_create(
            source, state, options["level"], values
        )
        if options["verbose"]:
            for submission_filter in new_submission_filters:
                self.stdout.write("{}\n".format(submission_filter))
