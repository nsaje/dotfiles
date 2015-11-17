import json
import requests
import logging
import sys

logging.getLogger('requests').setLevel(logging.CRITICAL)
requests.packages.urllib3.disable_warnings()


from dash import models

AD_GROUP_IDS = []

EMAIL = ''
PASSWORD = ''

SIGNIN_URL_USER = 'https://dashboard.gravity.com/user/signin'
SIGNIN_URL_PUBLIC_LARAVEL = 'https://dashboard.gravity.com/public/signin?fromLaravelPost=1'
CAMPAIGN_GET_ARTICLES_URL = ('https://dashboard.gravity.com/api/campaign-article-settings?'
                             'campaignKey={campaign_id}&page=1&sg={site_token}')


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


def _login(session):
    session.headers['X_REQUESTED_WITH'] = 'XMLHttpRequest'
    try:
        response = session.post(
            SIGNIN_URL_USER,
            data={
                'email': EMAIL,
                'password': PASSWORD,
            },
            allow_redirects=True
        )
    except Exception:
        et, ei, tb = sys.exc_info()
        raise Exception, ei, tb

    # the response is empty, only check status code
    check_response_error(response, Exception,
                         'Login to /user failed.')

    try:
        response = session.post(
            SIGNIN_URL_PUBLIC_LARAVEL,
            data={
                'email': EMAIL,
                'password': PASSWORD,
            },
            allow_redirects=True
        )
    except Exception:
        et, ei, tb = sys.exc_info()
        raise Exception, ei, tb

    check_response_error(response, Exception,
                         'Login to /public failed.')


def check_response_error(response, exception_cls, info=None):
    if response.status_code >= 400:
        raise exception_cls('Response status code {}. {}'.format(response.status_code, (info if info else '')))


def extract_json(content):
    # in some cases gravity returns some other content from their api
    # besides a json dict (php file list)
    bracket_indices = None
    if '{' in content and '}' in content:
        bracket_indices = (content.find('{'), content.rfind('}'))

    if '[' in content and ']' in content and (bracket_indices is None or content.find('[') < bracket_indices[0]):
        bracket_indices = (content.find('['), content.rfind(']'))

    if bracket_indices:
        return content[bracket_indices[0]: bracket_indices[1] + 1]

    return content


def list_articles(session, source_campaign_key):
    site_token, campaign_key = source_campaign_key
    try:
        url = CAMPAIGN_GET_ARTICLES_URL.format(site_token=site_token, campaign_id=campaign_key)
        response = session.get(url, allow_redirects=True)
    except Exception:
        et, ei, tb = sys.exc_info()
        raise Exception, ei, tb

    check_response_error(response, Exception, 'Fetching campaign article list failed.')

    content = extract_json(response.content.decode('cp1252'))
    return json.loads(content)


old_urls_gravity = {}
if __name__ == '__main__':
    session = get_requests_session()
    _login(session)

    if 'AD_GROUP_IDS' in globals() and AD_GROUP_IDS:
        ad_group_ids = AD_GROUP_IDS
    else:
        ad_group_ids = [ags.ad_group_id for ags in models.AdGroupSource.objects.filter(can_manage_content_ads=True,
                                                                                       source_id=2)]

    for ad_group_id in ad_group_ids:
        content_ads = list(models.ContentAd.objects.filter(ad_group_id=ad_group_id))
        try:
            ad_group_source = models.AdGroupSource.objects.get(ad_group_id=ad_group_id, source_id=2)
        except models.AdGroupSource.DoesNotExist:
            continue

        if ad_group_source.source_campaign_key == "PENDING":
            continue

        articles = list_articles(session, ad_group_source.source_campaign_key)

        count = 0
        for article in articles:
            if 'r1.zemanta.com' in article['article']['url']:
                continue

            if ad_group_id not in old_urls_gravity:
                old_urls_gravity[ad_group_id] = []
            old_urls_gravity[ad_group_id].append(article)

            count += 1

        print 'AD GROUP ID: {} NUM LINKS: {}, OLD URLS: {}'.format(ad_group_id, len(articles), len(old_urls_gravity.get(ad_group_id, [])))

    print 'COUNT:', count
