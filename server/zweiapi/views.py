import json
import logging
import traceback

import hashlib
from django.core.cache import cache

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from django.conf import settings

import actionlog.models
import actionlog.constants
import actionlog.sync
import dash.api
import reports.update

from utils import request_signer
from utils import statsd_helper

logger = logging.getLogger(__name__)


@csrf_exempt
def zwei_callback(request, action_id):
    logger.info('Received zwei callback: %s', action_id)

    _validate_callback(request, action_id)
    action = _get_action(action_id)

    data = json.loads(request.body)
    try:
        _process_zwei_response(action, data, request)
        _update_last_successful_sync_dt(action, request)
    except Exception as e:
        _handle_zwei_callback_error(e, action)

    response_data = {'status': 'OK'}
    return JsonResponse(response_data)


def _update_last_successful_sync_dt(action, request):
    if not action.order or action.state == actionlog.constants.ActionState.FAILED:
        return

    status_sync_dt = None
    report_sync_dt = None

    if (action.order.order_type == actionlog.constants.ActionLogOrderType.FETCH_REPORTS and
        all(a.state == actionlog.constants.ActionState.SUCCESS
            for a in actionlog.models.ActionLog.objects.filter(order=action.order))):
        report_sync_dt = action.order.created_dt
        status_sync_dt = actionlog.sync.AdGroupSourceSync(
            action.ad_group_source).get_latest_status_sync()

    elif action.order.order_type == actionlog.constants.ActionLogOrderType.FETCH_STATUS:
        report_sync_dt = actionlog.sync.AdGroupSourceSync(
            action.ad_group_source).get_latest_report_sync()
        status_sync_dt = action.order.created_dt

    if status_sync_dt is None or report_sync_dt is None:
        return

    action.ad_group_source.last_successful_sync_dt = min(status_sync_dt, report_sync_dt)
    action.ad_group_source.save(request)


def _get_error_message(data):
    message = []
    if data.get('error', {}).get('error'):
        message.append(data['error']['error'])
    if data.get('error', {}).get('message'):
        message.append(data['error']['message'])
    if data.get('error', {}).get('traceback'):
        message.append(data['error']['traceback'])
    if data.get('message'):
        message.append(data['message'])

    return '\n'.join(message)


def _prepare_report_rows(ad_group, data_rows):
    raw_articles = [{'url': row['url'], 'title': row['title']} for row in data_rows]
    articles = dash.api.reconcile_articles(ad_group, raw_articles)

    if not len(articles) == len(data_rows):
        raise Exception('Not all articles were reconciled')

    stats_rows = []
    for article, data_row in zip(articles, data_rows):
        r = {
            'article': article,
            'impressions': data_row['impressions'],
            'clicks': data_row['clicks'],
            'data_cost_cc': data_row.get('data_cost_cc') or 0
        }
        if data_row.get('cost_cc') is None:
            r['cost_cc'] = data_row['cpc_cc'] * data_row['clicks']
        else:
            r['cost_cc'] = data_row['cost_cc']

        stats_rows.append(r)
    return stats_rows


