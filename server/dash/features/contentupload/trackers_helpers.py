import re
from typing import Dict
from typing import List
from typing import Union

from typing_extensions import TypedDict

from dash import constants

GDPR_REGEX = re.compile(r"{gdpr}|{gdpr_consent_[0-9]+}|\[gdpr\]|\[gdpr_consent_[0-9]+\]", re.IGNORECASE)


class ContentAdTracker(TypedDict):
    event_type: str
    method: str
    url: str
    fallback_url: Union[None, str]
    tracker_optional: bool
    supported_privacy_frameworks: List[str]


def convert_legacy_trackers(tracker_urls: List[str], tracker_optional: bool = False) -> List[ContentAdTracker]:
    if tracker_urls is None:
        return []

    trackers = [
        get_tracker(
            url=tracker_url,
            fallback_url=None,
            event_type=constants.TrackerEventType.IMPRESSION,
            method=constants.TrackerMethod.IMG,
            tracker_optional=tracker_optional,
        )
        for tracker_url in tracker_urls
        if tracker_url
    ]
    return trackers


def get_tracker(
    url: str,
    event_type: str,
    method: str,
    tracker_optional: bool = False,
    fallback_url: Union[None, str] = None,
    **kwargs,
) -> ContentAdTracker:
    return {
        "event_type": event_type,
        "method": method,
        "url": url,
        "fallback_url": fallback_url,
        "supported_privacy_frameworks": get_privacy_frameworks(url, fallback_url),
        "tracker_optional": tracker_optional,
    }


def get_privacy_frameworks(url: str, fallback_url: Union[None, str]) -> List[str]:
    if fallback_url:
        return list(set(_get_privacy_frameworks_from_url(url)) & set(_get_privacy_frameworks_from_url(fallback_url)))
    else:
        return _get_privacy_frameworks_from_url(url)


def map_trackers_to_csv(trackers: List[ContentAdTracker]) -> Dict:
    csv_trackers = {}
    for i, tracker in enumerate(trackers, start=1):
        csv_trackers["tracker_{}_event_type".format(i)] = tracker.get("event_type")
        csv_trackers["tracker_{}_method".format(i)] = tracker.get("method")
        csv_trackers["tracker_{}_url".format(i)] = tracker.get("url")
        csv_trackers["tracker_{}_fallback_url".format(i)] = tracker.get("fallback_url")
        csv_trackers["tracker_{}_optional".format(i)] = "true" if tracker.get("tracker_optional") else "false"
    return csv_trackers


def get_tracker_status_key(url: str, method: str) -> str:
    return "{}__{}".format(url, method)


def _get_privacy_frameworks_from_url(url: str) -> List[str]:
    if not url:
        return []

    privacy_frameworks = []
    if GDPR_REGEX.search(url):
        privacy_frameworks.append(constants.TrackerPrivacyFramework.GDPR)

    if "{us_privacy}" in url or "[us_privacy]" in url:
        privacy_frameworks.append(constants.TrackerPrivacyFramework.CCPA)

    return privacy_frameworks
