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
from integrations.bizwire.internal import helpers, reprocess

import restapi.views
import restapi.adgroupsource.views

from utils import dates_helper
from utils import k1_helper

from zemauth.models import User

AD_GROUP_NAME_TEMPLATE = '{start_date} - DEFAULT TARGETING'


def _is_pacific_midnight():
    return _is_pacific_hour(0)


def _is_pacific_hour(hour):
    pacific_now = helpers.get_pacific_now()
    return pacific_now.hour == hour


def _is_local_midnight():
    local_now = dates_helper.local_now()
    return local_now.hour == 0


def _is_day_before_new_rotation():
    return True  # TODO: define days when rotation happens


def _should_create_new_ad_groups():
    return _is_pacific_midnight() and _is_day_before_new_rotation()


def reprocess_missing_articles():
    missing_keys = reprocess.get_missing_keys()
    reprocess.purge_candidates(missing_keys)
    reprocess.invoke_lambdas(missing_keys)


def check_pacific_noon_and_stop_ads():
    if not _is_pacific_hour(12):
        return

    todays_ad_groups = _get_todays_ad_groups()

    utc_now = dates_helper.utc_now()
    content_ads = dash.models.ContentAd.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        created_dt__lt=datetime.datetime(utc_now.year, utc_now.month, utc_now.day, utc_now.hour),
        state=dash.constants.ContentAdSourceState.ACTIVE,
    ).exclude(ad_group__in=todays_ad_groups)
    dash.api.update_content_ads_state(content_ads, dash.constants.ContentAdSourceState.INACTIVE, None)

    ad_group_ids = set(ca.ad_group_id for ca in content_ads)
    k1_helper.update_ad_groups(ad_group_ids, msg="bizwire.rotate_adgroup")


def _get_todays_ad_groups():
    pacific_today = helpers.get_pacific_now().date()
    todays_ad_groups = models.AdGroupRotation.objects.filter(
        start_date=pacific_today,
    )

    return todays_ad_groups


def check_time_and_create_new_ad_groups():
    if not _should_create_new_ad_groups():
        return

    start_date = datetime.date.today() + datetime.timedelta(days=1)
    _rotate_ad_groups(start_date)


def check_date_and_stop_old_ad_groups():
    if not _is_pacific_hour(12):
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


def check_local_midnight_and_recalculate_daily_budgets():
    # NOTE: if no article is uploaded at midnight, daily budgets will stay the same
    # as before, potentially causing overspend, so we recalculate at midnight
    if not _is_local_midnight():
        return

    ad_group_id = helpers.get_current_ad_group_id()
    recalculate_and_set_new_daily_budgets(ad_group_id)


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

    num_content_ads += dash.models.ContentAdCandidate.objects.filter(
        ad_group_id=ad_group_id,
        created_dt__gte=utc_start,
        created_dt__lt=utc_end,
    ).count()  # assume candidates are getting processed successfully

    rtb_cost_per_article = config.DAILY_BUDGET_PER_ARTICLE * (1 - config.OB_DAILY_BUDGET_PCT)
    new_rtb_daily_budget = config.DAILY_BUDGET_RTB_INITIAL + num_content_ads * rtb_cost_per_article

    ob_cost_per_article = config.DAILY_BUDGET_PER_ARTICLE * config.OB_DAILY_BUDGET_PCT
    new_ob_daily_budget = config.DAILY_BUDGET_OB_INITIAL + num_content_ads * ob_cost_per_article

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
        },
        'autopilot': {
            'state': 'INACTIVE',
        }
    }
    url = 'rest/v1/adgroups/'
    ad_group_id = int(_make_restapi_fake_post_request(restapi.views.AdGroupViewList, url, data)['id'])
    _set_initial_sources_settings(ad_group_id)
    _set_initial_rtb_settings(ad_group_id)
    _set_ad_group(ad_group_id, 'ACTIVE')
    _set_custom_cpcs(ad_group_id)
    _set_all_rtb_default_cpc(ad_group_id)

    k1_helper.update_ad_group(ad_group_id, msg="bizwire.create_adgroup")
    return ad_group_id


def _set_ad_group(ad_group_id, state):
    data = {
        'state': state,
    }
    url = 'rest/v1/adgroups/{}/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.views.AdGroupViewDetails, url, data, view_args=[ad_group_id])


def _set_custom_cpcs(ad_group_id):
    for source_id, custom_cpc in config.CUSTOM_CPC_SETTINGS.items():
        current_settings = dash.models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id
        ).get_current_settings()

        new_settings = current_settings.copy_settings()
        new_settings.cpc_cc = custom_cpc
        new_settings.save(None)


def _set_all_rtb_default_cpc(ad_group_id):
    # HACK: when restapi supports setting all rtb cpc, this can be removed
    current_settings = dash.models.AdGroup.objects.get(id=ad_group_id).get_current_settings()
    if current_settings.b1_sources_group_cpc_cc == config.DEFAULT_CPC:
        return

    new_settings = current_settings.copy_settings()
    new_settings.b1_sources_group_cpc_cc = config.DEFAULT_CPC
    new_settings.save(None)


def _list_ad_group_sources(ad_group_id):
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_get_request(restapi.adgroupsource.views.AdGroupSourcesViewList, url, view_args=[ad_group_id])


def _set_initial_rtb_settings(ad_group_id):
    return _set_rtb_daily_budget(ad_group_id, config.DAILY_BUDGET_RTB_INITIAL)


def _set_initial_sources_settings(ad_group_id):
    sources = _list_ad_group_sources(ad_group_id)
    data = [{
        'source': source['source'],
        'dailyBudget': config.DAILY_BUDGET_OB_INITIAL,
        'cpc': config.DEFAULT_CPC,
        'state': 'ACTIVE',
    } for source in sources]
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.adgroupsource.views.AdGroupSourcesViewList, url, data, view_args=[ad_group_id])


def _set_source_daily_budget(ad_group_id, source, daily_budget):
    data = [{
        'source': source,
        'dailyBudget': daily_budget,
        'state': 'ACTIVE',
    }]
    url = 'rest/v1/adgroups/{}/sources/'.format(ad_group_id)
    return _make_restapi_fake_put_request(restapi.adgroupsource.views.AdGroupSourcesViewList, url, data, view_args=[ad_group_id])


def _set_rtb_daily_budget(ad_group_id, daily_budget):
    data = {
        'groupEnabled': True,
        'dailyBudget': daily_budget,
        'cpc': config.DEFAULT_CPC,
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