@transaction.atomic
def _process_zwei_response(action, data, request):
    logger.info('Processing Action Response: %s', action)

    if action.state != actionlog.constants.ActionState.WAITING:
        logger.warning('Action not waiting for a response. Action: %s, response: %s', action, data)
        return

    if data['status'] != 'success':
        logger.warning('Action failed. Action: %s, response: %s', action, data)

        action.state = actionlog.constants.ActionState.FAILED
        action.message = _get_error_message(data)
        action.save()

        return

    action.state = actionlog.constants.ActionState.SUCCESS
    if action.action == actionlog.constants.Action.FETCH_REPORTS:
        date = action.payload['args']['date']
        ad_group = action.ad_group_source.ad_group
        source = action.ad_group_source.source

        if _has_changed(data, ad_group, source, date):
            rows = _prepare_report_rows(ad_group, data['data'])
            valid = reports.update.is_traffic_update_valid(date, ad_group, source, rows)

            if valid:
                reports.update.stats_update_adgroup_source_traffic(date, ad_group, source, rows)
                if source.source_type.can_manage_content_ads():
                    reports.update.update_content_ads_source_traffic_stats(date, ad_group, source, data['data'])
            else:
                msg = 'Update of source traffic for adgroup %d, source %d, datetime %s skipped due to report not valid.'

                action.state = actionlog.constants.ActionState.FAILED
                action.message = msg.format(
                    ad_group.id, source.id, date
                )

                statsd_helper.statsd_incr('reports.update.update_traffic_metrics_skipped')
                statsd_helper.statsd_incr(
                    'reports.update.update_traffic_metrics_skipped.%s' % (source.source_type.type)
                )

                logger.warning(msg, ad_group.id, source.id, date)

    elif action.action == actionlog.constants.Action.FETCH_CAMPAIGN_STATUS:
        dash.api.update_ad_group_source_state(action.ad_group_source, data['data'])

    elif action.action == actionlog.constants.Action.SET_CAMPAIGN_STATE:
        ad_group_source = action.ad_group_source
        conf = action.payload['args']['conf']

        dash.api.update_ad_group_source_state(ad_group_source, conf)
    elif action.action == actionlog.constants.Action.CREATE_CAMPAIGN:
        dash.api.update_campaign_key(
            action.ad_group_source,
            data['data']['source_campaign_key'],
            request
        )
        dash.api.add_content_ad_sources(action.ad_group_source)
    elif action.action == actionlog.constants.Action.INSERT_CONTENT_AD:
        if 'source_content_ad_id' in data['data']:
            dash.api.insert_content_ad_callback(
                action.ad_group_source,
                action.content_ad_source,
                data['data'].get('source_content_ad_id'),
                data['data'].get('source_state'),
                data['data'].get('submission_status'),
                data['data'].get('submission_errors')
            )
    elif action.action == actionlog.constants.Action.UPDATE_CONTENT_AD:
        dash.api.update_content_ad_source_state(
            action.content_ad_source,
            data['data']
        )
    elif action.action == actionlog.constants.Action.GET_CONTENT_AD_STATUS:
        dash.api.update_multiple_content_ad_source_states(
            action.ad_group_source,
            data['data']
        )

    logger.info('Process action successful. Action: %s', action)
    action.save()

    if action.action in actionlog.models.DELAYED_ACTIONS:
        actionlog.api.send_delayed_actionlogs([ad_group_source])


def _has_changed(data, ad_group, source, date):
    if not settings.USE_HASH_CACHE:
        # treat everything as new data
        return True

    md5_hash = hashlib.md5()
    md5_hash.update(json.dumps(data['data']))

    val = md5_hash.hexdigest()
    key = 'fetch_reports_response_hash_{}_{}_{}'.format(ad_group.id, source.id, date)

    old_val = cache.get(key)
    if old_val is None or val != old_val:
        logger.info('Reports data has changed since last sync for ad group: {}, source: {}, date: {}'.format(
            ad_group.id, source.id, date))

        cache.set(key, val, settings.HASH_CACHE_TTL)
        return True

    return False


def _handle_zwei_callback_error(e, action):
    tb = traceback.format_exc()
    msg = 'Zwei callback failed for action: %(action_id)s. Error: %(error)s, message: %(message)s.'
    args = {
        'action_id': action.id,
        'error': e.__class__.__name__,
        'message': repr(e.message)
    }
    logger.exception(msg, args)

    msg += '\n\nTraceback: %(traceback)s'
    args.update({'traceback': tb})

    action.state = actionlog.constants.ActionState.FAILED
    action.message = msg % args
    action.save()


def _validate_callback(request, action_id):
    '''
    if the request is not valid this raises an exception
    '''
    try:
        request_signer.verify_wsgi_request(request, settings.ZWEI_API_SIGN_KEY)
    except request_signer.SignatureError as e:
        logger.exception('Invalid zwei callback signature.')

        msg = 'Zwei callback failed for action: %s. Error: %s'
        logger.error(msg, action_id, repr(e.message))


def _get_action(action_id):
    try:
        action = actionlog.models.ActionLog.objects.get(id=action_id)
        return action
    except ObjectDoesNotExist:
        raise Exception('Invalid action_id in callback')
