import binascii
import copy
import json
import logging
import urllib2

from django.conf import settings

from utils import encryption_helpers
from utils import json_helper
from utils import request_signer

logger = logging.getLogger(__name__)


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
    # Decrypt has to be the last thing to happen before sending to zwei.
    # Payload with decrypted credentials should never be logged.
    payload = _decrypt_payload_credentials(action.payload)
    data = json.dumps(payload, cls=json_helper.JSONEncoder)
    request = urllib2.Request(settings.ZWEI_API_URL, data)

    request_signer.sign(request, settings.ZWEI_API_SIGN_KEY)

    urllib2.urlopen(request)
