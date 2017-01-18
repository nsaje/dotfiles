import datetime
import json
import math

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

AD_GROUP_NAME_TEMPLATE = '{start_date} - DEFAULT TARGETING'


def _is_pacific_midnight():
    pacific_now = helpers.get_pacific_now()
    return pacific_now.hour == 0


def _is_day_before_new_rotation():
    return True  # TODO: define days when rotation happens


def _should_create_new_ad_groups():
    return _is_pacific_midnight() and _is_day_before_new_rotation()


def check_pacific_midnight_and_stop_ads():
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

    pacific_today = helpers.get_pacific_now().date()
    previous_start_date = models.AdGroupRotation.objects.filter(
        start_date__lte=pacific_today,
    ).values_list('start_date', flat=True).order_by('-start_date').distinct()[1]
    ad_group_ids = models.AdGroupRotation.objects.filter(
        start_date=previous_start_date
    ).values_list('ad_group_id', flat=True)
    for ad_group_id in ad_group_ids:
        _set_ad_group(ad_group_id, 'INACTIVE')


def recalculate_and_set_new_daily_budgets(ad_group_id):
    local_now = dates_helper.local_now()  # assume budget rotation happens midnight eastern
    local_midnight_today = datetime.datetime(local_now.year, local_now.month, local_now.day)
    utc_start = dates_helper.local_to_utc_time(local_midnight_today)

    local_midnight_tomorrow = local_midnight_today + datetime.timedelta(days=1)
    utc_end = dates_helper.local_to_utc_time(local_midnight_tomorrow)

    num_content_ads = dash.models.ContentAd.objects.filter(
        ad_group_id=ad_group_id,
        created_dt__gte=utc_start,
        created_dt__lt=utc_end,
    ).count()

    num_candidates = dash.models.ContentAdCandidate.objects.filter(
        ad_group_id=ad_group_id,
        created_dt__gte=utc_start,
        created_dt__lt=utc_end,
    ).count()  # assume they're getting processed successfully

    new_rtb_daily_budget = max(
        (num_content_ads + num_candidates) * config.DAILY_BUDGET_PER_ARTICLE * 0.95,
        config.DAILY_BUDGET_INITIAL,
    )
    new_ob_daily_budget = max(
        (num_content_ads + num_candidates) * config.DAILY_BUDGET_PER_ARTICLE * 0.05,
        config.DAILY_BUDGET_INITIAL,
    )

    _set_rtb_daily_budget(ad_group_id, math.ceil(new_rtb_daily_budget))
    _set_source_daily_budget(ad_group_id, 'outbrain', math.ceil(new_ob_daily_budget))


@transaction.atomic
def _rotate_ad_groups(start_date):
    ad_group_name = AD_GROUP_NAME_TEMPLATE.format(
        start_date=start_date,
    )
    ad_group_id = _create_ad_group(ad_group_name, start_date)
    _persist_ad_group_rotation(start_date, ad_group_id)


def _create_ad_group(name, start_date):
    data = {
        'campaignId': config.AUTOMATION_CAMPAIGN,
        'name': name,
        'state': 'INACTIVE',
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
                'included': [cat.upper() for cat in config.INTEREST_TARGETING]
            },
        }
    }
    url = 'rest/v1/adgroups/'
    ad_group_id = int(_make_restapi_fake_post_request(restapi.views.AdGroupViewList, url, data)['id'])
    _set_initial_sources_settings(ad_group_id)
    _set_initial_rtb_settings(ad_group_id)
    _set_ad_group(ad_group_id, 'ACTIVE')

    return ad_group_id


def _set_ad_group(ad_group_id, state):
    data = {
        'state': state,
    }
    url = 'rest/v1/adgroups/{}/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.views.AdGroupViewDetails, url, data, view_args=[ad_group_id])


def _list_ad_group_sources(ad_group_id):
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_get_request(restapi.views.AdGroupSourcesViewList, url, view_args=[ad_group_id])


def _set_initial_rtb_settings(ad_group_id):
    return _set_rtb_daily_budget(ad_group_id, config.DAILY_BUDGET_INITIAL)


def _set_initial_sources_settings(ad_group_id):
    sources = _list_ad_group_sources(ad_group_id)
    data = [{
        'source': source['source'],
        'dailyBudget': config.DAILY_BUDGET_INITIAL,
        'cpc': config.DEFAULT_CPC,
        'state': 'ACTIVE',
    } for source in sources]
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.views.AdGroupSourcesViewList, url, data, view_args=[ad_group_id])


def _set_source_daily_budget(ad_group_id, source, daily_budget):
    data = [{
        'source': source,
        'dailyBudget': daily_budget,
        'state': 'ACTIVE',
    }]
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.views.AdGroupSourcesViewList, url, data, view_args=[ad_group_id])


def _set_rtb_daily_budget(ad_group_id, daily_budget):
    data = {
        'groupEnabled': True,
        'dailyBudget': daily_budget,
        'state': 'ACTIVE',
    }
    url = 'rest/v1/adgroups/{}/sources/rtb/'.format(ad_group_id)
    return _make_restapi_fake_put_request(
        restapi.views.AdGroupSourcesRTBViewDetails, url, data, view_args=[ad_group_id])


def _persist_ad_group_rotation(start_date, ad_group_id):
    if models.AdGroupRotation.objects.filter(start_date__gte=start_date):
        raise Exception('Ad group already exists')

    models.AdGroupRotation.objects.create(
        ad_group_id=ad_group_id,
        start_date=start_date,
    )


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
