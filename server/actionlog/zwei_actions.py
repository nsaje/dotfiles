import binascii
import copy
import json
import logging
import urllib2

from django.conf import settings

from utils import encryption_helpers

logger = logging.getLogger(__name__)


def _decrypt_payload_credentials(action):
    payload = copy.deepcopy(action.payload)
    if not payload.get('credentials'):
        return payload

    payload['credentials'] = json.loads(
        encryption_helpers.aes_decrypt(
            binascii.a2b_base64(
                action.ad_group_network.network_credentials.credentials
            ),
            settings.CREDENTIALS_ENCRYPTION_KEY
        )
    )

    return payload


def send(action):
    payload = _decrypt_payload_credentials(action)
    data = json.dumps(payload)
    request = urllib2.Request(settings.ZWEI_API_URL, data)

    urllib2.urlopen(request)
