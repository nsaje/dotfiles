import httplib
import json
import logging
import requests
from django.conf import settings

from dash import constants

logger = logging.getLogger(__name__)

ACCESS_TYPE = 'AGENCY'
PERMITTED_ROLES = ['ADVERTISER']
FB_PAGES_URL = 'https://graph.facebook.com/{}/{}/pages'
FB_PAGE_ID_URL = "https://graph.facebook.com/{}/{}?fields=id"
FB_API_VERSION = 'v2.6'

ERROR_INVALID_PAGE = 'Param page_id must be a valid page ID'
ERROR_ALREADY_PENDING = 'There is already pending client request for page'
ERROR_ALREADY_CONNECTED = 'You Already Have Access To This Page'


def update_facebook_account(facebook_account, new_url):
    if new_url == facebook_account.page_url:
        return

    if not new_url:
        facebook_account.page_url = None
        facebook_account.page_id = None
        facebook_account.status = constants.FacebookPageRequestType.EMPTY
        return

    facebook_account.page_url = new_url
    page_id = get_page_id(new_url)
    if page_id:
        facebook_account.page_id = page_id
        facebook_account.status = _send_page_access_request(page_id)
    else:
        facebook_account.page_id = None
        facebook_account.status = constants.FacebookPageRequestType.ERROR


def get_page_id(page_url):
    page_id = _extract_page_id_from_url(page_url)
    params = {'access_token': settings.FB_ACCESS_TOKEN}
    response = requests.get(FB_PAGE_ID_URL.format(FB_API_VERSION, page_id), params=params)

    if response.status_code != httplib.OK:
        logger.error('Error while retrieving facebook page id. Status code: %s, Error %s', response.status_code,
                     response.content)
        return None

    return response.json()['id']


def _extract_page_id_from_url(page_url):
    url = page_url.strip('/')
    page_id = url[url.rfind('/') + 1:]
    dash_index = page_id.rfind('-')
    if dash_index != -1:
        page_id = page_id[dash_index + 1:]
    return page_id


def _send_page_access_request(page_id):
    params = {'page_id': page_id,
              'access_type': ACCESS_TYPE,
              'permitted_roles': PERMITTED_ROLES,
              'access_token': settings.FB_ACCESS_TOKEN}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(FB_PAGES_URL.format(FB_API_VERSION, settings.FB_BUSINESS_ID), data=json.dumps(params),
                             headers=headers)

    if response.status_code == 200:
        return constants.FacebookPageRequestType.PENDING
    elif response.status_code == 400:
        error = response.json().get('error', {})

        if ERROR_ALREADY_CONNECTED in error.get('error_user_title', ''):
            return constants.FacebookPageRequestType.CONNECTED
        elif ERROR_ALREADY_PENDING in error.get('message', ''):
            return constants.FacebookPageRequestType.PENDING
        elif ERROR_INVALID_PAGE in error.get('message', ''):
            logger.warning('FB api returned an invalid page error for pageId: {}. Error message: {}', page_id,
                           error.get('message'))
            return constants.FacebookPageRequestType.INVALID

    error = response.json().get('error', {})
    logger.error('FB api returned and unknown error for pageId: {}. Status code: {}, error message: {}',
                 response.status_code, error)
    return constants.FacebookPageRequestType.ERROR
