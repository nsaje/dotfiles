from datetime import datetime
from functools import partial

import newrelic.agent
from django.http import Http404

import dash.constants
import dash.features.submission_filters
import dash.models
from dash import constants
from utils import dates_helper
from utils import db_router
from utils import metrics_compat
from utils import sspd_client
from utils import threads
from utils import zlogging

from .base import K1APIView

logger = zlogging.getLogger(__name__)


OUTBRAIN_SOURCE_SLUG = "outbrain"
BIZWIRE_CAMPAIGN_ID = 1096
SOURCES_SSPD_REQUIRED = (120, 170)  # MSN


class ContentAdsView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        content_ad_ids = request.GET.get("content_ad_ids")
        ad_group_ids = request.GET.get("ad_group_ids")
        include_archived = request.GET.get("include_archived") == "True"
        exclude_display = request.GET.get("exclude_display", "false").lower() == "true"

        content_ads = dash.models.ContentAd.objects.all().filter(image_present=True)
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
        if exclude_display:
            content_ads = content_ads.exclude_display()
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
                "type": item.type,
                "language": campaign_settings_map[item.ad_group.campaign_id].language,
                "title": item.title,
                "url": item.url,
                "redirect_id": item.redirect_id,
                "image_id": item.image_id,
                "image_width": item.image_width,
                "image_height": item.image_height,
                "image_hash": item.image_hash,
                "image_crop": item.image_crop,
                "icon_id": item.icon.image_id if item.icon else None,
                "icon_width": item.icon.width if item.icon else None,
                "icon_height": item.icon.height if item.icon else None,
                "icon_hash": item.icon.image_hash if item.icon else None,
                "description": "" if item.ad_group_id == 156382 else item.description,
                "brand_name": item.brand_name,
                "display_url": item.display_url,
                "call_to_action": item.call_to_action,
                "tracker_urls": item.tracker_urls,
                "video_asset": video_asset,
                "label": item.label,
                "additional_data": item.additional_data,
                "document_id": item.document_id,
                "document_features": item.document_features,
                "ad_tag": item.ad_tag,
            }

            if content_ad["icon_id"] is None:
                default_icon = item.ad_group.campaign.account.settings.default_icon

                if default_icon:
                    content_ad["icon_id"] = default_icon.image_id
                    content_ad["icon_width"] = default_icon.width
                    content_ad["icon_height"] = default_icon.height
                    content_ad["icon_hash"] = default_icon.image_hash

            response.append(content_ad)

        return self.response_ok(response)

    def put(self, request, content_ad_id):
        try:
            content_ad = dash.models.ContentAd.objects.get(id=content_ad_id)
        except dash.models.ContentAd.DoesNotExist:
            logger.exception("update_content_ad: content_ad does not exist", content_ad=content_ad_id)
            raise Http404

        updates = {}
        data = request.data
        if "document_id" in data and content_ad.document_id != data["document_id"]:
            updates["document_id"] = data["document_id"]

        if "document_features" in data and content_ad.document_features != data["document_features"]:
            updates["document_features"] = data["document_features"]

        if updates:
            content_ad.update(None, write_history=False, **updates)

        return self.response_ok(data)


