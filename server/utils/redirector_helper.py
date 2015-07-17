import json
import logging
import urllib2

from django.conf import settings

from utils import request_signer


logger = logging.getLogger(__name__)

NUM_RETRIES = 3


def validate_url(url):
    try:
        data = json.dumps({'url': url})
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
        logger.exception('Exception in insert_redirect_try')
        raise e


def insert_adgroup(ad_group_id, tracking_codes, disable_auto_tracking=False):
    try:
        url = settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group_id)
        data = json.dumps({
            'trackingcode': tracking_codes,
            'disableautotracking': disable_auto_tracking,
        })
        return _call_api_retry(url, data)
    except Exception as e:
        logger.exception('Exception in insert_adgroup_try')
        raise e


def _call_api_retry(url, data, method='POST'):
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
