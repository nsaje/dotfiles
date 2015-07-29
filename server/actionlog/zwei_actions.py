import binascii
import copy
import json
import logging
import traceback
import urllib2

from django.conf import settings

from actionlog import constants
from utils import encryption_helpers
from utils import json_helper
from utils import request_signer

logger = logging.getLogger(__name__)


def _handle_error(action, e):
    msg = traceback.format_exc(e)

    logger.error(msg)

    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save()


def _decrypt_payload_credentials(payload):
    # Decrypt has to be the last thing to happen before sending to zwei.
    # Payload with decrypted credentials should never be logged.
    payload = copy.deepcopy(payload)
    if not payload.get('credentials'):
        return payload

    payload['credentials'] = json.loads(
        encryption_helpers.aes_decrypt(
            binascii.a2b_base64(
                payload['credentials']
            ),
            settings.CREDENTIALS_ENCRYPTION_KEY
        )
    )

    return payload


def send(action):
    try:
        payload = _decrypt_payload_credentials(action.payload)
        data = json.dumps(payload, cls=json_helper.JSONEncoder)
        request = urllib2.Request(settings.ZWEI_API_URL, data)
        request_signer.urllib2_secure_open(request, settings.ZWEI_API_SIGN_KEY)
    except Exception as e:
        _handle_error(action, e)


def send_multiple(actionlogs):
    try:
        data = []
        for action in actionlogs:
            data.append(_decrypt_payload_credentials(action.payload))

        request = urllib2.Request(settings.ZWEI_API_BATCH_URL, json.dumps(data, cls=json_helper.JSONEncoder))
        request_signer.urllib2_secure_open(request, settings.ZWEI_API_SIGN_KEY)
    except Exception as e:
        for action in actionlogs:
            _handle_error(action, e)


def get_supply_dash_url(source_type, credentials, source_campaign_key):
    try:
        # Decrypt has to be the last thing to happen before sending to zwei.
        # Payload with decrypted credentials should never be logged.
        enc_payload = {
            'source': source_type,
            'credentials': credentials,
            'args': {
                'source_campaign_key': source_campaign_key
            }
        }
        payload = _decrypt_payload_credentials(enc_payload)
        data = json.dumps(payload, cls=json_helper.JSONEncoder)
        request = urllib2.Request(settings.ZWEI_API_GET_DASH_URL_URL, data)

        response = request_signer.urllib2_secure_open(
            request, settings.ZWEI_API_SIGN_KEY)
        return json.loads(response.read())
    except Exception as e:
        msg = traceback.format_exc(e)
        logger.error(msg)
