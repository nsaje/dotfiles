import logging
import sys
import traceback
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction

import actionlog.api
import actionlog.constants
import actionlog.exceptions
import actionlog.models
import actionlog.zwei_actions

import dash.constants
import dash.models

logger = logging.getLogger(__name__)


def init_insert_content_ad_action(content_ad_source):
    args = {
        'content_ad_key': content_ad_source.get_source_key(),
        'content_ad': {
            'state': content_ad_source.state,
            'title': content_ad_source.content_ad.article.title,
            'url': content_ad_source.content_ad.article.url,
            'image': content_ad_source.content_ad.get_image_url(),
        }
    }

    action = _create_action(
        content_ad_source,
        actionlog.constants.Action.INSERT_CONTENT_AD,
        args
    )

    actionlog.zwei_actions.send(action)


def init_update_content_ad_action(content_ad_source):
    args = {
        'content_ad_key': content_ad_source.get_source_key(),
        'content_ad': {
            'state': content_ad_source.state,
        }
    }

    action = _create_action(
        content_ad_source,
        actionlog.constants.Action.UPDATE_CONTENT_AD,
        args
    )

    actionlog.zwei_actions.send(action)


def _create_action(content_ad_source, action, args={}):
    msg = "create upsert_content_ad action started: content_ad_source.id: {}".format(
        content_ad_source.id,
    )
    logger.info(msg)

    ad_group_source = dash.models.AdGroupSource.objects.get(
        ad_group_id=content_ad_source.content_ad.article.ad_group,
        source=content_ad_source.source,
    )

    action = actionlog.models.ActionLog.objects.create(
        action=action,
        action_type=actionlog.constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'credentials': ad_group_source.source_credentials and ad_group_source.source_credentials.credentials,
                'args': args,
                'callback_url': callback
            }

            action.payload = payload
            action.save()

            return action
    except Exception as e:
        logger.exception('An exception occurred while initializing content ad source action.')
        msg = traceback.format_exc(e)

        action.state = actionlog.constants.ActionState.FAILED
        action.message = msg
        action.save()

        et, ei, tb = sys.exc_info()
        raise actionlog.exceptions.InsertActionException, ei, tb
