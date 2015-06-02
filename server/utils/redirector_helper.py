import json
import urllib2

from django.conf import settings

from utils import request_signer


def insert_redirect(url, content_ad_id, ad_group_id):
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

    return ret['data']
