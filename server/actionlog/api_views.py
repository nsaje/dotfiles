import json

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from . import models
from . import constants


@csrf_exempt
def zwei_callback(request, action_id):
    try:
        action = models.ActionLog(id=action_id)
    except ObjectDoesNotExist:
        raise Exception('Invalid action_id in callback')

    data = json.loads(request.body)
    _process_zwei_response(action, data)

    response_data = {'status': 'OK'}
    return JsonResponse(response_data)


@transaction.atomic
def _process_zwei_response(action, data):
    if data['status'] != 'success':
        action.status = constants.ActionStatus.FAILED
        action.save()

    if action.type == constants.ActionType.FETCH_REPORTS:
        # TODO call reports handling function when available
        return NotImplementedError
    elif action.type == constants.ActionType.FETCH_CAMPAIGN_STATUS:
        # TODO call campaign status save function
        return NotImplementedError

    action.status = constants.ActionStatus.SUCCESS
    action.save()
