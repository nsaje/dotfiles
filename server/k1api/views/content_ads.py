import logging

import influx
from django.http import Http404

import dash.constants
import dash.features.submission_filters
import dash.models
from dash import constants
from utils import dates_helper
from utils import db_for_reads
from utils import sspd_client
from .base import K1APIView

logger = logging.getLogger(__name__)


OUTBRAIN_SOURCE_SLUG = "outbrain"


class ContentAdsView(K1APIView):
    @db_for_reads.use_read_replica()
    def get(self, request):
        content_ad_ids = request.GET.get("content_ad_ids")
        ad_group_ids = request.GET.get("ad_group_ids")
        include_archived = request.GET.get("include_archived") == "True"

        content_ads = dash.models.ContentAd.objects.all()
        if not include_archived:
            content_ads = content_ads.exclude_archived()
            nonarchived_ad_groups = dash.models.AdGroup.objects.all().exclude_archived()
            content_ads.filter(ad_group__in=nonarchived_ad_groups)
        if content_ad_ids:
            content_ad_ids = content_ad_ids.split(",")
            content_ads = content_ads.filter(id__in=content_ad_ids)
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")
            content_ads = content_ads.filter(ad_group_id__in=ad_group_ids)
        content_ads = content_ads.select_related("ad_group", "ad_group__campaign", "ad_group__campaign__account")
        campaign_settings_map = {
            cs.campaign_id: cs
            for cs in (
                dash.models.CampaignSettings.objects.filter(
                    campaign_id__in=set([ca.ad_group.campaign_id for ca in content_ads])
                )
                .group_current_settings()
                .only("campaign_id", "language")
            )
        }

        response = []
        for item in content_ads:
            video_asset = None
            video_asset_obj = item.video_asset
            if video_asset_obj:
                video_asset = {
                    "id": str(video_asset_obj.id),
                    "duration": video_asset_obj.duration,
                    "formats": video_asset_obj.formats,
                    "vasturi": video_asset_obj.get_vast_url(),
                }
            content_ad = {
                "id": item.id,
                "ad_group_id": item.ad_group_id,
                "campaign_id": item.ad_group.campaign_id,
                "account_id": item.ad_group.campaign.account_id,
                "agency_id": item.ad_group.campaign.account.agency_id,
                "language": campaign_settings_map[item.ad_group.campaign_id].language,
                "title": item.title,
                "url": item.url,
                "redirect_id": item.redirect_id,
                "image_id": item.image_id,
                "image_width": item.image_width,
                "image_height": item.image_height,
                "image_hash": item.image_hash,
                "image_crop": item.image_crop,
                "description": "" if item.ad_group_id == 156382 else item.description,
                "brand_name": item.brand_name,
                "display_url": item.display_url,
                "call_to_action": item.call_to_action,
                "tracker_urls": item.tracker_urls,
                "video_asset": video_asset,
                "label": item.label,
                "additional_data": item.additional_data,
            }
            response.append(content_ad)

        return self.response_ok(response)


