from django.db.models import Q

import utils.command_helpers
import dash.models
import dash.constants


class Command(utils.command_helpers.ExceptionCommand):
    help = "Recheck rejected ads"

    def add_arguments(self, parser):
        parser.add_argument(dest="source", nargs=1)
        parser.add_argument("--ad-groups", dest="ad_groups", default="")
        parser.add_argument("--campaigns", dest="campaigns", default="")

    def _print(self, msg):
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        source = options["source"] and options["source"][0]
        lookup = {}
        if source and source.isdigit():
            lookup["source_id"] = int(source)
        elif source:
            lookup["source"] = dash.models.Source.objects.get(
                Q(bidder_slug="b1_{}".format(source)) | Q(bidder_slug=source)
            )
        else:
            self._print("Invalid source.")
            return
        if options.get("ad_groups"):
            lookup["content_ad__ad_group_id__in"] = list(map(int, options.get("ad_groups", "").split(",")))
        elif options.get("campaigns"):
            lookup["content_ad__ad_group__campaign_id__in"] = list(map(int, options.get("campaigns", "").split(",")))
        else:
            self._print("No ad groups or campaigns.")
            return

        for cas in dash.models.ContentAdSource.objects.filter(
            submission_status=dash.constants.ContentAdSubmissionStatus.REJECTED, **lookup
        ).select_related("source"):
            print("Updating ad {} on source {} to PENDING".format(cas.content_ad_id, cas.source))
            cas.submission_status = dash.constants.ContentAdSubmissionStatus.PENDING
            cas.save()
