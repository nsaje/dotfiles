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
from reports import api as reportsapi
from dash import api as dashapi


logger = logging.getLogger(__name__)


@csrf_exempt
def zwei_callback(request, action_id):
    try:
        request_signer.verify_wsgi_request(request, settings.ZWEI_API_SIGN_KEY)
    except request_signer.SignatureError as e:
        logger.exception('Invalid zwei callback signature.')

        msg = 'Zwei callback failed for action: {action_id}. Error: {error}'.format(
            action_id=action_id, error=repr(e.message)
        )
        logger.error(msg)

    try:
        action = actionlogmodels.ActionLog.objects.get(id=action_id)
    except ObjectDoesNotExist:
        raise Exception('Invalid action_id in callback')

    data = json.loads(request.body)
    try:
        _process_zwei_response(action, data)
    except Exception as e:
        tb = traceback.format_exc()
        msg = 'Zwei callback failed for action: {action_id}. Error: {error}, message: {message}.'\
              '\n\nTraceback: {traceback}'\
              .format(action_id=action.id, error=e.__class__.__name__, message=repr(e.message), traceback=tb)
        logger.error(msg)

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
    if data.get('message'):
        message.append(data['message'])

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
        for source_campaign_key, data_rows in data['data']:
            if source_campaign_key == action.ad_group_source.source_campaign_key:
                rows = data_rows
                break
        else:
            raise Exception('Source campaign key not in results.')
        date = action.payload['args']['date']
        ad_group = action.ad_group_source.ad_group
        source = action.ad_group_source.source
        reportsapi.save_report(ad_group, source, rows, date)
    elif action.action == actionlogconstants.Action.FETCH_CAMPAIGN_STATUS:
        dashapi.campaign_status_upsert(action.ad_group_source, data['data'])
    elif action.action == actionlogconstants.Action.SET_CAMPAIGN_STATE:
        state = action.payload['args']['state']
        dashapi.update_campaign_state(action.ad_group_source, state)
    elif action.action == actionlogconstants.Action.CREATE_CAMPAIGN:
        dashapi.update_campaign_key(action.ad_group_source, data['data']['source_campaign_key'])

    action.state = actionlogconstants.ActionState.SUCCESS
    action.save()
