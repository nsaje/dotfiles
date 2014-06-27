import json
import logging

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from . import models
from . import constants

from reports import api as reportsapi

logger = logging.getLogger(__name__)


@csrf_exempt
def zwei_callback(request, action_id):
    try:
        action = models.ActionLog.objects.get(id=action_id)
    except ObjectDoesNotExist:
        raise Exception('Invalid action_id in callback')

    data = json.loads(request.body)
    _process_zwei_response(action, data)

    response_data = {'status': 'OK'}
    return JsonResponse(response_data)


@transaction.atomic
def _process_zwei_response(action, data):
    if action.action_status != constants.ActionStatus.WAITING:
        logger.warning('Action not waiting for a response. Action: %s, data: %s', action, data)
        return

    if data['status'] != 'success':
        action.action_status = constants.ActionStatus.FAILED
        action.save()
        return

    if action.action_type == constants.ActionType.FETCH_REPORTS:
        reportsapi.upsert(data, action.ad_group, action.network)
    elif action.action_type == constants.ActionType.FETCH_CAMPAIGN_STATUS:
        # TODO call campaign status save function
        return NotImplementedError

    action.status = constants.ActionStatus.SUCCESS
    action.save()