class ContentAdSourcesView(K1APIView):
    @db_for_reads.use_read_replica()
    def get(self, request):
        content_ad_ids = request.GET.get("content_ad_ids")
        ad_group_ids = request.GET.get("ad_group_ids")
        source_types = request.GET.get("source_types")
        slugs = request.GET.get("source_slugs")
        source_content_ad_ids = request.GET.get("source_content_ad_ids")
        include_state = request.GET.get("include_state", "True") == "True"
        content_ad_sources = dash.models.ContentAdSource.objects.filter(source__deprecated=False)

        if not content_ad_ids:  # exclude archived if not querying by id explicitly
            content_ad_sources.filter(content_ad__archived=False)
        if content_ad_ids:
            content_ad_sources = content_ad_sources.filter(content_ad_id__in=content_ad_ids.split(","))
        if ad_group_ids:
            content_ad_sources = content_ad_sources.filter(content_ad__ad_group_id__in=ad_group_ids.split(","))
        if source_content_ad_ids:
            content_ad_sources = content_ad_sources.filter(source_content_ad_id__in=source_content_ad_ids.split(","))

        if source_types:
            content_ad_sources = content_ad_sources.filter(source__source_type__type__in=source_types.split(","))
        if slugs:
            content_ad_sources = content_ad_sources.filter(source__bidder_slug__in=slugs.split(","))

        content_ad_sources = content_ad_sources.select_related(
            "content_ad", "source", "content_ad__ad_group__campaign__account"
        ).values(
            "id",
            "content_ad_id",
            "content_ad__ad_group_id",
            "content_ad__ad_group__campaign_id",
            "content_ad__ad_group__campaign__account_id",
            "content_ad__ad_group__campaign__account__agency_id",
            "content_ad__ad_group__amplify_review",
            "content_ad__amplify_review",
            "source_id",
            "source__content_ad_submission_policy",
            "source__bidder_slug",
            "source__tracking_slug",
            "source_content_ad_id",
            "submission_status",
            "state",
        )

        if request.GET.get("use_filters", "false") == "true":
            content_ad_sources = dash.features.submission_filters.filter_valid_content_ad_sources(content_ad_sources)

        amplify_review_statuses = {}
        sspd_statuses = {}

        if include_state:
            amplify_review_statuses = self._get_amplify_review_statuses(content_ad_sources)
            # if content_ad_sources:
            #     sspd_statuses = sspd_client.get_approval_status(
            #         [content_ad_source["id"] for content_ad_source in content_ad_sources]
            #     )

        response = []
        for content_ad_source in content_ad_sources:
            item = {
                "id": content_ad_source["id"],
                "content_ad_id": content_ad_source["content_ad_id"],
                "source_id": content_ad_source["source_id"],
                "ad_group_id": content_ad_source["content_ad__ad_group_id"],
                "source_slug": content_ad_source["source__bidder_slug"],
                "tracking_slug": content_ad_source["source__tracking_slug"],
                "source_content_ad_id": content_ad_source["source_content_ad_id"],
                "submission_status": content_ad_source["submission_status"],
            }
            if include_state:
                item["state"] = self._get_content_ad_source_state(
                    content_ad_source["state"],
                    content_ad_source["source__content_ad_submission_policy"],
                    content_ad_source["content_ad__ad_group__amplify_review"],
                    content_ad_source["content_ad__amplify_review"],
                    amplify_review_statuses.get(
                        content_ad_source["content_ad_id"], dash.constants.ContentAdSubmissionStatus.PENDING
                    ),
                    sspd_statuses.get(content_ad_source["id"]),
                )

            response.append(item)

        return self.response_ok(response)

    def _get_amplify_review_statuses(self, content_ad_sources):
        statuses = dash.models.ContentAdSource.objects.filter(
            content_ad_id__in=set(content_ad_source["content_ad_id"] for content_ad_source in content_ad_sources),
            source__bidder_slug=OUTBRAIN_SOURCE_SLUG,
        ).values("content_ad_id", "submission_status")
        return {status["content_ad_id"]: status["submission_status"] for status in statuses}

    def _get_content_ad_source_state(
        self,
        content_ad_source_state,
        source_submission_policy,
        ad_group_amplify_review,
        content_ad_amplify_review,
        amplify_review_status,
        sspd_status,
    ):
        if (
            (
                content_ad_amplify_review
                and ad_group_amplify_review
                and source_submission_policy == dash.constants.SourceSubmissionPolicy.AUTOMATIC_WITH_AMPLIFY_APPROVAL
                and amplify_review_status != dash.constants.ContentAdSubmissionStatus.APPROVED
            )
            # or sspd_status == dash.constants.ContentAdSubmissionStatus.REJECTED
            # or not sspd_status
        ):
            return dash.constants.ContentAdSourceState.INACTIVE
        else:
            return content_ad_source_state

    def put(self, request):
        content_ad_id = request.GET.get("content_ad_id")
        source_slug = request.GET.get("source_slug")
        data = request.data

        content_ad_source = dash.models.ContentAdSource.objects.filter(content_ad_id=content_ad_id).filter(
            source__bidder_slug=source_slug
        )

        if not content_ad_source:
            logger.exception(
                "update_content_ad_status: content_ad_source does not exist. content ad id: %d, source slug: %s",
                content_ad_id,
                source_slug,
            )
            raise Http404

        modified = False
        content_ad_source = content_ad_source[0]
        if "submission_status" in data and content_ad_source.submission_status != data["submission_status"]:
            if content_ad_source.submission_status == constants.ContentAdSubmissionStatus.PENDING and data[
                "submission_status"
            ] in [constants.ContentAdSubmissionStatus.REJECTED, constants.ContentAdSubmissionStatus.APPROVED]:
                time_delta = dates_helper.utc_now() - content_ad_source.modified_dt
                influx.timing(
                    "content_ads_source.submission_processing_time", time_delta.total_seconds(), exchange=source_slug
                )

            content_ad_source.submission_status = data["submission_status"]
            if content_ad_source.submission_status == constants.ContentAdSubmissionStatus.APPROVED:
                content_ad_source.submission_errors = None
            modified = True

        if "submission_errors" in data and content_ad_source.submission_errors != data["submission_errors"]:
            content_ad_source.submission_errors = data["submission_errors"]
            modified = True

        if "source_content_ad_id" in data and content_ad_source.source_content_ad_id != data["source_content_ad_id"]:
            if content_ad_source.source_content_ad_id:
                return self.response_error("Cannot change existing source_content_ad_id", status=400)
            content_ad_source.source_content_ad_id = data["source_content_ad_id"]
            modified = True

        if modified:
            content_ad_source.save()

        return self.response_ok(data)
