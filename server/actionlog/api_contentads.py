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


def init_insert_content_ad_action(content_ad_source, request=None, send=True):
    ad_group_source = dash.models.AdGroupSource.objects.get(ad_group=content_ad_source.content_ad.ad_group,
                                                            source=content_ad_source.source)
    ad_group_settings = ad_group_source.ad_group.get_current_settings()

    args = {
        'source_campaign_key': ad_group_source.source_campaign_key,
        'content_ad_id': content_ad_source.get_source_id(),
        'content_ad': {
            'state': content_ad_source.state,
            'title': content_ad_source.content_ad.title,
            'url': content_ad_source.content_ad.url,
            'submission_status': content_ad_source.submission_status,
            'image_id': content_ad_source.content_ad.image_id,
            'image_width': content_ad_source.content_ad.image_width,
            'image_height': content_ad_source.content_ad.image_height,
            'image_hash': content_ad_source.content_ad.image_hash,
            'display_url': ad_group_settings.display_url,
            'brand_name': ad_group_settings.brand_name,
            'description': ad_group_settings.description,
            'call_to_action': ad_group_settings.call_to_action,
            'tracking_slug': ad_group_source.source.tracking_slug
        }
    }

    if content_ad_source.source_content_ad_id:
        args['content_ad']['source_content_ad_id'] = content_ad_source.source_content_ad_id

    action = _create_action(
        ad_group_source,
        actionlog.constants.Action.INSERT_CONTENT_AD,
        args=args,
        request=request,
        content_ad_source=content_ad_source
    )

    msg = "insert_content_ad action created: content_ad_source.id: {}".format(
        content_ad_source.id,
    )
    logger.info(msg)

    if send:
        actionlog.zwei_actions.send(action)

    return action


def init_update_content_ad_action(content_ad_source, request, send=True):
    ad_group_source = dash.models.AdGroupSource.objects.get(ad_group=content_ad_source.content_ad.ad_group,
                                                            source=content_ad_source.source)
    args = {
        'source_campaign_key': ad_group_source.source_campaign_key,
        'content_ad_id': content_ad_source.get_source_id(),
        'content_ad': {
            'state': content_ad_source.state,
            'submission_status': content_ad_source.submission_status
        }
    }

    action = _create_action(
        ad_group_source,
        actionlog.constants.Action.UPDATE_CONTENT_AD,
        args=args,
        request=request,
        content_ad_source=content_ad_source
    )

    msg = "update_content_ad action created: content_ad_source.id: {}".format(
        content_ad_source.id,
    )
    logger.info(msg)

    if send:
        actionlog.zwei_actions.send(action)

    return action


def init_get_content_ad_status_action(ad_group_source, order, request, send=True):
    args = {
        'source_campaign_key': ad_group_source.source_campaign_key
    }

    action = _create_action(
        ad_group_source,
        actionlog.constants.Action.GET_CONTENT_AD_STATUS,
        args=args,
        order=order,
        request=request
    )

    msg = "get_content_ad_status action created: ad_group_source.id: {}".format(
        ad_group_source.id,
    )
    logger.info(msg)

    if send:
        actionlog.zwei_actions.send(action)

    return action


def init_submit_ad_group_action(ad_group_source, content_ad_source, request, send=False):
    ad_group_settings = ad_group_source.ad_group.get_current_settings()
    args = {
        'source_campaign_key': ad_group_source.source_campaign_key,
        'content_ad': {
            'id': content_ad_source.get_source_id(),
            'state': content_ad_source.state,
            'title': content_ad_source.content_ad.title,
            'url': content_ad_source.content_ad.url,
            'image_id': content_ad_source.content_ad.image_id,
            'image_width': content_ad_source.content_ad.image_width,
            'image_height': content_ad_source.content_ad.image_height,
            'display_url': ad_group_settings.display_url,
            'brand_name': ad_group_settings.brand_name,
            'description': ad_group_settings.description,
            'call_to_action': ad_group_settings.call_to_action,
        }
    }

    action = _create_action(
        ad_group_source,
        actionlog.constants.Action.SUBMIT_AD_GROUP,
        args=args,
        request=request,
        content_ad_source=content_ad_source
    )

    msg = "submit_ad_group action created: content_ad_source.id: {}".format(
        content_ad_source.id,
    )
    logger.info(msg)

    if send:
        actionlog.zwei_actions.send(action)

    return action


def _create_action(ad_group_source, action, args={}, content_ad_source=None, request=None, order=None):
    action = actionlog.models.ActionLog(
        action=action,
        action_type=actionlog.constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        content_ad_source=content_ad_source,
        order=order
    )
    action.save(request)

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

            action.save(request)

            return action
    except Exception as e:
        logger.exception('An exception occurred while initializing content ad source action.')
        msg = traceback.format_exc(e)

        action.state = actionlog.constants.ActionState.FAILED
        action.message = msg
        action.save(request)

        et, ei, tb = sys.exc_info()
        raise actionlog.exceptions.InsertActionException, ei, tb
