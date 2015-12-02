import json
import logging
import traceback
import datetime

import hashlib
from django.core.cache import cache

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from django.conf import settings

import newrelic.agent

import actionlog.models
import actionlog.constants
import actionlog.sync
import actionlog.zwei_actions

import dash.api
import dash.models
import reports.refresh
import reports.update
import reports.api_publishers
import reports.daily_statements
from reports.api import get_day_cost

from utils import request_signer
from utils import statsd_helper

logger = logging.getLogger(__name__)


@csrf_exempt
@statsd_helper.statsd_timer('zweiapi.views', 'zwei_callback')
def zwei_callback(request, action_id):
    newrelic.agent.set_background_task(flag=True)
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

    ad_group_source = action.ad_group_source
    if (action.order.order_type == actionlog.constants.ActionLogOrderType.FETCH_REPORTS and
        all(a.state == actionlog.constants.ActionState.SUCCESS
            for a in actionlog.models.ActionLog.objects.filter(order=action.order))):
        if ad_group_source.last_successful_reports_sync_dt != action.order.created_dt:
            ad_group_source.last_successful_reports_sync_dt = action.order.created_dt
            ad_group_source.save(update_fields=['last_successful_reports_sync_dt'])

    elif action.order.order_type == actionlog.constants.ActionLogOrderType.FETCH_STATUS:
        ad_group_source.last_successful_status_sync_dt = action.order.created_dt
        ad_group_source.save(update_fields=['last_successful_status_sync_dt'])

    ad_group_source = dash.models.AdGroupSource.objects.get(id=ad_group_source.id)
    if ad_group_source.last_successful_status_sync_dt is None or\
       ad_group_source.last_successful_reports_sync_dt is None:
        return

    ad_group_source.last_successful_sync_dt = min(ad_group_source.last_successful_status_sync_dt,
                                                  ad_group_source.last_successful_reports_sync_dt)
    ad_group_source.save()


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


def _prepare_report_rows(ad_group, source, data_rows):
    raw_articles = [{'url': row['url'], 'title': row['title']} for row in data_rows]
    articles = dash.api.reconcile_articles(ad_group, raw_articles)

    if not len(articles) == len(data_rows):
        raise Exception('Not all articles were reconciled')

    content_ad_sources = {}
    for content_ad_source in dash.models.ContentAdSource.objects.filter(
            content_ad__ad_group=ad_group,
            source=source):
        content_ad_sources[content_ad_source.get_source_id()] = content_ad_source

    stats_rows = []
    for article, data_row in zip(articles, data_rows):
        if 'id' not in data_row:
            statsd_helper.statsd_incr('reports.update.err_content_ad_no_id')
            raise Exception('\'id\' field not present in data row.')

        if data_row['id'] not in content_ad_sources:
            statsd_helper.statsd_incr('reports.update.err_unknown_content_ad_id')
            raise Exception('Stats for an unknown id. ad group={}. source={}. id={}.'.format(
                ad_group.id,
                source.id,
                data_row['id']
            ))

        stats_rows.append({
            'id': data_row['id'],
            'article': article,
            'impressions': data_row['impressions'],
            'clicks': data_row['clicks'],
            'data_cost_cc': data_row.get('data_cost_cc') or 0,
            'cost_cc': data_row['cost_cc'],
            'content_ad_source': content_ad_sources[data_row['id']],
        })

    return stats_rows


def _remove_content_ad_sources_from_report_rows(report_rows):
    ignored_keys = ('content_ad_source', 'id')
    return [{k: v for k, v in row.items() if k not in ignored_keys} for row in report_rows]


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

    actions = []
    with transaction.atomic():
        action.state = actionlog.constants.ActionState.SUCCESS
        action.save()

        if action.action == actionlog.constants.Action.FETCH_REPORTS:
            _fetch_reports_callback(action, data)

        elif action.action == actionlog.constants.Action.FETCH_REPORTS_BY_PUBLISHER:
            _fetch_reports_by_publisher_callback(action, data)

        elif action.action == actionlog.constants.Action.FETCH_CAMPAIGN_STATUS:
            dash.api.update_ad_group_source_state(action.ad_group_source, data['data'])

        elif action.action == actionlog.constants.Action.SET_CAMPAIGN_STATE:
            ad_group_source = action.ad_group_source
            conf = action.payload['args']['conf']

            dash.api.update_ad_group_source_state(ad_group_source, conf)
            actions.extend(actionlog.api.send_delayed_actionlogs([ad_group_source], send=False))

        elif action.action == actionlog.constants.Action.SET_PUBLISHER_BLACKLIST:
            args = action.payload['args']
            dash.api.update_publisher_blacklist_state(args)

        elif action.action == actionlog.constants.Action.CREATE_CAMPAIGN:
            dash.api.create_campaign_callback(
                action.ad_group_source,
                data['data']['source_campaign_key'],
                request
            )

            logger.info('Submitting content ads after campaign creation. Action %s', action)
            content_ad_sources = dash.api.add_content_ad_sources(action.ad_group_source)
            actions.extend(dash.api.submit_content_ads(content_ad_sources, request=None))

            logger.info('Ordering additional updates after campaign creation. Action %s', action)
            dash.api.order_additional_updates_after_campaign_creation(action.ad_group_source,
                                                                      request=None)

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
            actions.extend(
                dash.api.update_multiple_content_ad_source_states(
                    action.ad_group_source,
                    data['data']
                )
            )

        elif action.action == actionlog.constants.Action.SUBMIT_AD_GROUP:
            actions.extend(
                dash.api.submit_ad_group_callback(
                    action.ad_group_source,
                    data['data']['source_content_ad_id'],
                    data['data']['submission_status'],
                    data['data']['submission_errors'],
                )
            )

        logger.info('Process action successful. Action: %s', action)

    actionlog.zwei_actions.send(actions)


