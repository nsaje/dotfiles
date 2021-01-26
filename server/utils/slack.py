import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

from utils import zlogging

logger = zlogging.getLogger(__name__)

DASH_URL = "https://one.zemanta.com/v2/analytics/{level}/{id}/{tab}"

USER_DEFAULT = "Z1"
USER_FRAUD = "Fraud Audit"
USER_AD_GROUP = "Audit Ad groups"
USER_AUDIT_CPC = "Audit CPC"
USER_BCM = "Budgets Info"
USER_CAMPAIGN_STOP = "Real-time campaign stop"
USER_BLUEKAI_MONITORING = "BlueKai Monitoring"
USER_SPEND_PATTERNS = "Spend patterns"
USER_REFRESH_K1 = "Refresh k1"
USER_AUTOPILOT = "Autopilot"
USER_HACKS = "Hacks"
USER_OVERSPEND = "OverSpend"
USER_ETL_MATERIALIZE = "ETL Materialize"

MESSAGE_TYPE_SUCCESS = ":sunglasses:"
MESSAGE_TYPE_INFO = ":information_source:"
MESSAGE_TYPE_WARNING = ":warning:"
MESSAGE_TYPE_CRITICAL = ":rage:"

CHANNEL_ALERTS_RND_PRODOPS = "rnd-solutions-feed"
CHANNEL_ZEM_FEED_BUDGETS = "zem-feed-budgets"
CHANNEL_ZEM_FEED_NEW_ACCOUNTS = "zem-feed-new-accounts"
CHANNEL_ZEM_FEED_CAMPSTOP = "zem-feed-campstop"
CHANNEL_RND_Z1_ALERTS = "rnd-z1-alerts"
CHANNEL_RND_Z1_ALERTS_AUX = "rnd-z1-alerts-aux"
CHANNEL_ZEM_FEED_HACKS = "zem-feed-hacks"


def _post_to_slack(data):
    if settings.SLACK_LOG_ENABLE:
        data = urllib.parse.urlencode({"payload": json.dumps(data)})
        req = urllib.request.Request(settings.SLACK_INCOMING_HOOK_URL, data.encode("utf-8"))
        response = urllib.request.urlopen(req)
        return response.read() == "ok"
    else:
        logger.warning("Slack log disabled", message=data)


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


def publish(
    text,
    channel=CHANNEL_ALERTS_RND_PRODOPS,
    msg_type=MESSAGE_TYPE_INFO,
    username=USER_DEFAULT,
    attachments=None,
    **kwargs,
):
    data = {}
    data.update(kwargs)
    data.update({"text": text, "username": username})
    if msg_type:
        data["icon_emoji"] = msg_type
    if channel:
        data["channel"] = channel
    if attachments:
        data["attachments"] = attachments
    _post_to_slack(data)
