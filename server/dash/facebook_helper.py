import json

import requests
from django.conf import settings

from dash import constants

ACCESS_TYPE = 'AGENCY'
PERMITTED_ROLES = ['ADVERTISER']
FB_API_URL = 'https://graph.facebook.com/%s/%s/pages'
API_VERSION = 'v2.6'

ERROR_INVALID_PAGE = 'Param page_id must be a valid page ID'
ERROR_ALREADY_PENDING = 'There is already pending client request for page'
ERROR_ALREADY_CONNECTED = 'You Already Have Access To This Page'


def send_page_access_request(page_id):
    params = {'page_id': page_id,
              'access_type': ACCESS_TYPE,
              'permitted_roles': PERMITTED_ROLES,
              'access_token': settings.FB_ACCESS_TOKEN}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

    response = requests.post(FB_API_URL % (API_VERSION, settings.FB_APP_ID), data=json.dumps(params), headers=headers)

    if response.status_code == 200:
        return constants.FacebookPageRequestType.PENDING
    elif response.status_code == 400:
        error = json.loads(response.content).get('error')
        if error:
            if error.get('error_user_title') and error['error_user_title'].find(ERROR_ALREADY_CONNECTED) >= 0:
                return constants.FacebookPageRequestType.CONNECTED
            elif error.get('message') and error['message'].find(ERROR_INVALID_PAGE) >= 0:
                return constants.FacebookPageRequestType.INVALID_PAGE
            elif error.get('message') and error['message'].find(ERROR_ALREADY_PENDING) >= 0:
                return constants.FacebookPageRequestType.PENDING
    return constants.FacebookPageRequestType.UNKNOWN

