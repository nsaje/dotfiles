import json
import logging

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from actionlog import models as actionlogmodels
from actionlog import constants as actionlogconstants

from reports import api as reportsapi
from dash import api as dashapi

logger = logging.getLogger(__name__)


@csrf_exempt
def zwei_callback(request, action_id):
    try:
        action = actionlogmodels.ActionLog.objects.get(id=action_id)
    except ObjectDoesNotExist:
        raise Exception('Invalid action_id in callback')

    data = json.loads(request.body)
    try:
        _process_zwei_response(action, data)
    except Exception as e:
        msg = 'Zwei callback failed for action: {action_id}. Error: {error}, message: {message}'\
              .format(action_id=action.id, error=e.__class_.__name__, message=repr(e.message))
        logger.warning(msg)

        action.state = actionlogconstants.ActionState.FAILED
        action.message = msg
        action.save()

    response_data = {'status': 'OK'}
    return JsonResponse(response_data)


def _get_error_message(data):
    if not data.get('error'):
        return ''

    message = []
    if data['error'].get('error'):
        message.append(data['error']['error'])
    if data['error'].get('message'):
        message.append(data['error']['message'])
    if data['error'].get('traceback'):
        message.append(data['error']['traceback'])

    return '\n'.join(message)


@transaction.atomic
def _process_zwei_response(action, data):
    logger.info('Processing Action Response: %s, response: %s', action, data)

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
        for entry in data['data']:
            if entry[0] == action.ad_group_network.network_campaign_key:
                rows = entry[1]
                break
        else:
            raise Exception('Network campaign key not in results.')
        date = action.payload['args']['date']
        reportsapi.upsert_report(action.ad_group_network, rows, date)
    elif action.action == actionlogconstants.Action.FETCH_CAMPAIGN_STATUS:
        dashapi.campaign_status_upsert(action.ad_group_network, data['data'])

    action.state = actionlogconstants.ActionState.SUCCESS
    action.save()
