import json
import logging
import urllib2

from django.conf import settings

from utils import request_signer


logger = logging.getLogger(__name__)

NUM_RETRIES = 3

BANKER_ADGROUP_SPEND = '/api/realtimestats/{adgroup}/'


def get_adgroup_realtimespend(ad_group_id):
    url = settings.BIDDER_API_URL_BASE + BANKER_ADGROUP_SPEND.format(adgroup=ad_group_id)
    try:
        ret_dict = _call_api_retry(url, method='GET')
        return {
            'spend': ret_dict['spend'],
        }
    except Exception:
        logger.exception('Exception in get_adgroup_realtimestats')
        raise


def _call_api_retry(url, data=None, method='POST', num_retries=NUM_RETRIES):
    for _ in xrange(num_retries):
        try:
            return _call_api(url, data, method)
        except Exception as error:
            pass

    raise error


def _call_api(url, data, method='POST'):
    request = urllib2.Request(url, data)
    request.get_method = lambda: method
    response = request_signer.urllib2_secure_open(request, settings.BIDDER_API_SIGN_KEY[0])

    status_code = response.getcode()
    if status_code != 200:
        raise Exception('Invalid response status code. status code: {}'.format(status_code))

    ret = json.loads(response.read())
    if ret['error'] is not None:
        raise Exception('Request not successful. status: {}'.format(ret['error']))

    return ret
