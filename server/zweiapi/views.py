import json
import logging
import traceback

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from django.conf import settings

from utils import request_signer
from actionlog import models as actionlogmodels
from actionlog import constants as actionlogconstants
from dash import api as dashapi

import actionlog.sync
import reports.update


logger = logging.getLogger(__name__)


@csrf_exempt
def zwei_callback(request, action_id):
    try:
        request_signer.verify_wsgi_request(request, settings.ZWEI_API_SIGN_KEY)
    except request_signer.SignatureError as e:
        logger.exception('Invalid zwei callback signature.')

        msg = 'Zwei callback failed for action: %s. Error: %s'
        logger.error(msg, action_id, repr(e.message))

    try:
        action = actionlogmodels.ActionLog.objects.get(id=action_id)
    except ObjectDoesNotExist:
        raise Exception('Invalid action_id in callback')

    data = json.loads(request.body)
    try:
        _process_zwei_response(action, data)

        if action.order and action.order.order_type in actionlogconstants.ActionLogOrderType.get_sync_types():
            action.ad_group_source.last_successful_sync_dt = \
                actionlog.sync.AdGroupSourceSync(action.ad_group_source).get_latest_success()
            action.ad_group_source.save()
    except Exception as e:
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

        action.state = actionlogconstants.ActionState.FAILED
        action.message = msg % args
        action.save()

    response_data = {'status': 'OK'}
    return JsonResponse(response_data)


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


def _prepare_report_row(ad_group):
    def _inner(row):
        r = {
            'article': dashapi.reconcile_article(row['url'], row['title'], ad_group),
            'impressions': row['impressions'],
            'clicks': row['clicks'],
        }
        if row.get('cost_cc') is None:
            r['cost_cc'] = row['cpc_cc'] * row['clicks']
        else:
            r['cost_cc'] = row['cost_cc']
        return r
    return _inner


@transaction.atomic
def _process_zwei_response(action, data):
    logger.info('Processing Action Response: %s', action)

    if action.state != actionlogconstants.ActionState.WAITING:
        logger.warning('Action not waiting for a response. Action: %s, response: %s', action, data)
        return

    if data['status'] != 'success':
        logger.warning('Action failed. Action: %s, response: %s', action, data)

        action.state = actionlogconstants.ActionState.FAILED
        action.message = _get_error_message(data)
        action.save()

        return

    if action.action == actionlogconstants.Action.FETCH_REPORTS:
        date = action.payload['args']['date']
        ad_group = action.ad_group_source.ad_group
        source = action.ad_group_source.source

        for source_campaign_key, data_rows in data['data']:
            if source_campaign_key == action.ad_group_source.source_campaign_key:
                rows = map(_prepare_report_row(ad_group), data_rows)
                break
        else:
            raise Exception('Source campaign key not in results.')

        reports.update.stats_update_adgroup_source_traffic(date, ad_group, source, rows)
    elif action.action == actionlogconstants.Action.FETCH_CAMPAIGN_STATUS:
        dashapi.campaign_status_upsert(action.ad_group_source, data['data'])
    elif action.action == actionlogconstants.Action.SET_CAMPAIGN_STATE:
        state = action.payload['args']['conf']['state']
        dashapi.update_campaign_state(action.ad_group_source, state)
    elif action.action == actionlogconstants.Action.CREATE_CAMPAIGN:
        dashapi.update_campaign_key(action.ad_group_source, data['data']['source_campaign_key'])

    action.state = actionlogconstants.ActionState.SUCCESS
    action.save()