class ContentAdSourcesView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        content_ad_ids = request.GET.get("content_ad_ids")
        ad_group_ids = request.GET.get("ad_group_ids")
        source_types = request.GET.get("source_types")
        slugs = request.GET.get("source_slugs")
        source_content_ad_ids = request.GET.get("source_content_ad_ids")
        modified_dt_from = request.GET.get("modified_dt_from")
        include_state = request.GET.get("include_state", "true").lower() == "true"
        include_blocked = request.GET.get("include_blocked", "true").lower() == "true"
        exclude_display = request.GET.get("exclude_display", "false").lower() == "true"

        should_get_review_information = include_state or not include_blocked

        sspd_thread = None
        if should_get_review_information:
            sspd_fn = partial(
                sspd_client.get_approval_status,
                ad_group_ids.split(",") if ad_group_ids else None,
                content_ad_ids.split(",") if content_ad_ids else None,
                source_types.split(",") if source_types else None,
                slugs.split(",") if slugs else None,
            )
            sspd_thread = threads.AsyncFunction(sspd_fn)
            sspd_thread.start()

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
        if exclude_display:
            content_ad_sources = content_ad_sources.exclude_display()

        if modified_dt_from:
            try:
                modified_dt = datetime.strptime(modified_dt_from, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError as error:
                logger.exception("Invalid input parameters.")
                return self.response_error(str(error), status=400)

            content_ad_sources = content_ad_sources.filter(modified_dt__gte=modified_dt)

        content_ad_sources = content_ad_sources.select_related(
            "content_ad", "source", "content_ad__ad_group__campaign__account"
        ).values(
            "id",
            "content_ad_id",
            "content_ad__ad_group_id",
            "content_ad__ad_group__campaign_id",
            "content_ad__ad_group__campaign__type",
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

        if should_get_review_information:
            amplify_review_statuses = self._get_amplify_review_statuses(content_ad_sources)
            if sspd_thread is not None:
                sspd_statuses = self._get_sspd_thread_result(sspd_thread)

        if not include_blocked:
            content_ad_sources = [
                content_ad_source
                for content_ad_source in content_ad_sources
                if not (
                    self._is_blocked_by_amplify(content_ad_source, amplify_review_statuses)
                    or self._is_blocked_by_sspd(content_ad_source, sspd_statuses)
                )
            ]

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
                    content_ad_source, amplify_review_statuses, sspd_statuses
                )

            response.append(item)

        return self.response_ok(response)

    def _get_amplify_review_statuses(self, content_ad_sources):
        statuses = dash.models.ContentAdSource.objects.filter(
            content_ad_id__in=set(content_ad_source["content_ad_id"] for content_ad_source in content_ad_sources),
            source__bidder_slug=OUTBRAIN_SOURCE_SLUG,
        ).values("content_ad_id", "submission_status")
        return {status["content_ad_id"]: status["submission_status"] for status in statuses}

    @newrelic.agent.function_trace()
    def _get_sspd_thread_result(self, sspd_thread):
        sspd_thread.join()
        return sspd_thread.get_result()

    def _get_content_ad_source_state(self, content_ad_source, amplify_review_statuses, sspd_statuses):
        if self._is_blocked_by_amplify(content_ad_source, amplify_review_statuses) or self._is_blocked_by_sspd(
            content_ad_source, sspd_statuses
        ):
            return dash.constants.ContentAdSourceState.INACTIVE
        else:
            return content_ad_source["state"]

    @staticmethod
    def _is_blocked_by_amplify(content_ad_source, amplify_review_statuses):
        if content_ad_source["content_ad__ad_group__campaign__type"] == dash.constants.CampaignType.DISPLAY:
            return False

        source_submission_policy = content_ad_source["source__content_ad_submission_policy"]
        ad_group_amplify_review = content_ad_source["content_ad__ad_group__amplify_review"]
        content_ad_amplify_review = content_ad_source["content_ad__amplify_review"]
        amplify_review_status = amplify_review_statuses.get(
            content_ad_source["content_ad_id"], dash.constants.ContentAdSubmissionStatus.PENDING
        )
        return (
            content_ad_amplify_review
            and ad_group_amplify_review
            and source_submission_policy == dash.constants.SourceSubmissionPolicy.AUTOMATIC_WITH_AMPLIFY_APPROVAL
            and amplify_review_status != dash.constants.ContentAdSubmissionStatus.APPROVED
        )

    @staticmethod
    def _is_blocked_by_sspd(content_ad_source, sspd_statuses):
        if content_ad_source["content_ad__ad_group__campaign__type"] == dash.constants.CampaignType.DISPLAY:
            return False

        if content_ad_source["content_ad__ad_group__campaign_id"] == BIZWIRE_CAMPAIGN_ID:
            return False

        sspd_status = sspd_statuses.get(content_ad_source["id"])

        if not sspd_status and content_ad_source["source_id"] in SOURCES_SSPD_REQUIRED:
            metrics_compat.incr("content_ads_source.missing_sspd_status", 1)
            return True

        return sspd_status == dash.constants.ContentAdSubmissionStatus.REJECTED

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
                metrics_compat.timing(
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
