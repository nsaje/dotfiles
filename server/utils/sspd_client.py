import copy
import datetime
import json

import jwt
import requests
from django.conf import settings

from dash import constants
from dash import models
from utils import dates_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)

APPROVAL_STATUS_URL = "/service/approvalstatus"
CONTENT_AD_STATUS_URL = "/service/contentadstatus"
SOURCE_URL = "/service/source"
AD_GROUP_URL = "/service/adgroup"
CONTENT_AD_URL = "/service/contentad"
CONTENT_AD_SOURCE_URL = "/service/contentadsource"

MAX_REQUEST_IDS = 500
TIMEOUT = (10, 10)  # TIMEOUT IN SECONDS (CONNECT TIME, READ TIME)
TIMEOUT_SYNC_SOURCES = (30, 60)
TIMEOUT_SYNC_AD_GROUPS = (30, 60)
TIMEOUT_SYNC_CONTENT_ADS = (30, 60)
TIMEOUT_SYNC_CONTENT_AD_SOURCES = (30, 60)


class SSPDApiException(Exception):
    pass


def get_approval_status(
    ad_group_ids=None, content_ad_ids=None, source_types=None, slugs=None, content_ad_source_ids=None
):
    url = settings.SSPD_BASE_URL + APPROVAL_STATUS_URL
    approval_status_dict = {
        "adGroupIds": ad_group_ids,
        "contentAdIds": content_ad_ids,
        "sourceTypes": source_types,
        "slugs": slugs,
        "contentAdSourceIds": content_ad_source_ids,
    }
    approval_statuses = _make_request("post", url, data=json.dumps(approval_status_dict))
    return _map_approval_statuses(approval_statuses)


def _map_approval_statuses(approval_statuses):
    return {int(id_): getattr(constants.ContentAdSspdStatus, status) for id_, status in approval_statuses.items()}


def get_content_ad_status(content_ad_ids):
    url = settings.SSPD_BASE_URL + CONTENT_AD_STATUS_URL
    if not content_ad_ids:
        raise SSPDApiException("Request not allowed")
    content_ad_statuses = _paginate_request(
        "get", url, params={"contentAdIds": content_ad_ids}, paginate_key="contentAdIds", timeout=TIMEOUT
    )
    return _map_content_ad_statuses(content_ad_statuses)


def _map_content_ad_statuses(content_ad_statuses):
    source_map = {source.id: source for source in models.Source.objects.all()}
    return {
        int(id_): {
            source_map[source_status["sourceId"]].id: {
                "reason": source_status["reason"],
                "status": getattr(constants.ContentAdSspdStatus, source_status["status"]),
            }
            for source_status in per_source_statuses
        }
        for id_, per_source_statuses in content_ad_statuses.items()
    }


def sync_batch(batch):
    ad_group = models.AdGroup.objects.get(id=batch.ad_group_id)
    if ad_group.campaign.type == constants.CampaignType.DISPLAY:
        return

    success = sync_ad_groups({ad_group})
    if not success:
        logger.warning("Fail to sync ad_groups to SSPD for batch", batch=batch.id)
        return

    content_ads = _get_content_ads(batch)
    sources = _get_sources(content_ads)
    content_ad_sources = _get_content_ad_sources(content_ads)

    success = sync_sources(sources)
    if not success:
        logger.warning("Fail to sync sources to SSPD for batch", batch=batch.id)
        return

    success = sync_content_ads(content_ads)
    if not success:
        logger.warning("Fail to sync content_ads to SSPD for batch", batch=batch.id)
        return

    success = sync_content_ad_sources(content_ad_sources)
    if not success:
        logger.warning("Fail to sync content_ad_sources to SSPD for batch", batch=batch.id)


def _get_content_ads(batch):
    return set(batch.contentad_set.all())


def _get_sources(content_ads):
    items = set()
    for content_ad in content_ads:
        sources = set(content_ad.sources.all())
        items |= sources
    return items


def _get_content_ad_sources(content_ads):
    items = set()
    for content_ad in content_ads:
        content_ad_sources = set(content_ad.contentadsource_set.all())
        items |= content_ad_sources
    return items