def _get_reports_cache_key_val(data, ad_group, source, date, key_type):
    md5_hash = hashlib.md5()
    md5_hash.update(json.dumps(data['data']))

    val = md5_hash.hexdigest()
    key = 'fetch_reports_response_hash_{}_{}_{}_{}'.format(ad_group.id, source.id, date, key_type)

    return key, val


def _has_changed(data, ad_group, source, date, key_type):
    if not settings.USE_HASH_CACHE:
        # treat everything as new data
        return True

    key, val = _get_reports_cache_key_val(data, ad_group, source, date, key_type)
    old_val = cache.get(key)

    if old_val is None or val != old_val:
        logger.info('Change of data for ad group: {}, source: {}, date: {}, key type {}'.format(
            ad_group.id, source.id, date, key_type))
        logger.info("Old key {}, new key {}".format(old_val, val))

        return True

    return False


def _set_reports_cache(data, ad_group, source, date, key_type):
    if not settings.USE_HASH_CACHE:
        return

    key, val = _get_reports_cache_key_val(data, ad_group, source, date, key_type)
    cache.set(key, val, settings.HASH_CACHE_TTL)


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


def _fetch_reports_callback(action, data):
    date = action.payload['args']['date']
    ad_group = action.ad_group_source.ad_group
    source = action.ad_group_source.source

    logger.info('_fetch_reports_callback: Processing reports callback for adgroup {adgroup_id}  source {source_id}'.format(
        adgroup_id=ad_group.id, source_id=source.id if source is not None else 0)
    )

    traffic_metrics_exist = reports.api.traffic_metrics_exist(ad_group, source, date)
    rows_raw = data['data']

    valid_response = True
    empty_response = False

    if traffic_metrics_exist and len(rows_raw) == 0:
        empty_response = True
        if not reports.api.can_delete_traffic_metrics(ad_group, source, date):
            valid_response = False

    # centralize in order to reduce possibility of mistake
    change_unique_key = "reports_by_link"

    if not _has_changed(data, ad_group, source, date, change_unique_key):
        logger.info('_fetch_reports_callback: no changes adgroup {adgroup_id}  source {source_id}'.format(
            adgroup_id=ad_group.id, source_id=source.id if source is not None else 0)
        )

    if valid_response and _has_changed(data, ad_group, source, date, change_unique_key):
        rows = _prepare_report_rows(ad_group, source, data['data'])
        article_rows = _remove_content_ad_sources_from_report_rows(rows)

        reports.update.stats_update_adgroup_source_traffic(date, ad_group, source, article_rows)
        reports.update.update_content_ads_source_traffic_stats(date, ad_group, source, rows)

        # set cache only after everything has updated successfully
        _set_reports_cache(data, ad_group, source, date, change_unique_key)

    if not valid_response:
        msg = 'Update of source traffic for adgroup %d, source %d, datetime '\
              '%s skipped due to report not being valid (empty response).'

        action.state = actionlog.constants.ActionState.FAILED
        action.message = msg % (ad_group.id, source.id, date)
        action.save()

        logger.warning(msg, ad_group.id, source.id, date)

    if empty_response:
        logger.warning(
            'Empty report received for adgroup %d, source %d, datetime %s',
            ad_group.id,
            source.id,
            date
        )
        statsd_helper.statsd_incr('reports.update.update_traffic_metrics_skipped')
        statsd_helper.statsd_incr(
            'reports.update.update_traffic_metrics_skipped.%s' % (source.source_type.type)
        )


def _fetch_reports_by_publisher_callback(action, data):
    date_str = action.payload['args']['date']
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    ad_group = action.ad_group_source.ad_group
    source = action.ad_group_source.source

    rows_raw = data['data']

    valid_response = True
    empty_response = False

    # centralize in order to reduce possibility of mistakes, if you want everything to run again, just increase the number
    change_unique_key = "reports_by_publisher_2"

    if valid_response:  # and _has_changed(data, ad_group, source, date, change_unique_key):
        ret = get_day_cost(date, ad_group=ad_group, source=source)
        cost = ret['cost']
        if cost is None:
            cost = 0

        reports.api_publishers.ob_insert_adgroup_date(date,
                                                      ad_group.id,
                                                      "Outbrain",  # Hardcoding this at the time, the problem is that source.name can change
                                                      rows_raw,
                                                      cost)
        _set_reports_cache(data, ad_group, source, date, change_unique_key)

    if not valid_response:
        msg = 'Update of publishers for adgroup %d, source %d, datetime '\
              '%s skipped due to report not being valid (empty response).'

        action.state = actionlog.constants.ActionState.FAILED
        action.message = msg % (ad_group.id, source.id, date)
        action.save()

        logger.warning(msg, ad_group.id, source.id, date)

    if empty_response:
        logger.warning(
            'Empty report received for adgroup %d, source %d, datetime %s',
            ad_group.id,
            source.id,
            date
        )
        statsd_helper.statsd_incr('reports.update.update_traffic_metrics_skipped')
        statsd_helper.statsd_incr(
            'reports.update.update_traffic_metrics_skipped.%s' % (source.source_type.type)
        )
