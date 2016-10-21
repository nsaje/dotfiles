import logging
import sys
import traceback
import collections
from operator import attrgetter
import newrelic.agent

from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.query import QuerySet

from . import exceptions
from . import models
from . import constants
from . import zwei_actions

import dash.constants
import dash.models
import utils.url_helper

logger = logging.getLogger(__name__)


def init_set_ad_group_state(ad_group, state, request, send=True):
    order = models.ActionLogOrder.objects.create(
        order_type=constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE
    )

    if state == dash.constants.AdGroupSettingsState.ACTIVE:
        actions = init_enable_ad_group(ad_group, request, order=order, send=False)
    else:
        actions = init_pause_ad_group(ad_group, request, order=order, send=False)

    if send:
        zwei_actions.send(actions)

    return actions


def init_enable_ad_group(ad_group, request, order=None, send=True):
    source_settings_qs = dash.models.AdGroupSourceSettings.objects\
        .filter(ad_group_source__ad_group=ad_group)\
        .group_current_settings()

    allowed_sources_ids = ad_group.campaign.account.allowed_sources\
        .values_list('id', flat=True)

    new_actionlogs = []
    for source_settings in source_settings_qs:
        if source_settings.ad_group_source.source_id not in allowed_sources_ids:
            continue

        if source_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
            changes = {
                'state': dash.constants.AdGroupSourceSettingsState.ACTIVE,
            }
            new_actionlogs.extend(
                set_ad_group_source_settings(changes,
                                             source_settings.ad_group_source,
                                             request=request,
                                             order=order,
                                             send=send)
            )

    return new_actionlogs


def init_pause_ad_group(ad_group, request, order=None, send=True):
    new_actionlogs = []
    for ad_group_source in dash.models.AdGroupSource.objects.filter(ad_group=ad_group):
        changes = {
            'state': dash.constants.AdGroupSourceSettingsState.INACTIVE,
        }

        new_actionlogs.extend(
            set_ad_group_source_settings(
                changes,
                ad_group_source,
                request=request,
                order=order,
                send=send
            )
        )

    return new_actionlogs


def init_set_ad_group_manual_property(ad_group_source, request, prop, value):
    msg = u"init_set_ad_group_manual_property started: ad_group_source.id: {}, prop: {}, value: {}".format(
        ad_group_source.id,
        prop,
        value
    )
    logger.info(msg)

    if ad_group_source.source_campaign_key == settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE:
        logger.info('init_set_ad_group_manual_property: {} ad_group_source on ad_group {} pending - action not created'.format(
            dash.constants.SourceType.get_text(dash.constants.SourceType.GRAVITY),
            ad_group_source.ad_group.id))
        return

    if ad_group_source.source.maintenance or ad_group_source.source.deprecated:
        logger.info('Skipping creation of manual action since source {} is in maintenance mode or deprecated.'.format(
            ad_group_source.source.name))
        return

    try:
        existing_actions = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.MANUAL
        )
        existing_actions = [a for a in existing_actions if a.payload['property'] == prop]
        action = models.ActionLog(
            action=constants.Action.SET_PROPERTY,
            action_type=constants.ActionType.MANUAL,
            expiration_dt=None,
            state=constants.ActionState.WAITING,
            ad_group_source=ad_group_source,
            payload={
                'property': prop,
                'value': value,
            },
        )
        action.save(request)

        if existing_actions:
            for a in existing_actions:
                a.state = constants.ActionState.ABORTED
                a.save(request)

    except Exception as e:
        logger.exception('An exception occurred while initializing set_property action.')
        _handle_error(action, e, request)


def set_ad_group_source_settings(changes, ad_group_source, request=None, order=None, send=True):
    extra = {}
    if changes.get('cpc_cc') is not None:
        changes['cpc_cc'] = int(changes['cpc_cc'] * 10000)

    if changes.get('daily_budget_cc') is not None:
        changes['daily_budget_cc'] = int(changes['daily_budget_cc'] * 10000)

    if changes.get('tracking_code') is not None:
        extra['tracking_slug'] = ad_group_source.source.tracking_slug

    _init_set_ad_group_source_settings(
        ad_group_source=ad_group_source,
        conf=changes,
        request=request,
        order=order,
        extra=extra,
    )
    return send_delayed_actionlogs([ad_group_source], send=send)


