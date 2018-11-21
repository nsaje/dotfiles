import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


DEFAULT_USERNAME = "z1"
DASH_URL = "https://one.zemanta.com/v2/analytics/{level}/{id}/{tab}"

MESSAGE_TYPE_SUCCESS = ":sunglasses:"
MESSAGE_TYPE_INFO = ":information_source:"
MESSAGE_TYPE_WARNING = ":warning:"
MESSAGE_TYPE_CRITICAL = ":rage:"


def _post_to_slack(data):
    if settings.SLACK_LOG_ENABLE:
        data = urllib.parse.urlencode({"payload": json.dumps(data)})
        req = urllib.request.Request(settings.SLACK_INCOMING_HOOK_URL, data.encode("utf-8"))
        response = urllib.request.urlopen(req)
        return response.read() == "ok"
    else:
        logger.warning("Slack log disabled, message: %s", data)


def link(url="", anchor=""):
    return "<{url}|{anchor}>".format(url=url, anchor=anchor)


def ad_group_url(ad_group, tab="ads"):
    url = DASH_URL.format(level="adgroup", id=ad_group.pk, tab="sources")
    return link(url, ad_group.name)


def campaign_url(campaign, tab=""):
    url = DASH_URL.format(level="campaign", id=campaign.pk, tab=tab)
    return link(url, campaign.name)


def account_url(account, tab="campaigns"):
    url = DASH_URL.format(level="account", id=account.pk, tab=tab)
    return link(url, account.name)


def publish(text, channel=None, msg_type=MESSAGE_TYPE_INFO, username=DEFAULT_USERNAME, attachments=None):
    data = {"text": text, "username": username}
    if msg_type:
        data["icon_emoji"] = msg_type
    if channel:
        data["channel"] = channel
    if attachments:
        data["attachments"] = attachments
    _post_to_slack(data)
