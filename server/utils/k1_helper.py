import logging

from django.conf import settings

from server.celery import app

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


def _send_task(queue_name, task_name, **kwargs):
    if settings.K1_DEMO_MODE:
        return

    try:
        app.send_task(task_name, queue=queue_name, kwargs=kwargs)
    except:
        logger.exception("Error sending ping to k1. Task: %s", task_name, extra={
            'data': kwargs,
        })
