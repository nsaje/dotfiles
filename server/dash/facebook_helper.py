import json
import logging
import requests
from django.conf import settings

from dash import constants

logger = logging.getLogger(__name__)

ACCESS_TYPE = 'AGENCY'
PERMITTED_ROLES = ['ADVERTISER']
FB_API_URL = 'https://graph.facebook.com/{}/{}/pages'
API_VERSION = 'v2.6'

ERROR_INVALID_PAGE = 'Param page_id must be a valid page ID'
ERROR_ALREADY_PENDING = 'There is already pending client request for page'
ERROR_ALREADY_CONNECTED = 'You Already Have Access To This Page'


def update_facebook_account(facebook_account, new_url):
    if new_url == facebook_account.page_url:
        return

    facebook_account.page_url = new_url
    facebook_account.status = _send_page_access_request(
        facebook_account) if new_url else constants.FacebookPageRequestType.EMPTY


def _send_page_access_request(facebook_account):
    page_id = facebook_account.get_page_id()

    params = {'page_id': page_id,
              'access_type': ACCESS_TYPE,
              'permitted_roles': PERMITTED_ROLES,
              'access_token': settings.FB_ACCESS_TOKEN}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

    response = requests.post(FB_API_URL.format(API_VERSION, settings.FB_BUSINESS_ID), data=json.dumps(params),
                             headers=headers)

    if response.status_code == 200:
        return constants.FacebookPageRequestType.PENDING
    elif response.status_code == 400:
        error = json.loads(response.content).get('error', {})

        if error.get('error_user_title', '').find(ERROR_ALREADY_CONNECTED) >= 0:
            return constants.FacebookPageRequestType.CONNECTED
        elif error.get('message', '').find(ERROR_ALREADY_PENDING) >= 0:
            return constants.FacebookPageRequestType.PENDING
        elif error.get('message', '').find(ERROR_INVALID_PAGE) >= 0:
            logger.warning('FB api returned an invalid page error for pageId: {}. Error message: {}', page_id,
                           error.get('message'))
            return constants.FacebookPageRequestType.INVALID

    logger.error('FB api returned and unknown error for pageId: {}. Error message: {}', error)
    return constants.FacebookPageRequestType.ERROR
