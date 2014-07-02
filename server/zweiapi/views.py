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
    _process_zwei_response(action, data)

    response_data = {'status': 'OK'}
    return JsonResponse(response_data)


@transaction.atomic
def _process_zwei_response(action, data):
    logger.info('Processing Action Response: %s, response: %s', action, data)

    if action.state != actionlogconstants.ActionState.WAITING:
        logger.warning('Action not waiting for a response. Action: %s, response: %s', action, data)
        return

    if data['status'] != 'success':
        action.state = actionlogconstants.ActionState.FAILED
        action.save()
        return

    if action.action == actionlogconstants.Action.FETCH_REPORTS:
        date = action.payload['args']['date']
        reportsapi.upsert(data['data'], date)
    elif action.action == actionlogconstants.Action.FETCH_CAMPAIGN_STATUS:
        dashapi.campaign_status_upsert(action.ad_group_network, data['data'])
    elif action.action == actionlogconstants.Action.FETCH_CAMPAIGN_STATUS:
        raise NotImplementedError

    action.state = actionlogconstants.ActionState.SUCCESS
    action.save()