def init_fetch_ad_group_source_settings(ad_group_source, request):
    order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.FETCH_STATUS
    )
    return _init_fetch_status(ad_group_source, order, request=request)


def set_publisher_blacklist(key, level, state, publishers, request, source_type, ad_group_source, send=True):
    if not publishers:
        return []

    action = models.ActionLog(
        action=constants.Action.SET_PUBLISHER_BLACKLIST,
        action_type=constants.ActionType.AUTOMATIC,
        expiration_dt=None,
        state=constants.ActionState.ABORTED,
    )
    action.save(request)

    try:
        with transaction.atomic():
            callback = utils.url_helper.get_zwei_callback_url(action.id)

            args = {
                'key': key,
                'level': level,
                'state': state,
                'publishers': publishers
            }

            payload = {
                'action': action.action,
                'source': source_type.type,
                'expiration_dt': action.expiration_dt,
                'args': args,
                'callback_url': callback,
            }

            action.ad_group_source = ad_group_source
            action.payload = payload
            action.save(request)
    except Exception as e:
        logger.exception('An exception occurred while initializing set_publisher_blacklist action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb

    return send_delayed_actionlogs(send=send)


def create_campaign(ad_group_source, name, request, send=True):
    action = None
    try:
        action = _init_create_campaign(ad_group_source, name, request)
    except exceptions.InsertActionException:
        pass
    else:
        if send:
            zwei_actions.send(action)

    return action


def create_audience(audience, request):
    action = models.ActionLog(
        action=constants.Action.CREATE_AUDIENCE,
        action_type=constants.ActionType.MANUAL,
        expiration_dt=None,
        state=constants.ActionState.WAITING,
        message=u'Create audience "{}" on Outbrain for account {} (#{}) with rules'.format(
            audience.name,
            audience.pixel.account.name,
            audience.pixel.account_id
        )
    )
    action.save(request)


@transaction.atomic
def cancel_expired_actionlogs():
    waiting_actionlogs = models.ActionLog.objects.\
        filter(
            state=constants.ActionState.WAITING,
            expiration_dt__lt=datetime.utcnow()
        )

    for actionlog in waiting_actionlogs:
        logger.info(
            'Action log %s has expired. Updating state to: %s.',
            actionlog,
            constants.ActionState.FAILED
        )

        actionlog.message = 'Action log has expired.'
        actionlog.state = constants.ActionState.FAILED
        actionlog.save()


def send_delayed_actionlogs(ad_group_sources=None, send=True):
    new_actionlogs = []
    with transaction.atomic():
        delayed_actionlogs = models.ActionLog.objects.filter(
            action__in=[constants.Action.SET_CAMPAIGN_STATE, constants.Action.SET_PUBLISHER_BLACKLIST],
            action_type=constants.ActionType.AUTOMATIC,
            state=constants.ActionState.DELAYED,
        ).order_by('created_dt')

        if ad_group_sources is not None:
            delayed_actionlogs = delayed_actionlogs.filter(ad_group_source__in=ad_group_sources)

        for actionlog in delayed_actionlogs:
            waiting_actionlogs = models.ActionLog.objects.filter(
                state=constants.ActionState.WAITING,
                action__in=[constants.Action.CREATE_CAMPAIGN,
                            constants.Action.SET_CAMPAIGN_STATE,
                            constants.Action.SET_PUBLISHER_BLACKLIST],
                action_type=constants.ActionType.AUTOMATIC,
                ad_group_source=actionlog.ad_group_source,
            )

            if waiting_actionlogs.exists():
                continue

            # WORKAROUND (will be fixed with new version of actionlogs)
            # some actions can be created (and delayed) when waiting on CREATE_CAMPAIGN action to complete
            # and source_campaign_key is not yet available (payload has empty value). In case it is still not
            # available prevent propagation of this action, otherwise update payload's source_campaign_key.
            if 'args' in actionlog.payload \
                    and 'source_campaign_key' in actionlog.payload['args'] \
                    and not actionlog.payload['args']['source_campaign_key']:
                if not actionlog.ad_group_source.source_campaign_key:
                    continue
                actionlog.payload['args']['source_campaign_key'] = actionlog.ad_group_source.source_campaign_key

            logger.info(
                'Sending delayed action log %s. Updating state to: %s.',
                actionlog,
                constants.ActionState.WAITING
            )
            actionlog.state = constants.ActionState.WAITING
            actionlog.expiration_dt = models._due_date_default()
            actionlog.payload['expiration_dt'] = actionlog.expiration_dt
            actionlog.save()

            new_actionlogs.append(actionlog)

    if send:
        zwei_actions.send(new_actionlogs)

    return new_actionlogs


def get_ad_group_sources_waiting(**kwargs):
    constraints = {}

    if 'ad_group' in kwargs:
        key = 'ad_group_source__ad_group'
        if isinstance(kwargs['ad_group'], collections.Sequence) or isinstance(kwargs['ad_group'], QuerySet):
            key += '__in'
        constraints[key] = kwargs['ad_group']
    if 'campaign' in kwargs:
        key = 'ad_group_source__ad_group__campaign'
        if isinstance(kwargs['campaign'], collections.Sequence) or isinstance(kwargs['campaign'], QuerySet):
            key += '__in'
        constraints[key] = kwargs['campaign']
    if 'account' in kwargs:
        key = 'ad_group_source__ad_group__campaign__account'
        if isinstance(kwargs['account'], collections.Sequence) or isinstance(kwargs['account'], QuerySet):
            key += '__in'
        constraints[key] = kwargs['account']

    actions = models.ActionLog.objects.filter(
        action=constants.Action.CREATE_CAMPAIGN,
        action_type=constants.ActionType.AUTOMATIC,
        state__in=[constants.ActionState.WAITING, constants.ActionState.FAILED],
        **constraints
    ).select_related('ad_group_source')

    return [action.ad_group_source for action in actions]


def is_waiting_for_manual_set_target_regions_action(ad_group_source):
    set_property_action = models.ActionLog.objects.filter(
        action=constants.Action.SET_PROPERTY,
        action_type=constants.ActionType.MANUAL,
        ad_group_source=ad_group_source,
        state__in=[constants.ActionState.FAILED, constants.ActionState.WAITING]
    )
    return any('target_regions' == act.payload['property'] for act in set_property_action)


@newrelic.agent.function_trace()
def is_waiting_for_set_actions(ad_group):
    action_types = (constants.Action.SET_CAMPAIGN_STATE, constants.Action.SET_PROPERTY)
    ad_group_sources = ad_group.adgroupsource_set.all()
    # get latest action for ad_group where order != null
    # using two queries for performance reasons
    try:
        latest_set_campaign_state_action = models.ActionLog.objects.filter(
            action=constants.Action.SET_CAMPAIGN_STATE,
            ad_group_source_id__in=[ags.id for ags in ad_group_sources],
            order__isnull=False
        ).latest('created_dt')
    except ObjectDoesNotExist:
        latest_set_campaign_state_action = None

    try:
        latest_set_property_action = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            ad_group_source_id__in=[ags.id for ags in ad_group_sources],
            order__isnull=False
        ).latest('created_dt')
    except ObjectDoesNotExist:
        latest_set_property_action = None

    if latest_set_campaign_state_action is None and latest_set_property_action is None:
        return False

    latest_action = max(
        [a for a in [latest_set_campaign_state_action, latest_set_property_action] if a is not None],
        key=attrgetter('created_dt'))

    # check whether there are unsuccessful actions in this order
    is_fail_in_latest_group = models.ActionLog.objects.filter(
        action__in=action_types,
        state=constants.ActionState.FAILED,
        ad_group_source_id__in=[ags.id for ags in ad_group_sources],
        order=latest_action.order
    ).exists()

    is_any_waiting_action = models.ActionLog.objects.filter(
        action__in=action_types,
        state=constants.ActionState.WAITING,
        ad_group_source_id__in=[ags.id for ags in ad_group_sources],
    ).exists()

    return is_fail_in_latest_group or is_any_waiting_action


