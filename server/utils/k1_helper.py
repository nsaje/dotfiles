import json
import logging
import urllib
import urllib2

import newrelic.agent
from django.conf import settings

from server.celery import app

from utils import request_signer
from utils import dates_helper

logger = logging.getLogger(__name__)


def update_accounts(account_ids, msg=''):
    for account_id in account_ids:
        update_account(account_id, msg=msg)


def update_account(account_id, msg=''):
    _send_task(settings.K1_CONSISTENCY_PING_ACCOUNT_QUEUE,
               'consistency_ping_account',
               account_id=account_id,
               msg=msg)


def update_ad_groups(ad_group_ids, msg=''):
    for ag_id in ad_group_ids:
        update_ad_group(ag_id, msg=msg)


def update_ad_group(ad_group_id, msg=''):
    _send_task(settings.K1_CONSISTENCY_PING_AD_GROUP_QUEUE,
               'consistency_ping_ad_group',
               ad_group_id=ad_group_id,
               msg=msg)


def update_content_ads(ad_group_id, content_ad_ids, msg=''):
    for ad_id in content_ad_ids:
        update_content_ad(ad_group_id, ad_id, msg=msg)


def update_content_ad(ad_group_id, content_ad_id, msg=''):
    _send_task(settings.K1_CONSISTENCY_PING_CONTENT_AD_QUEUE,
               'consistency_ping_content_ad',
               ad_group_id=ad_group_id,
               content_ad_id=content_ad_id,
               msg=msg)


def update_blacklist(ad_group_id, msg=''):
    _send_task(settings.K1_CONSISTENCY_PING_BLACKLIST_QUEUE,
               'consistency_ping_blacklist',
               ad_group_id=ad_group_id,
               msg=msg)


@newrelic.agent.function_trace()
def _send_task(queue_name, task_name, **kwargs):
    if settings.K1_DEMO_MODE:
        return

    kwargs['initiated_at_dt'] = dates_helper.utc_now()

    try:
        app.send_task(task_name, queue=queue_name, kwargs=kwargs)
    except Exception:
        logger.exception("Error sending ping to k1. Task: %s", task_name, extra={
            'data': kwargs,
        })


def _call_api(url, data=None, method='GET'):
    if settings.K1_DEMO_MODE and method != 'GET':
        return {}

    request = urllib2.Request(url, data)
    request.get_method = lambda: method
    response = request_signer.urllib2_secure_open(request, settings.K1_API_SIGN_KEY[0])

    status_code = response.getcode()
    if status_code != 200:
        raise Exception('Invalid response status code. status code: {}'.format(status_code))

    ret = json.loads(response.read())
    if ret['error']:
        raise Exception('Request not successful. error: {}'.format(ret['error']))

    return ret.get('response')


def get_adgroup_realtimestats(ad_group_id, params={}):
    url = settings.K1_REALTIMESTATS_ADGROUP_URL.format(ad_group_id=ad_group_id)
    if not url:
        return []
    if params:
        url += '?' + urllib.urlencode(params)
    return _call_api(url)
