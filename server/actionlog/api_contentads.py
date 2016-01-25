import logging
import sys
import traceback

from django.db import transaction

import actionlog.api
import actionlog.constants
import actionlog.exceptions
import actionlog.models
import actionlog.zwei_actions

import dash.constants
import dash.models

import utils.url_helper

logger = logging.getLogger(__name__)


def init_insert_content_ad_action(content_ad_source, request=None, send=True):
    ad_group_source = dash.models.AdGroupSource.objects.filter(
        ad_group=content_ad_source.content_ad.ad_group,
        source=content_ad_source.source
    ).select_related('ad_group', 'source__source_type').get()

    action = _create_action(
        ad_group_source,
        actionlog.constants.Action.INSERT_CONTENT_AD,
        args={
            'source_campaign_key': ad_group_source.source_campaign_key,
            'content_ad': _get_content_ad_dict(ad_group_source, content_ad_source)
        },
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


def init_insert_content_ad_batch(batch, source, request, send=True):
    content_ad_sources = dash.models.ContentAdSource.objects.filter(content_ad__batch=batch, source=source)

    if not content_ad_sources.exists():
        logger.info('init_insert_content_ad_batch: no content ad sources for batch id: {}'.format(batch.id))
        return None

    ad_group_source = dash.models.AdGroupSource.objects.filter(
        ad_group=content_ad_sources[0].content_ad.ad_group,
        source=source
    ).select_related('ad_group', 'source__source_type').get()

    args = {
        'source_campaign_key': ad_group_source.source_campaign_key,
        'content_ads': [_get_content_ad_dict(ad_group_source, cas) for cas in content_ad_sources],
        'extra': {}
    }

    if ad_group_source.source.source_type.type == dash.constants.SourceType.GRAVITY:
        args['extra']['ad_group_id'] = ad_group_source.ad_group.id
        args['extra']['campaign_name'] = ad_group_source.get_external_name()
        args['extra']['batch_name'] = batch.name

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        args['extra']['brand_name'] = ad_group_settings.brand_name

        if request and request.user:
            args['extra']['user_email'] = request.user.email

    action = _create_action(
        ad_group_source,
        actionlog.constants.Action.INSERT_CONTENT_AD_BATCH,
        args=args,
        request=request,
    )

    msg = "insert_content_ad_batch action created: ad_group_source.id: {}".format(
        ad_group_source.id,
    )
    logger.info(msg)

    if send:
        actionlog.zwei_actions.send(action)

    return action


def _create_update_content_ad_action(content_ad_source, ad_group_source, changes, request):
    args = {
        'source_campaign_key': ad_group_source.source_campaign_key,
        'content_ad': _get_content_ad_dict(ad_group_source, content_ad_source),
        'changes': changes,
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

    return action


def init_update_content_ad_action(content_ad_source, changes, request, send=True):
    if type(changes) is not dict:
        raise Exception('changes is not of type dict. changes: {}'.format(changes))

    ad_group_source = dash.models.AdGroupSource.objects.filter(
        ad_group=content_ad_source.content_ad.ad_group,
        source=content_ad_source.source
    ).select_related('ad_group', 'source__source_type').get()

    action = _create_update_content_ad_action(content_ad_source, ad_group_source, changes, request)

    if send:
        actionlog.zwei_actions.send(action)

    return action


def init_bulk_update_content_ad_actions(content_ad_sources_changes, request, check_action_exists=False):
    ad_group_sources = {
        (ags.ad_group_id, ags.source_id): ags for ags in dash.models.AdGroupSource.objects.filter(
            ad_group_id__in=[cas.content_ad.ad_group_id for cas, _ in content_ad_sources_changes],
            source_id__in=[cas.source_id for cas, _ in content_ad_sources_changes]
        ).select_related('ad_group', 'source__source_type')
    }

    actions = []
    for content_ad_source, changes in content_ad_sources_changes:
        ad_group_source = ad_group_sources.get((content_ad_source.content_ad.ad_group_id, content_ad_source.source_id))

        if check_action_exists and _waiting_action_exists(ad_group_source, content_ad_source):
            continue

        actions.append(_create_update_content_ad_action(content_ad_source, ad_group_source, changes, request))

    return actions


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
    logger.debug(msg)

    if send:
        actionlog.zwei_actions.send(action)

    return action


def init_submit_ad_group_action(ad_group_source, content_ad_source, request, send=False):
    args = {
        'source_campaign_key': ad_group_source.source_campaign_key,
        'content_ad': _get_content_ad_dict(ad_group_source, content_ad_source)
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


def _get_content_ad_dict(ad_group_source, content_ad_source):
    if ad_group_source.source.update_tracking_codes_on_content_ads() and\
            ad_group_source.can_manage_content_ads:
        ad_group_tracking_codes = ad_group_source.ad_group.get_current_settings().get_tracking_codes()

        url = content_ad_source.content_ad.url_with_tracking_codes(
            utils.url_helper.combine_tracking_codes(
                ad_group_tracking_codes,
                ad_group_source.get_tracking_ids(),
            )
        )
    else:
        url = content_ad_source.content_ad.url

    result = {
        'ad_group_id': content_ad_source.content_ad.ad_group_id,
        'content_ad_id': content_ad_source.content_ad_id,
        'source_content_ad_id': content_ad_source.source_content_ad_id,
        'state': content_ad_source.state,
        'title': content_ad_source.content_ad.title,
        'url': url,
        'submission_status': content_ad_source.submission_status,
        'image_id': content_ad_source.content_ad.image_id,
        'image_width': content_ad_source.content_ad.image_width,
        'image_height': content_ad_source.content_ad.image_height,
        'image_hash': content_ad_source.content_ad.image_hash,
        'redirect_id': content_ad_source.content_ad.redirect_id,
        'display_url': content_ad_source.content_ad.display_url,
        'brand_name': content_ad_source.content_ad.brand_name,
        'description': content_ad_source.content_ad.description,
        'call_to_action': content_ad_source.content_ad.call_to_action,
        'tracking_slug': ad_group_source.source.tracking_slug,
        'tracker_urls': content_ad_source.content_ad.tracker_urls
    }

    return result


def _waiting_action_exists(ad_group_source, content_ad_source):
    return actionlog.models.ActionLog.objects.filter(
        action=[actionlog.constants.Action.UPDATE_CONTENT_AD,
                actionlog.constants.Action.INSERT_CONTENT_AD,
                actionlog.constants.Action.INSERT_CONTENT_AD_BATCH],
        state__in=[actionlog.constants.ActionState.FAILED, actionlog.constants.ActionState.WAITING],
        ad_group_source=ad_group_source,
        content_ad_source=content_ad_source,
    ).exists()


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
            callback = utils.url_helper.get_zwei_callback_url(action.id)

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
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
