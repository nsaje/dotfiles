import datetime
import json

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

import dash.api
import dash.constants
import dash.models
from django.db import transaction

from integrations.bizwire import config, models
from integrations.bizwire.internal import helpers

import restapi.views

from utils import dates_helper
from utils import k1_helper

from zemauth.models import User

DEFAULT_TARGETING_STR = 'DEFAULT TARGETING'


def _is_pacific_midnight():
    pacific_now = helpers.get_pacific_now()
    return pacific_now.hour == 0


def _is_day_before_new_rotation():
    return True  # TODO: define days when rotation happens


def _should_create_new_ad_groups():
    return _is_pacific_midnight() and _is_day_before_new_rotation()


def check_midnight_and_stop_ads():
    if not _is_pacific_midnight():
        return

    utc_now = dates_helper.utc_now()
    content_ads = dash.models.ContentAd.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        created_dt__lt=datetime.datetime(utc_now.year, utc_now.month, utc_now.day, utc_now.hour),
        state=dash.constants.ContentAdSourceState.ACTIVE,
    )
    dash.api.update_content_ads_state(content_ads, dash.constants.ContentAdSourceState.INACTIVE, None)

    ad_group_ids = set(ca.ad_group_id for ca in content_ads)
    k1_helper.update_ad_groups(ad_group_ids)


def check_time_and_create_new_ad_groups():
    if not _should_create_new_ad_groups():
        return

    start_date = datetime.date.today() + datetime.timedelta(days=1)
    _rotate_ad_groups(start_date)


def check_date_and_stop_old_ad_groups():
    if not _is_pacific_midnight():
        return

    pacific_today = helpers.get_pacific_now().date
    previous_start_date = models.AdGroupTargeting.objects.filter(
        start_date__lte=pacific_today,
    ).values_list('start_date', flat=True).order_by('-start_date').distinct()[1]
    ad_group_ids = models.AdGroupTargeting.objects.filter(
        start_date=previous_start_date
    ).values_list('ad_group_id', flat=True)
    for ad_group_id in ad_group_ids:
        _stop_ad_group(ad_group_id)


@transaction.atomic
def _rotate_ad_groups(start_date):
    targeting_options = []
    default_ad_group_name = _get_ad_group_name(start_date)
    default_ad_group_id = _create_ad_group(default_ad_group_name, start_date, config.INTEREST_TARGETING_OPTIONS)
    targeting_options.append((default_ad_group_id, []))

    for interest_targeting in config.INTEREST_TARGETING_GROUPS:
        name = _get_ad_group_name(start_date, interest_targeting=interest_targeting)
        ad_group_id = _create_ad_group(name, start_date, interest_targeting)
        targeting_options.append((ad_group_id, interest_targeting))

    _persist_targeting_options(start_date, targeting_options)


def _create_ad_group(name, start_date, interest_targeting):
    data = {
        'campaignId': config.AUTOMATION_CAMPAIGN,
        'name': name,
        'state': 'ACTIVE',
        'startDate': start_date.isoformat(),
        'endDate': None,
        'targeting': {
            'devices': ['DESKTOP', 'TABLET', 'MOBILE'],
            'geo': {
                'included': {
                    'countries': ['US'],
                }
            },
            'interest': {
                'included': [cat.upper() for cat in interest_targeting]
            },
        }
    }
    url = 'rest/v1/adgroups/'
    ad_group_id = int(_make_restapi_fake_post_request(restapi.views.AdGroupViewList, url, data)['id'])
    _set_sources_settings(ad_group_id)
    return ad_group_id


def _stop_ad_group(ad_group_id):
    data = {
        'state': 'INACTIVE',
    }
    url = 'rest/v1/adgroups/{}/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.views.AdGroupViewDetails, url, data, view_args=[ad_group_id])


def _list_ad_group_sources(ad_group_id):
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_get_request(restapi.views.AdGroupSourcesViewList, url, view_args=[ad_group_id])


def _set_sources_settings(ad_group_id):
    sources = _list_ad_group_sources(ad_group_id)
    data = [{
        'source': source['source'],
        'dailyBudget': config.DEFAULT_DAILY_BUDGET,
        'cpc': config.DEFAULT_CPC,
        'state': 'ACTIVE',
    } for source in sources]
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.views.AdGroupSourcesViewList, url, data, view_args=[ad_group_id])


def _persist_targeting_options(start_date, targeting_options):
    if models.AdGroupTargeting.objects.filter(start_date__gte=start_date):
        raise Exception('Targetings already exist')

    for ad_group_id, interest_targeting in targeting_options:
        models.AdGroupTargeting.objects.create(
            ad_group_id=ad_group_id,
            interest_targeting=sorted(interest_targeting),
            start_date=start_date,
        )


def _get_ad_group_name(start_date, interest_targeting=None):
    interest_targeting_str = DEFAULT_TARGETING_STR
    if interest_targeting:
        interest_targeting = sorted(list(set(interest_targeting) & set(config.INTEREST_TARGETING_OPTIONS)))
        interest_targeting_str = ', '.join(
            category.upper() for category in (interest_targeting)
        )

    name = config.AD_GROUP_NAME_TEMPLATE.format(
        start_date=start_date,
        interest_targeting_str=interest_targeting_str,
    )
    name_max_length = dash.models.AdGroup._meta.get_field('name').max_length
    if len(name) > name_max_length:
        name = name[:name_max_length-4] + ' ...'

    return name


def _make_restapi_fake_get_request(viewcls, url, view_args=[]):
    factory = APIRequestFactory()
    request = factory.get(url)
    return _make_restapi_fake_request(viewcls, view_args, request)


def _make_restapi_fake_post_request(viewcls, url, data, view_args=[]):
    factory = APIRequestFactory()
    request = factory.post(url, data, format='json')
    return _make_restapi_fake_request(viewcls, view_args, request)


def _make_restapi_fake_put_request(viewcls, url, data, view_args=[]):
    factory = APIRequestFactory()
    request = factory.put(url, data, format='json')
    return _make_restapi_fake_request(viewcls, view_args, request)


def _make_restapi_fake_request(viewcls, view_args, request):
    force_authenticate(request, user=User.objects.get(email=config.AUTOMATION_USER_EMAIL))
    view = viewcls.as_view()
    response = view(request, *view_args)
    response.render()
    if response.status_code >= 300:
        raise Exception(
            'RestAPI returned unexpected response. status code: {}, status text: {}'.format(
                response.status_code, response.status_text)
        )
    return json.loads(response.content)['data']
