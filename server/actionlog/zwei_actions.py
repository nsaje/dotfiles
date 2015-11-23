import copy
import json
import logging
import traceback
import urllib2
import datetime

from django.conf import settings

from actionlog import constants
from utils import json_helper
from utils import request_signer

logger = logging.getLogger(__name__)


MAX_ACTIONS_IN_BATCH = 200


def _handle_error(action, e):
    msg = traceback.format_exc(e)

    logger.error(msg)

    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save()


def resend(actions):
    if not isinstance(actions, list) and not isinstance(actions, tuple):
        actions = [actions]

    if not all(action.state == constants.ActionState.FAILED for action in actions):
        raise AssertionError('Not all selected actions have failed!')

    modified_date = datetime.datetime.utcnow()
    expiration_date = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    for action in actions:
        action.payload['expiration_dt'] = expiration_date.isoformat()

        if action.action == constants.Action.INSERT_CONTENT_AD:
            action.payload['args']['content_ad']['check_already_inserted'] = True

        action.modified_dt = modified_date
        action.state = constants.ActionState.WAITING
        action.expiration_dt = expiration_date
        action.save()

    send(actions)


def send(actions):
    if not isinstance(actions, list) and not isinstance(actions, tuple):
        actions = [actions]

    credentials_lookup = {}

    for i in range(0, len(actions), MAX_ACTIONS_IN_BATCH):
        actions_batch = actions[i:i+MAX_ACTIONS_IN_BATCH]
        try:
            data = []
            for action in actions_batch:
                if action.ad_group_source_id not in credentials_lookup and\
                   action.ad_group_source.source_credentials.credentials:
                    credentials_lookup[action.ad_group_source_id] = action.ad_group_source.source_credentials.decrypt()
                payload = copy.deepcopy(action.payload)
                payload['credentials'] = credentials_lookup.get(action.ad_group_source_id) or ''
                data.append(payload)

            request = urllib2.Request(settings.ZWEI_API_TASKS_URL, json.dumps(data, cls=json_helper.JSONEncoder))
            request_signer.urllib2_secure_open(request, settings.ZWEI_API_SIGN_KEY)
        except Exception as e:
            for action in actions_batch:
                _handle_error(action, e)


def get_supply_dash_url(source_type, credentials, source_campaign_key):
    try:
        payload = {
            'source': source_type,
            'credentials': credentials,
            'args': {
                'source_campaign_key': source_campaign_key
            }
        }
        data = json.dumps(payload, cls=json_helper.JSONEncoder)
        request = urllib2.Request(settings.ZWEI_API_GET_DASH_URL_URL, data)

        response = request_signer.urllib2_secure_open(
            request, settings.ZWEI_API_SIGN_KEY)
        return json.loads(response.read())
    except Exception as e:
        msg = traceback.format_exc(e)
        logger.error(msg)
