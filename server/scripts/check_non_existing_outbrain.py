import json
import logging
import requests

from dash import models

logging.getLogger('requests').setLevel(logging.CRITICAL)
requests.packages.urllib3.disable_warnings()

AD_GROUP_IDS = []

API_TOKEN = ''

DEFAULT_API_PAGE_LIMIT = 100

LIST_MARKETERS_API = 'https://api.outbrain.com/amplify/v0.1/marketers'
LIST_CAMPAIGNS_API = 'https://api.outbrain.com/amplify/v0.1/marketers/{marketer_id}/campaigns'
LIST_PROMOTED_LINKS_API = 'https://api.outbrain.com/amplify/v0.1/campaigns/{campaign_id}/promotedLinks'


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


def execute_api_call(url, method='GET', headers={}, params=None, data=None):
    api_token = API_TOKEN

    if data:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)

    headers.update({
        'OB-TOKEN-V1': api_token
    })
    r = session.request(method=method, url=url, data=data, params=params, headers=headers)

    if r.status_code != 200:
        raise Exception(
            u'Bad status code in API response. status_code: {}, message: {}'.format(r.status_code, r.text)
        )

    if r.text:
        return json.loads(r.text)


def get_promoted_links(campaign_id):
    result = []

    url = LIST_PROMOTED_LINKS_API.format(campaign_id=campaign_id)
    offset = 0
    while True:
        params = {
            'limit': DEFAULT_API_PAGE_LIMIT,
            'offset': offset
        }
        response = execute_api_call(url, params=params)
        for promoted_link in response['promotedLinks']:
            result.append(promoted_link)

        offset += DEFAULT_API_PAGE_LIMIT
        if response['totalCount'] <= offset:
            break

    return result


unmatched_outbrain = {}
if __name__ == '__main__':
    session = get_requests_session()

    if 'AD_GROUP_IDS' in globals() and AD_GROUP_IDS:
        ad_group_ids = AD_GROUP_IDS
    else:
        ad_group_ids = [ags.ad_group_id for ags in models.AdGroupSource.objects.filter(can_manage_content_ads=True,
                                                                                       source_id=3)]

    count = 0
    for ad_group_id in ad_group_ids:
        content_ads = list(models.ContentAd.objects.filter(ad_group_id=ad_group_id))
        try:
            ad_group_source = models.AdGroupSource.objects.get(ad_group_id=ad_group_id, source_id=3)
        except models.AdGroupSource.DoesNotExist:
            continue

        non_existing = set()
        promoted_links = get_promoted_links(ad_group_source.source_campaign_key['campaign_id'])
        for promoted_link in promoted_links:
            if not promoted_link['enabled']:
                continue

            try:
                models.ContentAdSource.objects.get(source_content_ad_id=promoted_link['id'],
                                                   source_id=3, content_ad__ad_group_id=ad_group_id)
                continue
            except models.ContentAdSource.DoesNotExist:
                pass

            if promoted_link['text'] == 'The Rise of Content Ads':
                continue

            if ad_group_id not in unmatched_outbrain:
                unmatched_outbrain[ad_group_id] = []
            unmatched_outbrain[ad_group_id].append(promoted_link)

            count += 1

        print 'AD GROUP ID: {} NUM LINKS: {}, NON EXISTING: {}'.format(ad_group_id, len(promoted_links), len(unmatched_outbrain.get(ad_group_id, [])))

    print 'COUNT:', count