def count_waiting_stats_actions():
    return models.ActionLog.objects.filter(
        Q(action_type=constants.ActionType.MANUAL) | Q(action=constants.Action.CREATE_CAMPAIGN),
        state=constants.ActionState.WAITING
    ).count()


def count_delayed_stats_actions():
    return models.ActionLog.objects.filter(
        state=constants.ActionState.DELAYED
    ).count()


def count_failed_stats_actions():
    return models.ActionLog.objects.filter(
        Q(action_type=constants.ActionType.MANUAL) |
        Q(action=constants.Action.CREATE_CAMPAIGN) |
        Q(action=constants.Action.SET_CAMPAIGN_STATE) |
        Q(action=constants.Action.INSERT_CONTENT_AD) |
        Q(action=constants.Action.INSERT_CONTENT_AD_BATCH) |
        Q(action=constants.Action.SUBMIT_AD_GROUP) |
        Q(action=constants.Action.UPDATE_CONTENT_AD),
        state=constants.ActionState.FAILED
    ).count()


def age_oldest_waiting_action(manual_action=True):
    if manual_action:
        filter_constraints = Q(action_type=constants.ActionType.MANUAL)
    else:
        filter_constraints = Q(action_type=constants.ActionType.AUTOMATIC)

    waiting_actions = models.ActionLog.objects.filter(
        filter_constraints,
        state=constants.ActionState.WAITING
    ).order_by('created_dt')

    if not waiting_actions.exists():
        return 0

    return int((datetime.utcnow() - waiting_actions[0].created_dt).total_seconds() / 3600)


