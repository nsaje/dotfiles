import json
import logging
import urllib2

from django.conf import settings

from utils import request_signer


logger = logging.getLogger(__name__)

INSERT_REDIRECT_RETRIES = 3


def insert_redirect(url, content_ad_id, ad_group_id):
    for _ in xrange(INSERT_REDIRECT_RETRIES):
        try:
            return _insert_redirect_try(url, content_ad_id, ad_group_id)
        except Exception as error:
            logger.exception('Exception in insert_redirect_try')

    raise error


def _insert_redirect_try(url, content_ad_id, ad_group_id):
    data = json.dumps({
        'url': url,
        'creativeid': content_ad_id,
        'adgroupid': ad_group_id,
    })
    request = urllib2.Request(settings.R1_REDIRECTS_API_URL, data)
    response = request_signer.urllib2_secure_open(request, settings.R1_API_SIGN_KEY)

    status_code = response.getcode()
    if status_code != 200:
        raise Exception('Invalid response status code. status code: {}'.format(status_code))

    ret = json.loads(response.read())
    if ret['status'] != 'ok':
        raise Exception('Generate redirect request not successful. status: {}'.format(ret['status']))

    if not ret['data']:
        raise Exception('Generate redirect request not successful. data: {}'.format(ret['data']))

    return ret['data']


def insert_adgroup(ad_group_id, tracking_codes, disable_auto_tracking=False):
    for _ in xrange(INSERT_REDIRECT_RETRIES):
        try:
            return _insert_adgroup_try(ad_group_id, tracking_codes, disable_auto_tracking)
        except Exception as error:
            logger.exception('Exception in insert_adgroup_try')

    raise error


def _insert_adgroup_try(ad_group_id, tracking_codes, disable_auto_tracking):
    data = json.dumps({
        'trackingcode': tracking_codes,
        'disableautotracking': disable_auto_tracking,
    })

    url = settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group_id)

    request = urllib2.Request(url, data)
    response = request_signer.urllib2_secure_open(request, settings.R1_API_SIGN_KEY)

    status_code = response.getcode()
    if status_code != 200:
        raise Exception('Invalid response status code. status code: {}'.format(status_code))

    ret = json.loads(response.read())
    if ret['status'] != 'ok':
        raise Exception('Upsert redirect adgroup request not successful. status: {}'.format(ret['status']))
