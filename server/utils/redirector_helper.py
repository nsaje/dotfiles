import json
import logging
import time
import urllib.request, urllib.error, urllib.parse

from django.conf import settings

from utils import request_signer


logger = logging.getLogger(__name__)

NUM_RETRIES = 3


def validate_url(url, ad_group_id):
    try:
        data = json.dumps({'url': url, 'adgroupid': ad_group_id})
        return _call_api_retry(settings.R1_VALIDATE_API_URL, data)
    except Exception:
        logger.exception('Exception in validate_url')
        raise


def insert_redirects(content_ads, clickthrough_resolve=True):
    if settings.R1_DEMO_MODE:
        data = {
            str(content_ad.id): {
                'redirect': {'url': 'http://example.com/FAKE'},
                'redirectid': 'XXXXXXXXXXXXX'
            } for content_ad in content_ads
        }
        return data

    try:
        data = json.dumps([{
            'url': content_ad.url,
            'creativeid': content_ad.id,
            'adgroupid': content_ad.ad_group_id,
            'noclickthroughresolve': not clickthrough_resolve,
        } for content_ad in content_ads])

        return _call_api_retry(settings.R1_REDIRECTS_BATCH_API_URL, data)
    except Exception:
        logger.exception('Exception in insert_redirect_batch')
        raise


def update_redirects(content_ads):
    data = [{
        'redirectid': content_ad.redirect_id,
        'redirect': {
            'url': content_ad.url,
        }
    } for content_ad in content_ads]
    if settings.R1_DEMO_MODE:
        return data

    return _call_api_retry(settings.R1_REDIRECTS_BATCH_API_URL, json.dumps(data), method='PUT')


def update_redirect(url, redirect_id):
    try:
        data = json.dumps({'url': url})

        return _call_api_retry(settings.R1_REDIRECTS_API_URL + redirect_id + '/', data, method='PUT')
    except Exception:
        logger.exception('Exception in update_redirect')
        raise


def insert_adgroup(ad_group):
    try:
        url = settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group.id)
        data = {
            'campaignid': ad_group.campaign_id,
            'accountid': ad_group.campaign.account_id,
            'trackingcode': ad_group.settings.get_tracking_codes(),
            'enablegatracking': ad_group.campaign.settings.enable_ga_tracking,
            'enableadobetracking': ad_group.campaign.settings.enable_adobe_tracking,
            'adobetrackingparam': ad_group.campaign.settings.adobe_tracking_param,
            'specialredirecttrackers': ad_group.settings.redirect_pixel_urls,
            'specialredirectjavascript': ad_group.settings.redirect_javascript,
        }
        return _call_api_retry(url, json.dumps(data), method='PUT')
    except Exception:
        logger.exception('Exception in insert_adgroup')
        raise


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
    except Exception:
        logger.exception('Exception in get_adgroup')
        raise


def get_adgroup_realtimestats(ad_group_id):
    url = settings.R1_REDIRECTS_ADGROUP_REALTIMESTATS_API_URL.format(adgroup=ad_group_id)
    try:
        return _call_api_retry(url, method='GET')
    except Exception:
        logger.exception('Exception in get_adgroup')
        raise


def upsert_audience(audience):
    try:
        rules = [{'id': str(rule.id), 'type': rule.type, 'value': rule.value} for rule in audience.audiencerule_set.all().order_by('pk')]
        source_pixels = [{'url': pixel.url, 'type': pixel.source_type.type} for pixel in audience.pixel.sourcetypepixel_set.all().order_by('pk')]

        audience_dict = {
            'id': str(audience.id),
            'accountid': audience.pixel.account.id,
            'pixieslug': audience.pixel.slug,
            'archived': audience.archived,
            'rules': rules,
            'pixels': source_pixels,
            'ttl': audience.ttl,
            'modifieddt': audience.modified_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        }

        data = json.dumps(audience_dict)
        return _call_api_retry(settings.R1_CUSTOM_AUDIENCE_API_URL.format(audience_id=audience.id), data=data, method='PUT')
    except Exception:
        logger.exception('Exception in insert_audience')
        raise


def delete_audience(audience_id):
    try:
        return _call_api_retry(settings.R1_CUSTOM_AUDIENCE_API_URL.format(audience_id=audience_id), method='DELETE')
    except Exception:
        logger.exception('Exception in delete_audience')
        raise


def get_pixel_traffic(timeout=300):
    request_url = settings.R1_PIXEL_TRAFFIC_URL

    logger.info('Querying pixel traffix')
    job_id = _call_api_retry(request_url, method='GET')

    start_time = time.time()
    while (time.time() - start_time) < timeout:
        logger.info('Polling pixel traffic results')
        result = _call_api_retry(settings.R1_PIXEL_TRAFFIC_RESULT_URL.format(job_id=job_id), method='GET')
        if result is None:
            time.sleep(2)
            continue

        return result

    raise Exception('Pixel traffic timeout')


def update_pixel(conversion_pixel):
    try:
        data = json.dumps({
            'redirecturl': conversion_pixel.redirect_url,
        })

        return _call_api_retry(settings.R1_PIXEL_URL.format(
            account_id=conversion_pixel.account_id,
            slug=conversion_pixel.slug,
        ), data, method='PUT')
    except Exception:
        logger.exception('Exception in update_pixel')
        raise


def _call_api_paginated(url, data=None, method='POST'):
    result = _call_api_retry(url, data, method)
    if result is None:
        return None

    result_data = result['data']
    while result['pagetoken'] != "":
        result = _call_api_retry(url + "?pagetoken=" + result['pagetoken'], data, method)
        if result is None:
            return None
        result_data += result['data']

    return result_data


def _call_api_retry(url, data=None, method='POST'):
    last_error = None
    for _ in range(NUM_RETRIES):
        try:
            return _call_api(url, data, method)
        except Exception as error:
            last_error = error

    raise last_error


def _call_api(url, data, method='POST'):
    if settings.R1_DEMO_MODE:
        return {}
    request = urllib.request.Request(url, data.encode('utf-8') if data else None)
    request.get_method = lambda: method
    response = request_signer.urllib_secure_open(request, settings.R1_API_SIGN_KEY)

    status_code = response.getcode()
    if status_code != 200:
        raise Exception('Invalid response status code. status code: {}'.format(status_code))

    ret = json.loads(response.read())
    if ret['status'] != 'ok':
        raise Exception('Request not successful. status: {}'.format(ret['status']))

    return ret.get('data')
