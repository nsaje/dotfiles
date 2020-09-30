import json
import time
import urllib.error
import urllib.parse
import urllib.request

import newrelic.agent
from django.conf import settings

from server.celery import app
from utils import request_signer
from utils import zlogging

logger = zlogging.getLogger(__name__)


def update_accounts(accounts, msg="", priority=False):
    for account in accounts:
        update_account(account, msg=msg, priority=priority)


def update_account(account, msg="", priority=False):
    _send_task(
        settings.K1_CONSISTENCY_PING_ACCOUNT_QUEUE,
        "consistency_ping_account",
        account_id=account.id,
        msg=msg,
        priority=priority,
    )


def update_ad_groups(ad_groups, msg="", priority=False):
    for ad_group in ad_groups:
        update_ad_group(ad_group, msg=msg, priority=priority)


def update_ad_group(ad_group, msg="", priority=False):
    _send_task(
        settings.K1_CONSISTENCY_PING_AD_GROUP_QUEUE,
        "consistency_ping_ad_group",
        account_id=ad_group.campaign.account_id,
        ad_group_id=ad_group.id,
        msg=msg,
        priority=priority,
    )


def update_content_ads(content_ads, msg="", priority=False):
    for content_ad in content_ads:
        update_content_ad(content_ad, msg=msg, priority=priority)


def update_content_ad(content_ad, msg="", priority=False):
    _send_task(
        settings.K1_CONSISTENCY_PING_CONTENT_AD_QUEUE,
        "consistency_ping_content_ad",
        account_id=content_ad.ad_group.campaign.account_id,
        ad_group_id=content_ad.ad_group_id,
        content_ad_id=content_ad.id,
        msg=msg,
        priority=priority,
    )


@newrelic.agent.function_trace()
def _send_task(queue_name, task_name, **kwargs):
    if settings.K1_DEMO_MODE:
        return

    kwargs["initiated_at"] = time.time()

    try:
        app.send_task(task_name, queue=queue_name, ignore_result=True, kwargs=kwargs)
    except Exception:
        logger.exception("Error sending ping to k1.", task_name=task_name, data=kwargs)


def _call_api(url, data=None, method="GET"):
    if settings.K1_DEMO_MODE and method != "GET":
        return {}

    request = urllib.request.Request(url, data.encode("utf-8") if data else None)
    request.get_method = lambda: method
    response = request_signer.urllib_secure_open(request, settings.K1_API_SIGN_KEY[0])

    status_code = response.getcode()
    if status_code != 200:
        raise Exception("Invalid response status code. status code: {}".format(status_code))

    ret = json.loads(response.read())
    if ret["error"]:
        raise Exception("Request not successful. error: {}".format(ret["error"]))

    return ret.get("response")


def get_adgroup_realtimestats(ad_group_id, params={}):
    url = settings.K1_REALTIMESTATS_ADGROUP_URL.format(ad_group_id=ad_group_id)
    if not url:
        return {"stats": []}
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return _call_api(url)


def get_yahoo_migration(account_id):
    url = settings.K1_YAHOO_MIGRATION_URL.format(account_id=account_id)
    return _call_api(url)


def update_yahoo_migration(account_id, **data):
    url = settings.K1_YAHOO_MIGRATION_URL.format(account_id=account_id)
    return _call_api(url, json.dumps(data), method="PUT")


def get_yahoo_migration_campaign_mappings(account_id):
    url = settings.K1_YAHOO_MIGRATION_CAMPAIGN_MAPPINGS_URL.format(account_id=account_id)
    return _call_api(url)


def get_yahoo_migration_content_ad_mappings(account_id):
    url = settings.K1_YAHOO_MIGRATION_CONTENT_AD_MAPPINGS_URL.format(account_id=account_id)
    return _call_api(url)
