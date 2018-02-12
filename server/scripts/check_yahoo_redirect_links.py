# coding: utf-8

import base64
import json
import requests
import logging

from dash import models

requests.packages.urllib3.disable_warnings()
logging.getLogger("requests").setLevel(logging.WARNING)

CLIENT_ID = ''
CLIENT_SECRET = ''
OAUTH_TOKENS = {}

DEFAULT_API_PAGE_LIMIT = 100
AUTH_TOKEN_EXPIRED_ERR = 'oauth_problem="token_expired"'


OAUTH_REFRESH_TOKEN_URL = 'https://api.login.yahoo.com/oauth2/get_token'

AD_GROUP_ENDPOINT = 'https://api.admanager.yahoo.com/v1/rest/adgroup/'
AD_ENDPOINT = 'https://api.admanager.yahoo.com/v1/rest/ad/'
# ?adGroupId={adgroup_id}


class SessionWithTimeout(requests.Session):

    def request(self, *args, **kwargs):
        if not kwargs.get('timeout') and hasattr(self, 'timeout'):
            kwargs['timeout'] = self.timeout
        if not kwargs.get('verify'):
            kwargs['verify'] = False
        return super(SessionWithTimeout, self).request(*args, **kwargs)


def get_requests_session():
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Zemanta/1.0; +http://www.zemanta.com)',
    }
    session = SessionWithTimeout()
    session.headers = headers
    session.timeout = 120
    return session


def _refresh_access_token():
    global OAUTH_TOKENS

    headers = {
        'Authorization': 'Basic {}'.format(
            base64.b64encode(CLIENT_ID + ':' + CLIENT_SECRET)
        )
    }

    data = {
        'redirect_uri': 'oob',
        'refresh_token': OAUTH_TOKENS['refresh_token'],
        'grant_type': 'refresh_token'
    }

    r = requests.post(OAUTH_REFRESH_TOKEN_URL, data=data, headers=headers)
    if not r.status_code == 200:
        raise Exception('Unable to refresh access token')

    OAUTH_TOKENS = json.loads(r.text)


def _get_auth_headers():
    return {'Authorization': 'Bearer {}'.format(OAUTH_TOKENS['access_token'])}


def _try_parse_api_response(response):
    try:
        return json.loads(response)
    except ValueError:
        pass

    raise Exception('Unknown API response format. response: %s' % response)


def _make_api_call(url, method='GET', data=None, params=None, headers={}):
    try:
        parsed = _make_api_request(method, url, data, params, headers)
    except Exception:
        _refresh_access_token()
        parsed = _make_api_request(method, url, data, params, headers)

    if parsed['errors']:
        raise Exception('Errors in API response. errors={errors}'.format(errors=parsed['errors']))

    if not isinstance(parsed['response'], list) and not parsed['response']:
        raise Exception('Empty API response')

    return parsed['response']


def _make_api_request(method, url, data, params, headers):
    headers.update(_get_auth_headers())
    r = requests.request(method=method, url=url, data=data, params=params, headers=headers)
    return _try_parse_api_response(r.content)


def _get_promoted_links(ad_group_id):
    result = []
    offset = 0

    while True:
        params = {
            'mr': DEFAULT_API_PAGE_LIMIT,
            'si': offset,
            'adGroupId': ad_group_id
        }
        ads = _make_api_call(AD_ENDPOINT, params=params)
        result.extend(ads)

        if len(ads) < DEFAULT_API_PAGE_LIMIT:
            break

        offset += DEFAULT_API_PAGE_LIMIT

    return result


def _get_adgroups(source_campaign_key):
    return _make_api_call(
        AD_GROUP_ENDPOINT,
        params={'campaignId': source_campaign_key},
    )


def _get_ad_group_id(campaign_id):
    ad_groups = _get_adgroups(campaign_id)
    if len(ad_groups) != 1:
        raise Exception('Wrong number of ad groups: {}'.format(len(ad_groups)))

    return ad_groups[0]['id']


y_cass = models.ContentAdSource.objects.filter(source_id=4, content_ad__redirect_id__isnull=False,
                                               source_content_ad_id__isnull=False)

print('getting ad group ids')
ad_group_ids = set()
for i, y_cas in enumerate(y_cass):
    if i % 1000 == 0:
        print(i)
    ad_group_ids.add(y_cas.content_ad.ad_group_id)

to_update = []
for ad_group_id in ad_group_ids:
    ad_group_source = models.AdGroupSource.objects.get(source_id=4, ad_group_id=ad_group_id)
    y_ad_group_id = _get_ad_group_id(ad_group_source.source_campaign_key)
    ads = _get_promoted_links(y_ad_group_id)
    print('AD GROUP %s, NUM ADS: %s' % (ad_group_id, len(ads)))

    for y_cas in y_cass.filter(content_ad__ad_group_id=ad_group_id):
        for ad in ads:
            if int(ad['id']) == int(y_cas.source_content_ad_id):
                if '//r1.zemanta.com' not in ad['landingUrl']:
                    print(y_cas.content_ad_id, ad['landingUrl'])
                    to_update.append(y_cas.content_ad_id)
