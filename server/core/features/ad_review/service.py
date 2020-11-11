import collections

from django.db.models.query import QuerySet

import core.models
from dash import constants
from utils import sspd_client
from utils import zlogging

logger = zlogging.getLogger(__name__)


SOURCES_SSPD_REQUIRED = (120, 170)  # MSN
OUTBRAIN_SOURCE_ID = 3


def get_per_source_submission_status_map(content_ads):
    per_source_map = collections.defaultdict(dict)

    if not isinstance(content_ads, QuerySet):
        content_ads = core.models.ContentAd.objects.filter(id__in=[content_ad.id for content_ad in content_ads])

    content_ads = content_ads.select_related("ad_group__campaign").prefetch_related("contentadsource_set__source")

    content_ads_ids = [content_ad.id for content_ad in content_ads]
    sspd_status_map = _get_sspd_status_map(content_ads_ids)
    amplify_reviews_map = _get_amplify_reviews_map(content_ads_ids)

    for content_ad in content_ads:
        for content_ad_source in content_ad.contentadsource_set.all():

            submission_status, submission_error = _get_submission_status(
                content_ad,
                content_ad_source,
                content_ad_source.source.content_ad_submission_policy,
                sspd_status_map,
                amplify_reviews_map,
            )
            content_ad_source_dict = {
                "source_id": content_ad_source.source.id,
                "bidder_slug": content_ad_source.source.bidder_slug,
                "submission_status": submission_status,
                "submission_errors": submission_error,
            }
            per_source_map[content_ad.id][content_ad_source.source_id] = content_ad_source_dict

    return per_source_map


def _get_submission_status(
    content_ad, content_ad_source, content_ad_submission_policy, sspd_status_map, amplify_reviews_map
):
    if content_ad.ad_group.campaign.type == constants.CampaignType.DISPLAY:
        return content_ad_source.get_submission_status(), content_ad_source.submission_errors
    else:
        return _get_submission_status_for_native_ads(
            content_ad, content_ad_source, content_ad_submission_policy, sspd_status_map, amplify_reviews_map
        )


def _get_submission_status_for_native_ads(
    content_ad, content_ad_source, content_ad_submission_policy, sspd_status_map, amplify_reviews_map
):
    sspd_status = None
    if sspd_status_map:
        sspd_status = sspd_status_map.get(content_ad.id, {}).get(content_ad_source.source_id)

    if sspd_status is None and content_ad_source.source_id in SOURCES_SSPD_REQUIRED:
        return constants.ContentAdSubmissionStatus.NOT_AVAILABLE, ""
    if sspd_status and sspd_status.get("status") == constants.ContentAdSubmissionStatus.REJECTED:
        return sspd_status["status"], sspd_status["reason"]
    if _should_use_amplify_review(content_ad, content_ad_submission_policy, amplify_reviews_map):
        outbrain_content_ad_source = amplify_reviews_map[content_ad.id]
        return outbrain_content_ad_source.get_submission_status(), outbrain_content_ad_source.submission_errors
    return content_ad_source.get_submission_status(), content_ad_source.submission_errors


def _get_sspd_status_map(content_ads_ids):
    try:
        return sspd_client.get_content_ad_status(content_ads_ids)
    except sspd_client.SSPDApiException:
        logger.exception("Failed to fetch sspd status")
        return None


def _get_amplify_reviews_map(content_ads_ids):
    qs = core.models.ContentAdSource.objects.filter(content_ad_id__in=content_ads_ids, source_id=OUTBRAIN_SOURCE_ID)

    amplify_reviews_map = {}
    for content_ad_source in qs:
        amplify_reviews_map[content_ad_source.content_ad_id] = content_ad_source
    return amplify_reviews_map


def _should_use_amplify_review(content_ad, content_ad_submission_policy, amplify_reviews_map):
    return (
        content_ad_submission_policy == constants.SourceSubmissionPolicy.AUTOMATIC_WITH_AMPLIFY_APPROVAL
        and content_ad.amplify_review
        and content_ad.id in amplify_reviews_map
    )