@newrelic.agent.function_trace()
def is_sync_in_progress(ad_groups=None, campaigns=None, accounts=None, sources=None):
    '''
    sync is in progress if one of the following is true:
    - a get reports action for this ad_group is in 'waiting' state
    - a fetch status action for this ad_group is in 'waiting' state
    '''

    if ad_groups and accounts:
        raise Exception('Please set only one, ad_groups or accounts.')

    q = models.ActionLog.objects.filter(
        state=constants.ActionState.WAITING,
        action_type=constants.ActionType.AUTOMATIC,
        action__in=(constants.Action.FETCH_REPORTS,
                    constants.Action.FETCH_CAMPAIGN_STATUS)
    )

    if ad_groups:
        q = q.filter(ad_group_source__ad_group__in=ad_groups)
    elif campaigns:
        q = q.filter(ad_group_source__ad_group__campaign__in=campaigns)
    elif accounts:
        q = q.filter(ad_group_source__ad_group__campaign__account__in=accounts)

    if sources:
        q = q.filter(ad_group_source__source__in=sources)

    waiting_actions = q.exists()

    return waiting_actions


@newrelic.agent.function_trace()
def is_publisher_blacklist_sync_in_progress(ad_group):
    '''
    sync is in progress if one of the following is true:
    - a get reports action for this ad_group is in 'waiting' state
    - a fetch status action for this ad_group is in 'waiting' state
    '''
    if ad_group is None:
        return False

    campaign = ad_group.campaign
    account = campaign.account

    # limit amount of actionlogs through which to sift
    yesterday = datetime.utcnow() - timedelta(days=1)

    q = models.ActionLog.objects.filter(
        Q(
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
            action=constants.Action.SET_PUBLISHER_BLACKLIST,
            created_dt__gte=yesterday
        ) & Q(
            Q(ad_group_source__ad_group=ad_group) |
            Q(Q(
                Q(payload__contains="level\":\"{level}\"".format(level=dash.constants.PublisherBlacklistLevel.CAMPAIGN)) &
                Q(payload__contains="\"key\":[{key}".format(key=campaign.id))
              ) | Q(
                Q(payload__contains="level\":\"{level}\"".format(level=dash.constants.PublisherBlacklistLevel.ACCOUNT)) &
                Q(payload__contains="\"key\":[{key}".format(key=account.id))
              ) | Q(payload__contains="level\":\"{level}\"".format(level=dash.constants.PublisherBlacklistLevel.GLOBAL))
            )
        )
    )

    waiting_actions = q.exists()

    return waiting_actions


