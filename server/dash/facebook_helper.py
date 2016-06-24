import httplib
import json
import logging
import requests

from dash import constants, models

logger = logging.getLogger(__name__)

ACCESS_TYPE = 'AGENCY'
PERMITTED_ROLES = ['ADVERTISER']
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}
FB_AD_ACCOUNT_URL = "https://graph.facebook.com/{}/{}/adaccount"
FB_PAGES_URL = 'https://graph.facebook.com/{}/{}/pages'
FB_PAGE_ID_URL = "https://graph.facebook.com/{}/{}?fields=id"
FB_USER_PERMISSIONS_URL = "https://graph.facebook.com/{}/{}/userpermissions"
FB_API_VERSION = 'v2.6'

TZ_AMERICA_NEW_YORK = 7
CURRENCY_USD = 'USD'

ERROR_INVALID_PAGE = 'Param page_id must be a valid page ID'
ERROR_ALREADY_PENDING = 'There is already pending client request for page'
ERROR_ALREADY_CONNECTED = 'You Already Have Access To This Page'


def update_facebook_account(facebook_account, new_url, business_id, access_token):
    if new_url == facebook_account.page_url:
        return

    if not new_url:
        facebook_account.page_url = None
        facebook_account.page_id = None
        facebook_account.status = constants.FacebookPageRequestType.EMPTY
        return

    facebook_account.page_url = new_url
    page_id = get_page_id(new_url, access_token)
    if page_id:
        facebook_account.page_id = page_id
        facebook_account.status = send_page_access_request(page_id, business_id, access_token)
    else:
        facebook_account.page_id = None
        facebook_account.status = constants.FacebookPageRequestType.ERROR


def get_page_id(page_url, access_token):
    page_id = extract_page_id_from_url(page_url)
    params = {'access_token': access_token}
    response = requests.get(FB_PAGE_ID_URL.format(FB_API_VERSION, page_id), params=params)

    if response.status_code != httplib.OK:
        logger.error('Error while retrieving facebook page id. Status code: %s, Error %s', response.status_code,
                     response.content)
        return None

    return response.json()['id']


def extract_page_id_from_url(page_url):
    url = page_url.strip('/')
    page_id = url[url.rfind('/') + 1:]
    dash_index = page_id.rfind('-')
    if dash_index != -1:
        page_id = page_id[dash_index + 1:]
    return page_id


def send_page_access_request(page_id, business_id, access_token):
    params = {'page_id': page_id,
              'access_type': ACCESS_TYPE,
              'permitted_roles': PERMITTED_ROLES,
              'access_token': access_token}
    response = requests.post(FB_PAGES_URL.format(FB_API_VERSION, business_id), data=json.dumps(params),
                             headers=HEADERS)

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


def get_all_pages(business_id, access_token):
    params = {'access_token': access_token}
    response = requests.get(FB_PAGES_URL.format(FB_API_VERSION, business_id), params=params)

    if response.status_code != httplib.OK:
        logger.error('Error while accessing facebook page api. Status code: %s, Error %s', response.status_code,
                     response.content)
        return None

    content = response.json()
    pages_dict = {}
    for page in content.get('data'):
        pages_dict[page['id']] = page['access_status']

    return pages_dict


def create_ad_account(name, page_id, app_id, business_id, access_token):
    params = {'name': name,
              'currency': CURRENCY_USD,
              'timezone_id': TZ_AMERICA_NEW_YORK,
              'end_advertiser': page_id,
              'media_agency': app_id,
              'partner': page_id,
              # TODO matijav 16.06.2016 disabled until we setup Business Manager Owned Normal Credit Line
              # 'invoice': True,
              'access_token': access_token}
    response = requests.post(FB_AD_ACCOUNT_URL.format(FB_API_VERSION, business_id), json.dumps(params),
                             headers=HEADERS)
    if response.status_code != httplib.OK:
        logger.error('Error while creating facebook ad account. Status code: %s, Error %s', response.status_code,
                     response.content)
        return None

    content = response.json()
    return content['id']


def add_system_user_permissions(connected_object_id, role, business_id, system_user_id, access_token):
    params = {'business':  business_id,
              'user': system_user_id,
              'role': role,
              'access_token': access_token}
    response = requests.post(FB_USER_PERMISSIONS_URL.format(FB_API_VERSION, connected_object_id), json.dumps(params),
                             headers=HEADERS)
    if response.status_code != httplib.OK:
        logger.error('Error while adding system user to a connected object. Status code: %s, Error %s',
                     response.status_code, response.content)
        return False
    return True


def get_credentials():
    return json.loads(models.SourceCredentials.objects.get(source__bidder_slug='facebook').decrypt())
