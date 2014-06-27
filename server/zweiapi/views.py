import json
import logging

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from actionlog import models as actionlogmodels
from actionlog import constants as actionlogconstants

from reports import api as reportsapi

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
    import ipdb; ipdb.set_trace();
    if action.action_status != actionlogconstants.ActionStatus.WAITING:
        logger.warning('Action not waiting for a response. Action: %s, data: %s', action, data)
        return

    if data['status'] != 'success':
        action.action_status = actionlogconstants.ActionStatus.FAILED
        action.save()
        return

    if action.action_type == actionlogconstants.ActionType.FETCH_REPORTS:
        reportsapi.upsert(data, action.ad_group, action.network)
    elif action.action_type == actionlogconstants.ActionType.FETCH_CAMPAIGN_STATUS:
        # TODO call campaign status save function
        return NotImplementedError

    action.status = actionlogconstants.ActionStatus.SUCCESS
    action.save()