def sync_sources(sources):
    try:
        url = settings.SSPD_BASE_URL + SOURCE_URL

        request = []
        for item in sources:
            item_dict = {
                "id": item.id,
                "name": item.name,
                "sourceType": item.source_type.type,
                "bidderSlug": item.bidder_slug,
            }
            request.append(item_dict)

        response = _make_request("post", url, data=json.dumps(request), timeout=TIMEOUT_SYNC_SOURCES)
        return response["data"]
    except SSPDApiException:
        return False
    except Exception:
        logger.exception("Unexpected exception")
        return False


def sync_ad_groups(ad_groups):
    try:
        url = settings.SSPD_BASE_URL + AD_GROUP_URL

        request = []
        for item in ad_groups:
            item_dict = {
                "id": item.id,
                "name": item.name,
                "campaignId": item.campaign.id,
                "campaignName": item.campaign.name,
                "accountId": item.campaign.account.id,
                "accountName": item.campaign.account.name,
                "agencyId": item.campaign.account.agency.id if item.campaign.account.agency else "",
                "agencyName": item.campaign.account.agency.name if item.campaign.account.agency else "",
            }
            request.append(item_dict)

        response = _make_request("post", url, data=json.dumps(request), timeout=TIMEOUT_SYNC_AD_GROUPS)
        return response["data"]
    except SSPDApiException:
        return False
    except Exception:
        logger.exception("Unexpected exception")
        return False


def sync_content_ads(content_ads):
    try:
        url = settings.SSPD_BASE_URL + CONTENT_AD_URL

        request = []
        for item in content_ads:
            item_dict = {
                "id": item.id,
                "adGroupId": item.ad_group_id,
                "title": item.title,
                "description": item.description,
                "brandName": item.brand_name,
                "imageId": item.image_id,
            }
            request.append(item_dict)

        response = _make_request("post", url, data=json.dumps(request), timeout=TIMEOUT_SYNC_CONTENT_ADS)
        return response["data"]
    except SSPDApiException:
        return False
    except Exception:
        logger.exception("Unexpected exception")
        return False


def sync_content_ad_sources(content_ad_sources):
    try:
        url = settings.SSPD_BASE_URL + CONTENT_AD_SOURCE_URL

        request = []
        for item in content_ad_sources:
            item_dict = {
                "id": item.id,
                "contentAdId": item.content_ad_id,
                "sourceId": item.source_id,
                "sourceContentAdId": item.source_content_ad_id,
            }
            request.append(item_dict)

        response = _make_request("post", url, data=json.dumps(request), timeout=TIMEOUT_SYNC_CONTENT_AD_SOURCES)
        return response["data"]
    except SSPDApiException:
        return False
    except Exception:
        logger.exception("Unexpected exception")
        return False


def _paginate_request(method, url, params, *, paginate_key, timeout=None):
    start = 0
    result = {}
    paginate_list = params.pop(paginate_key)
    while start < len(paginate_list):
        page_params = copy.copy(params)
        page_params[paginate_key] = ",".join(str(el) for el in paginate_list[start : start + MAX_REQUEST_IDS])
        result.update(_make_request(method, url, params=page_params, timeout=timeout))
        start += MAX_REQUEST_IDS
    return result


def _make_request(method, url, data=None, params=None, headers=None, timeout=None):
    if not headers:
        headers = {}
    _augment_with_auth_headers(headers)
    if method == "post":
        headers.update({"Content-type": "application/json"})
    try:
        response = requests.request(
            method, url, data=data if data else {}, params=params if params else {}, headers=headers, timeout=timeout
        )
    except requests.exceptions.RequestException as exception:
        raise SSPDApiException(exception) from exception
    if not response.ok:
        raise SSPDApiException("Request failed")
    return response.json()


def _augment_with_auth_headers(headers):
    payload = {"iss": "Z1", "exp": dates_helper.utc_now() + datetime.timedelta(seconds=60)}
    token = jwt.encode(payload, settings.SSPD_AUTH_SECRET, algorithm="HS256")
    auth_header = "Bearer " + token.decode("utf-8")
    headers.update({"Authorization": auth_header})
