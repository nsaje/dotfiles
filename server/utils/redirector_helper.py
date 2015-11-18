import json
import logging
import time
import urllib2

from django.conf import settings

from utils import request_signer
from utils import statsd_helper


logger = logging.getLogger(__name__)

NUM_RETRIES = 3


def validate_url(url, ad_group_id):
    try:
        data = json.dumps({'url': url, 'adgroupid': ad_group_id})
        return _call_api_retry(settings.R1_VALIDATE_API_URL, data)
    except Exception as e:
        logger.exception('Exception in validate_url')
        raise e


def insert_redirect(url, content_ad_id, ad_group_id):
    try:
        data = json.dumps({
            'url': url,
            'creativeid': int(content_ad_id),
            'adgroupid': int(ad_group_id),
        })

        return _call_api_retry(settings.R1_REDIRECTS_API_URL, data)
    except Exception as e:
        logger.exception('Exception in insert_redirect')
        raise e


def update_redirect(url, redirect_id):
    try:
        data = json.dumps({'url': url})

        _call_api_retry(settings.R1_REDIRECTS_API_URL + redirect_id + '/', data, method='PUT')
    except Exception as e:
        logger.exception('Exception in update_redirect')
        raise e


def insert_adgroup(ad_group_id, tracking_codes, enable_ga_tracking, enable_adobe_tracking, adobe_tracking_param):
    try:
        url = settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group_id)
        data = json.dumps({
            'trackingcode': tracking_codes,
            'enablegatracking': enable_ga_tracking,
            'enableadobetracking': enable_adobe_tracking,
            'adobetrackingparam': adobe_tracking_param,
        })
        return _call_api_retry(url, data, method='PUT')
    except Exception as e:
        logger.exception('Exception in insert_adgroup')
        raise e


def get_adgroup(ad_group_id):
    url = settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group_id)
    try:
        adgroup_dict = _call_api_retry(url, method='GET')
        return {
            'enable_ga_tracking': adgroup_dict.get('enablegatracking'),
            'enable_adobe_tracking': adgroup_dict.get('enableadobetracking'),
            'adobe_tracking_param': adgroup_dict.get('adobetrackingparam'),
            'tracking_code': adgroup_dict.get('trackingcode'),
        }
    except Exception as e:
        logger.exception('Exception in get_adgroup')
        raise e


@statsd_helper.statsd_timer('redirector_helper', 'fetch_redirects_impressions')
def fetch_redirects_impressions(date, account_id, slug, timeout=300):
    url = settings.R1_CONVERSION_STATS_URL.format(date=date.strftime('%Y-%m-%d'),
                                                  account_id=account_id,
                                                  slug=slug)

    logger.info('Querying redirect impressions')
    job_id = _call_api_retry(url, method='GET')

    start_time = time.time()
    while (time.time() - start_time) < timeout:
        logger.info('Polling redirect impressions results')
        result = _call_api_retry(settings.R1_CONVERSION_STATS_RESULT_URL.format(job_id=job_id), method='GET')
        if result is None:
            time.sleep(2)
            continue

        statsd_helper.statsd_gauge('redirector_helper.fetch_redirects_impressions_size', len(json.dumps(result)))
        return result

    raise Exception('Redirect conversion stats timeout')


def _call_api_retry(url, data=None, method='POST'):
    for _ in xrange(NUM_RETRIES):
        try:
            return _call_api(url, data, method)
        except Exception as error:
            pass

    raise error


def _call_api(url, data, method='POST'):
    request = urllib2.Request(url, data)
    request.get_method = lambda: method
    response = request_signer.urllib2_secure_open(request, settings.R1_API_SIGN_KEY)

    status_code = response.getcode()
    if status_code != 200:
        raise Exception('Invalid response status code. status code: {}'.format(status_code))

    ret = json.loads(response.read())
    if ret['status'] != 'ok':
        raise Exception('Request not successful. status: {}'.format(ret['status']))

    return ret.get('data')
