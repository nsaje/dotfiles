import datetime

from django.db.models import Q

import dash.models
import prodops.audience_report
import prodops.helpers
import utils.command_helpers

OEN = 305
HEADER = ("Ad ID", "Brand / Agency", "Image URL", "Landing page", "Title", "Display URL", "Brand name", "Description")


class Command(utils.command_helpers.ExceptionCommand):
    help = "Create ad submission report"

    def add_arguments(self, parser):
        parser.add_argument("source", type=str)
        parser.add_argument("--premium-only", dest="is_premium", action="store_true", default=False)
        parser.add_argument("--not-premium", dest="is_not_premium", action="store_true", default=False)
        parser.add_argument("--approved-only", dest="is_approved", action="store_true", default=False)
        parser.add_argument("--pending-only", dest="is_pending", action="store_true", default=False)
        parser.add_argument("--live-only", dest="is_live", action="store_true", default=False)
        parser.add_argument("--ex-oen", dest="is_not_oen", action="store_true", default=False)

    def _print(self, msg):
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        cas_list = dash.models.ContentAdSource.objects.all()

        source = options["source"]
        if source.isdigit():
            cas_list = cas_list.filter(source_id=int(source))
        elif source:
            cas_list = cas_list.filter(
                source=dash.models.Source.objects.get(Q(bidder_slug="b1_{}".format(source)) | Q(bidder_slug=source))
            )
        else:
            self._print("No source.")
            return

        flags = []
        if options["is_premium"]:
            cas_list = cas_list.filter(
                Q(content_ad__ad_group__custom_flags__b1_msn_approved=True)
                | Q(content_ad__ad_group__campaign__custom_flags__b1_msn_approved=True)
                | Q(content_ad__ad_group__campaign__account__custom_flags__b1_msn_approved=True)
                | Q(content_ad__ad_group__campaign__account__agency__custom_flags__b1_msn_approved=True)
            )
            flags.append("premium")
        if options["is_not_premium"]:
            cas_list = cas_list.exclude(
                Q(content_ad__ad_group__custom_flags__b1_msn_approved=True)
                | Q(content_ad__ad_group__campaign__custom_flags__b1_msn_approved=True)
                | Q(content_ad__ad_group__campaign__account__custom_flags__b1_msn_approved=True)
                | Q(content_ad__ad_group__campaign__account__agency__custom_flags__b1_msn_approved=True)
            )
            flags.append("notpremium")
        if options["is_approved"]:
            cas_list = cas_list.filter(submission_status=dash.constants.ContentAdSubmissionStatus.APPROVED)
            flags.append("approved")
        if options["is_pending"]:
            cas_list = cas_list.filter(
                submission_status__in=(
                    dash.constants.ContentAdSubmissionStatus.PENDING,
                    dash.constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                )
            )
            flags.append("pending")
        if options["is_live"]:
            cas_list = cas_list.filter(
                content_ad__ad_group_id__in=dash.models.AdGroup.objects.all()
                .filter_running()
                .values_list("pk", flat=True)
            )
            flags.append("live")
        if options["is_not_oen"]:
            cas_list = cas_list.exclude(content_ad__ad_group__campaign__account_id=OEN)
            flags.append("exoen")

        cas_list = cas_list.select_related(
            "content_ad",
            "content_ad__ad_group",
            "content_ad__ad_group__campaign",
            "content_ad__ad_group__campaign__account",
            "content_ad__ad_group__campaign__account__agency",
        )

        out = []
        for content_ad_source in cas_list:
            if content_ad_source.content_ad.video_asset:
                continue
            out.append(
                (
                    content_ad_source.content_ad.pk,
                    content_ad_source.content_ad.ad_group.campaign.account.get_long_name(),
                    content_ad_source.content_ad.get_image_url(),
                    content_ad_source.content_ad.url,
                    content_ad_source.content_ad.title,
                    content_ad_source.content_ad.display_url,
                    content_ad_source.content_ad.brand_name,
                    content_ad_source.content_ad.description,
                )
            )

        self._print(
            "Report: "
            + prodops.helpers.generate_report(
                "{}_ads_{}_{}".format(source, "-".join(flags), datetime.date.today()), [HEADER] + out
            )
        )