def _handle_error(action, e, request=None):
    msg = traceback.format_exc(e)

    logger.error(msg)

    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save(request)


def _get_campaign_settings(campaign):
    s = dash.models.CampaignSettings.objects.filter(campaign=campaign)
    if s:
        return s.latest('created_dt')

    return None


def _create_manual_action(ad_group_source, conf, request, order=None, message=''):
    if ad_group_source.source.maintenance or ad_group_source.source.deprecated:
        logger.info('Skipping creation of manual action since source {} is in maintenance mode or deprecated.'.format(
            ad_group_source.source.name))
        return

    for prop, val in conf.iteritems():
        action = models.ActionLog(
            action=constants.Action.SET_PROPERTY,
            action_type=constants.ActionType.MANUAL,
            expiration_dt=None,
            state=constants.ActionState.WAITING,
            ad_group_source=ad_group_source,
            payload={
                'property': prop,
                'value': val
            },
            order=order,
            message=message
        )
        action.save(request)


def _init_set_ad_group_source_settings(ad_group_source, conf, request, order=None, extra={}):
    logger.info('_init_set_ad_group_source_settings started: ad_group_source.id: %s, settings: %s',
                ad_group_source.id, str(conf))

    if ad_group_source.source.deprecated:
        return

    if ad_group_source.source_campaign_key == settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE:
        logger.info('_init_set_ad_group_source_settings: {} ad_group_source on ad_group {} pending - action not created'.format(
            dash.constants.SourceType.get_text(dash.constants.SourceType.GRAVITY),
            ad_group_source.ad_group.id))
        return

    if ad_group_source.source.maintenance:
        return

    if 'daily_budget_cc' in conf and\
       not ad_group_source.source.can_update_daily_budget_automatic() and\
       ad_group_source.source.can_update_daily_budget_manual():
        _create_manual_action(
            ad_group_source,
            {'daily_budget_cc': conf['daily_budget_cc']},
            request,
            order=order,
        )

        del conf['daily_budget_cc']

        if not len(conf):
            return

    action = models.ActionLog(
        action=constants.Action.SET_CAMPAIGN_STATE,
        action_type=constants.ActionType.AUTOMATIC,
        expiration_dt=None,
        state=constants.ActionState.ABORTED,
        ad_group_source=ad_group_source,
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
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                    'conf': conf,
                    'extra': extra,
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save(request)

    except Exception as e:
        logger.exception('An exception occurred while initializing set_campaign_state action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _init_fetch_status(ad_group_source, order, request=None):
    msg = '_init_fetch_status started: ad_group_source.id: {}'.format(
        ad_group_source.id
    )
    logger.debug(msg)

    action = models.ActionLog(
        action=constants.Action.FETCH_CAMPAIGN_STATUS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
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
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save(request)

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing get_campaign_status action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _init_fetch_reports(ad_group_source, date, order, request=None):
    msg = '_init_fetch_reports started: ad_group_source.id: {}, date: {}'.format(
        ad_group_source.id,
        repr(date)
    )
    logger.debug(msg)

    action = models.ActionLog(
        action=constants.Action.FETCH_REPORTS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
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
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save(request)

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing get_reports action')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _init_fetch_reports_by_publisher(ad_group_source, date, order, request=None):
    if not ad_group_source.source.can_fetch_report_by_publisher():
        logger.error('Trying to _init_fetch_reports_by_publisher() on source that does not support it: {}'.format(ad_group_source.id))
        raise exceptions.InsertActionException('Trying to _init_fetch_reports_by_publisher() on source that does not support it: {}'.format(ad_group_source.id))

    msg = '_init_fetch_reports started: ad_group_source.id: {}, date: {}'.format(
        ad_group_source.id,
        repr(date)
    )
    logger.debug(msg)

    action = models.ActionLog(
        action=constants.Action.FETCH_REPORTS_BY_PUBLISHER,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order,
        expiration_dt=datetime.utcnow() + timedelta(hours=3)
    )
    action.save(request)

    try:
        with transaction.atomic():
            callback = utils.url_helper.get_zwei_callback_url(action.id)

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save(request)

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing get_reports action')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _init_create_campaign(ad_group_source, name, request):
    if ad_group_source.source_campaign_key and \
            ad_group_source.source_campaign_key != settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE:
        msg = u'Unable to create external campaign for AdGroupSource with existing connection'\
              'ad_group_source.id={ad_group_source_id}, name={name}'.format(
                  ad_group_source_id=ad_group_source.id,
                  name=name,
              )
        logger.error(msg)

        raise exceptions.InsertCreateCampaignActionException(msg)

    msg = u"_init_create_campaign started: ad_group_source.id: {}, name: {}".format(
        ad_group_source.id,
        name,
    )
    logger.info(msg)

    order = models.ActionLogOrder.objects.create(
        order_type=constants.ActionLogOrderType.CREATE_CAMPAIGN
    )

    action = models.ActionLog(
        action=constants.Action.CREATE_CAMPAIGN,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )
    action.save(request)

    ad_group_settings = ad_group_source.ad_group.get_current_settings()
    campaign_settings = _get_campaign_settings(ad_group_source.ad_group.campaign)

    try:
        with transaction.atomic():
            callback = utils.url_helper.get_zwei_callback_url(action.id)

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'args': {
                    'name': name,
                    'extra': {},
                },
                'callback_url': callback,
            }

            if ad_group_source.source.source_type.type == dash.constants.SourceType.OUTBRAIN:
                payload['args']['marketer_id'] = _get_outbrain_marketer_id(
                    ad_group_source.ad_group.campaign.account,
                    request
                )

            if ad_group_source.source.source_type.type == dash.constants.SourceType.B1:
                payload['args']['extra']['ad_group_id'] = ad_group_source.ad_group.id
                payload['args']['extra']['exchange'] = ad_group_source.source.bidder_slug

            if ad_group_source.source.source_type.type == dash.constants.SourceType.GRAVITY:
                payload['args']['extra']['ad_group_id'] = ad_group_source.ad_group.id

                if request and request.user:
                    payload['args']['extra']['user_email'] = request.user.email

            if hasattr(ad_group_source.source, 'defaultsourcesettings'):
                params = ad_group_source.source.defaultsourcesettings.params
                if 'create_campaign' in params:
                    payload['args']['extra'].update(params['create_campaign'])

            ad_group_tracking_codes = None
            if ad_group_settings:
                payload['args']['extra'].update({
                    'target_devices': ad_group_settings.target_devices,
                    'target_regions': ad_group_settings.target_regions,
                    'retargeting_ad_groups': ad_group_settings.retargeting_ad_groups,
                    'brand_name': ad_group_settings.brand_name,
                    'display_url': ad_group_settings.display_url,
                    'start_date': ad_group_settings.start_date,
                    'end_date': ad_group_settings.end_date,
                })
                ad_group_tracking_codes = ad_group_settings.get_tracking_codes()


            # tracking code should always be ad group settings first, ad group source ids second
            payload['args']['extra'].update({
                'tracking_code': utils.url_helper.combine_tracking_codes(
                    ad_group_tracking_codes,
                    ''
                ),
                'tracking_slug': ad_group_source.source.tracking_slug
            })

            if campaign_settings:
                payload['args']['extra'].update({
                    'iab_category': campaign_settings.iab_category,
                })

            action.payload = payload
            action.save(request)

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing create_campaign action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


@transaction.atomic()
def _get_outbrain_marketer_id(account, request):
    if account.outbrain_marketer_id:
        return account.outbrain_marketer_id

    try:
        outbrain_account = dash.models.OutbrainAccount.objects.\
            filter(used=False).order_by('created_dt')[0]
    except IndexError:
        raise Exception('No unused Outbrain accounts available.')

    outbrain_account.used = True
    outbrain_account.save()

    account.outbrain_marketer_id = outbrain_account.marketer_id
    account.save(request)

    return account.outbrain_marketer_id
