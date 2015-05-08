import binascii
import copy
import httplib
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


def _set_as_failed(action, msg):
    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save()


def _handle_error(action, e):
    msg = traceback.format_exc(e)
    logger.error(msg)
    _set_as_failed(action, msg)


def _decrypt_payload_credentials(payload):
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
        # Decrypt has to be the last thing to happen before sending to zwei.
        # Payload with decrypted credentials should never be logged.
        payload = _decrypt_payload_credentials(action.payload)
        data = json.dumps(payload, cls=json_helper.JSONEncoder)
        request = urllib2.Request(settings.ZWEI_API_URL, data)

        response = request_signer.urllib2_secure_open(request, settings.ZWEI_API_SIGN_KEY)
        if response.getcode() != httplib.OK:
            _set_as_failed(action, response.read())

    except Exception as e:
        _handle_error(action, e)


def send_multiple(actionlogs):
    for actionlog in actionlogs:
        send(actionlog)


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
