# -*- coding: utf-8 -*-
import datetime
import json
import decimal
import logging
import base64
import http.client
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import pytz
from functools import partial

from django.db.models import Q
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404

import influx

from dash.views import helpers

from utils import lc_helper
from utils import api_common
from utils import exc
from utils import email_helper
from utils import request_signer
from utils import threads
from utils import db_for_reads

from automation import campaign_stop

import core.multicurrency
import core.entity.helpers

from dash import models, region_targeting_helper, retargeting_helper, campaign_goals
from dash import constants
from dash import forms
from dash import infobox_helpers

import stats.helpers

import analytics.projections

logger = logging.getLogger(__name__)

YAHOO_DASH_URL = 'https://gemini.yahoo.com/advertiser/{advertiser_id}/campaign/{campaign_id}'
OUTBRAIN_DASH_URL = 'https://my.outbrain.com/amplify/site/marketers/{marketer_id}/reports/content?campaignId={campaign_id}'
FACEBOOK_DASH_URL = 'https://business.facebook.com/ads/manager/campaign/?ids={campaign_id}&business_id={business_id}'

CAMPAIGN_NOT_CONFIGURED_SCENARIOS = {
    'multiple_missing': {
        'message': 'You are not able to add an ad group because campaign is missing some required configuration.',
        'action_text': 'Configure the campaign',
        'url_postfix': '',
    },
    'goal_missing': {
        'message': 'You are not able to add an ad group because campaign goal is not defined.',
        'action_text': 'Configure the campaign goal',
        'url_postfix': '&settingsScrollTo=zemCampaignGoalsSettings',
    },
    'language_missing': {
        'message': 'You are not able to add an ad group because campaign language is not defined.',
        'action_text': 'Configure the campaign language',
        'url_postfix': '&settingsScrollTo=zemCampaignGeneralSettings',
    },
}


def index(request):
    associated_agency = models.Agency.objects.all().filter(
        Q(users__id=request.user.id) | Q(account__users__id=request.user.id)
    ).first()
    return render(request, 'index.html', {
        'staticUrl': settings.CLIENT_STATIC_URL,
        'debug': settings.DEBUG,
        'whitelabel': associated_agency and associated_agency.whitelabel,
        'custom_favicon_url': associated_agency and associated_agency.custom_favicon_url,
        'custom_dashboard_title': associated_agency and associated_agency.custom_dashboard_title,
    })


def supply_dash_redirect(request):
    # We do not authorization validation here since it only redirects to third-party
    # dashboards and if user can't access them, there is no harm done.
    ad_group_id = request.GET.get('ad_group_id')
    source_id = request.GET.get('source_id')

    validation_errors = {}
    if not ad_group_id:
        validation_errors['ad_group_id'] = 'Missing param ad_group_id.'

    if not source_id:
        validation_errors['source_id'] = 'Missing param source_id.'

    if validation_errors:
        raise exc.ValidationError(errors=validation_errors)

    try:
        ad_group_source = models.AdGroupSource.objects.get(
            ad_group__id=int(ad_group_id), source__id=int(source_id))
    except models.AdGroupSource.DoesNotExist:
        raise Http404()

    credentials = ad_group_source.source_credentials and ad_group_source.source_credentials.decrypt()
    if ad_group_source.source.source_type.type == constants.SourceType.YAHOO:
        url = YAHOO_DASH_URL.format(
            advertiser_id=json.loads(credentials)['advertiser_id'],
            campaign_id=ad_group_source.source_campaign_key
        )
    elif ad_group_source.source.source_type.type == constants.SourceType.OUTBRAIN:
        if 'campaign_id' not in ad_group_source.source_campaign_key:
            raise Http404()
        url = OUTBRAIN_DASH_URL.format(
            campaign_id=ad_group_source.source_campaign_key['campaign_id'],
            marketer_id=str(ad_group_source.source_campaign_key['marketer_id'])
        )
    elif ad_group_source.source.source_type.type == constants.SourceType.FACEBOOK:
        url = FACEBOOK_DASH_URL.format(
            campaign_id=ad_group_source.source_campaign_key,
            business_id=json.loads(credentials)['business_id'],
        )
    else:
        raise exc.MissingDataError()

    return render(request, 'redirect.html', {'url': url})


class User(api_common.BaseApiView):

    @influx.timer('dash.api')
    def get(self, request, user_id):
        response = {}

        if user_id == 'current':
            response['user'] = self.get_dict(request.user)

        return self.create_api_response(response)

    def get_dict(self, user):
        if not user:
            return {}

        agency = helpers.get_user_agency(user)
        return {
            'id': str(user.pk),
            'email': user.email,
            'name': user.get_full_name(),
            'agency': agency.id if agency else None,
            'permissions': user.get_all_permissions_with_access_levels(),
            'timezone_offset': pytz.timezone(settings.DEFAULT_TIME_ZONE).utcoffset(
                datetime.datetime.utcnow(), is_dst=True).total_seconds()
        }


class AccountArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)
        account.archive(request)
        return self.create_api_response({})


class AccountRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.restore(request)
        return self.create_api_response({})


class CampaignArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.archive(request)
        return self.create_api_response({})


class CampaignRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.restore(request)

        return self.create_api_response({})


class AdGroupOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    @db_for_reads.use_stats_read_replica()
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        use_local_currency = request.user.has_perm('zemauth.can_see_infobox_in_local_currency')
        async_perf_query = threads.AsyncFunction(
            partial(
                infobox_helpers.get_yesterday_adgroup_spend,
                request.user,
                ad_group,
                use_local_currency
            )
        )
        async_perf_query.start()

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        ad_group_settings = ad_group.get_current_settings()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        ad_group_running_status = infobox_helpers.get_adgroup_running_status(
            request.user, ad_group, filtered_sources)

        header = {
            'title': ad_group.name,
            'active': ad_group_running_status,
            'level': constants.InfoboxLevel.ADGROUP,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ADGROUP)),
        }

        delivery = {
            'status': ad_group_running_status,
            'text': infobox_helpers.get_entity_delivery_text(ad_group_running_status)
        }

        basic_settings = self._basic_settings(request.user, ad_group, ad_group_settings)
        performance_settings = self._performance_settings(
            ad_group, request.user, ad_group_settings, start_date, end_date,
            async_perf_query, filtered_sources
        )
        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'delivery': delivery,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }
        return self.create_api_response(response)

    def _basic_settings(self, user, ad_group, ad_group_settings):
        settings = []

        flight_time, flight_time_left_days =\
            infobox_helpers.format_flight_time(
                ad_group_settings.start_date,
                ad_group_settings.end_date
            )
        days_left_description = None
        if flight_time_left_days is not None:
            days_left_description = "{} days left".format(flight_time_left_days)
        flight_time_setting = infobox_helpers.OverviewSetting(
            'Flight time:',
            flight_time,
            days_left_description
        )
        settings.append(flight_time_setting.as_dict())

        return settings

    def _performance_settings(self, ad_group, user, ad_group_settings, start_date, end_date,
                              async_query, filtered_sources):
        settings = []

        use_local_currency = user.has_perm('zemauth.can_see_infobox_in_local_currency')
        currency = ad_group.campaign.account.currency if use_local_currency else constants.Currency.USD

        yesterday_costs = async_query.join_and_get_result() or 0
        daily_cap = infobox_helpers.calculate_daily_ad_group_cap(ad_group, use_local_currency)

        settings.append(infobox_helpers.create_yesterday_spend_setting(
            yesterday_costs,
            daily_cap,
            currency,
            uses_bcm_v2=ad_group.campaign.account.uses_bcm_v2
        ).as_dict())

        if user.has_perm('zemauth.campaign_goal_performance'):
            settings.extend(infobox_helpers.get_primary_campaign_goal_ad_group(
                user,
                ad_group,
                start_date,
                end_date,
                currency,
                use_local_currency,
            ))

        return settings


class AdGroupArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.archive(request)
        return self.create_api_response({})


class AdGroupRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.restore(request)

        return self.create_api_response({})


class CampaignAdGroups(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        self._validate_campaign_ready(request, campaign)
        ad_group = core.entity.AdGroup.objects.create(request, campaign, is_restapi=self.rest_proxy)
        return self.create_api_response({'name': ad_group.name, 'id': ad_group.id})

    @staticmethod
    def _validate_campaign_ready(request, campaign):
        primary_goal = campaign_goals.get_primary_campaign_goal(campaign)
        scenario = None

        if not primary_goal and not campaign.settings.language:
            scenario = 'multiple_missing'
        elif not primary_goal:
            scenario = 'goal_missing'
        elif not campaign.settings.language:
            scenario = 'language_missing'

        if scenario:
            url = request.build_absolute_uri(
                '/v2/analytics/campaign/{}?settings'.format(
                    campaign.id,
                )
            ) + CAMPAIGN_NOT_CONFIGURED_SCENARIOS[scenario]['url_postfix']
            raise exc.ValidationError(
                data={
                    'message': CAMPAIGN_NOT_CONFIGURED_SCENARIOS[scenario]['message'],
                    'action': {
                        'text': CAMPAIGN_NOT_CONFIGURED_SCENARIOS[scenario]['action_text'],
                        'url': url,
                    }
                }
            )


class CampaignOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    @db_for_reads.use_stats_read_replica()
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_settings = campaign.get_current_settings()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        campaign_running_status = infobox_helpers.get_campaign_running_status(campaign)

        header = {
            'title': campaign.name,
            'active': campaign_running_status,
            'level': constants.InfoboxLevel.CAMPAIGN,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.CAMPAIGN)),
        }

        delivery = {
            'status': campaign_running_status,
            'text': infobox_helpers.get_entity_delivery_text(campaign_running_status)
        }

        basic_settings = self._basic_settings(request.user, campaign, campaign_settings)

        performance_settings = self._performance_settings(
            campaign,
            request.user,
            campaign_settings,
            start_date,
            end_date,
        )

        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'delivery': delivery,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }
        return self.create_api_response(response)

    @influx.timer('dash.api')
    def _basic_settings(self, user, campaign, campaign_settings):
        settings = []

        campaign_manager_setting = infobox_helpers.OverviewSetting(
            'Campaign Manager:',
            infobox_helpers.format_username(campaign_settings.campaign_manager)
        )
        settings.append(campaign_manager_setting.as_dict())

        start_date, end_date, never_finishes = self._calculate_flight_dates(
            campaign
        )
        if never_finishes:
            end_date = None

        flight_time, flight_time_left_days =\
            infobox_helpers.format_flight_time(
                start_date,
                end_date
            )
        flight_time_left_description = None
        if flight_time_left_days is not None:
            flight_time_left_description = "{} days left".format(flight_time_left_days)
        flight_time_setting = infobox_helpers.OverviewSetting(
            'Flight time:',
            flight_time,
            flight_time_left_description
        )
        settings.append(flight_time_setting.as_dict())

        use_local_currency = user.has_perm('zemauth.can_see_infobox_in_local_currency')
        currency = campaign.account.currency if use_local_currency else constants.Currency.USD
        currency_symbol = core.multicurrency.get_currency_symbol(currency)

        total_spend = infobox_helpers.get_total_campaign_budgets_amount(user, campaign)
        total_spend_available = infobox_helpers.calculate_available_campaign_budget(campaign, use_local_currency)
        campaign_budget_setting = infobox_helpers.OverviewSetting(
            'Campaign budget:',
            lc_helper.format_currency(total_spend, curr=currency_symbol),
            '{} remaining'.format(
                lc_helper.format_currency(total_spend_available, curr=currency_symbol)
            ),
            tooltip="Campaign media budget"
        )
        settings.append(campaign_budget_setting.as_dict())
        return settings

    @influx.timer('dash.api')
    def _performance_settings(self, campaign, user, campaign_settings, start_date, end_date):
        settings = []

        monthly_proj = analytics.projections.CurrentMonthBudgetProjections(
            'campaign',
            campaign=campaign
        )

        pacing = monthly_proj.total('pacing') or decimal.Decimal('0')

        use_local_currency = user.has_perm('zemauth.can_see_infobox_in_local_currency')
        currency = campaign.account.currency if use_local_currency else constants.Currency.USD
        currency_symbol = core.multicurrency.get_currency_symbol(currency)

        daily_cap = infobox_helpers.calculate_daily_campaign_cap(campaign, use_local_currency)
        yesterday_costs = infobox_helpers.get_yesterday_campaign_spend(user, campaign, use_local_currency) or 0
        settings.append(infobox_helpers.create_yesterday_spend_setting(
            yesterday_costs,
            daily_cap,
            currency,
            uses_bcm_v2=campaign.account.uses_bcm_v2
        ).as_dict())

        attributed_media_spend = monthly_proj.total('attributed_media_spend')
        if attributed_media_spend is not None:
            settings.append(infobox_helpers.OverviewSetting(
                'Campaign pacing:',
                lc_helper.format_currency(attributed_media_spend, curr=currency_symbol),
                description='{:.2f}% on plan'.format(pacing or 0),
                tooltip='Campaign pacing for the current month'
            ).as_dict())

        if user.has_perm('zemauth.campaign_goal_performance'):
            settings.extend(infobox_helpers.get_primary_campaign_goal(
                user,
                campaign,
                start_date,
                end_date,
                currency,
                use_local_currency,
            ))

        return settings

    def _calculate_flight_dates(self, campaign):
        start_date = None
        end_date = None
        never_finishes = False

        ad_groups_settings = models.AdGroupSettings.objects.filter(
            ad_group__campaign=campaign
        ).group_current_settings().values_list('start_date', 'end_date')
        for ad_group_settings in ad_groups_settings:
            adg_start_date = ad_group_settings[0]
            adg_end_date = ad_group_settings[1]

            if start_date is None:
                start_date = adg_start_date
            else:
                start_date = min(start_date, adg_start_date)

            if adg_end_date is None:
                never_finishes = True

            if end_date is None:
                end_date = adg_end_date
            else:
                end_date = max(end_date, adg_end_date or end_date)

        return start_date, end_date, never_finishes


class AccountOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    @db_for_reads.use_stats_read_replica()
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id, select_related_users=True)

        account_running_status = infobox_helpers.get_account_running_status(account)

        header = {
            'title': account.name,
            'active': account_running_status,
            'level': constants.InfoboxLevel.ACCOUNT,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ACCOUNT)),
        }

        delivery = {
            'status': account_running_status,
            'text': infobox_helpers.get_entity_delivery_text(account_running_status)
        }

        basic_settings = self._basic_settings(request.user, account)

        performance_settings = self._performance_settings(account, request.user)
        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'delivery': delivery,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }

        return self.create_api_response(response)

    def _basic_settings(self, user, account):
        settings = []

        account_settings = account.get_current_settings()
        account_manager_setting = infobox_helpers.OverviewSetting(
            'Account Manager:',
            infobox_helpers.format_username(account_settings.default_account_manager)
        )
        settings.append(account_manager_setting.as_dict())

        sales_manager_setting_label = 'Sales Representative:'
        cs_manager_setting_label = 'CS Representative:'

        sales_manager_setting = infobox_helpers.OverviewSetting(
            sales_manager_setting_label,
            infobox_helpers.format_username(account_settings.default_sales_representative),
            tooltip='Sales Representative'
        )
        settings.append(sales_manager_setting.as_dict())

        cs_manager_setting = infobox_helpers.OverviewSetting(
            cs_manager_setting_label,
            infobox_helpers.format_username(account_settings.default_cs_representative),
            tooltip='Customer Success Representative'
        )
        settings.append(cs_manager_setting.as_dict())

        use_local_currency = user.has_perm('zemauth.can_see_infobox_in_local_currency')
        allocated_credit, available_credit =\
            infobox_helpers.calculate_allocated_and_available_credit(account, use_local_currency)

        if use_local_currency:
            currency_symbol = core.multicurrency.get_currency_symbol(account.currency)
            allocated_credit_text = lc_helper.format_currency(
                allocated_credit,
                curr=currency_symbol,
            )
            unallocated_credit_text = lc_helper.format_currency(
                available_credit,
                curr=currency_symbol,
            )
        else:
            allocated_credit_text = lc_helper.default_currency(allocated_credit)
            unallocated_credit_text = lc_helper.default_currency(
                available_credit
            )

        allocated_credit_setting = infobox_helpers.OverviewSetting(
            'Allocated credit:',
            allocated_credit_text,
            description='{} unallocated'.format(unallocated_credit_text),
            tooltip='Total allocated and unallocated credit',
        )
        settings.append(allocated_credit_setting.as_dict())

        return settings

    def _performance_settings(self, account, user):
        settings = []

        use_local_currency = user.has_perm('zemauth.can_see_infobox_in_local_currency')
        currency = account.currency if use_local_currency else constants.Currency.USD
        daily_budget = infobox_helpers.calculate_daily_account_cap(account, use_local_currency)
        yesterday_costs = infobox_helpers.get_yesterday_account_spend(account, use_local_currency)
        settings.append(
            infobox_helpers.create_yesterday_spend_setting(
                yesterday_costs,
                daily_budget,
                currency,
                uses_bcm_v2=account.uses_bcm_v2
            ).as_dict(),
        )

        return settings


class AvailableSources(api_common.BaseApiView):

    @influx.timer('dash.api')
    def get(self, request):
        user_accounts = models.Account.objects.all().filter_by_user(request.user)
        user_sources = (models.Source.objects.filter(account__in=user_accounts)
                        .filter(deprecated=False)
                        .distinct()
                        .only('id', 'name', 'deprecated'))

        sources = []
        for source in user_sources:
            sources.append({
                'id': str(source.id),
                'name': source.name,
                'deprecated': source.deprecated,
            })

        return self.create_api_response({
            'sources': sources
        })


class AdGroupSources(api_common.BaseApiView):

    @influx.timer('dash.api')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group_settings = ad_group.get_current_settings()

        allowed_sources = ad_group.campaign.account.allowed_sources.all()
        ad_group_sources = ad_group.sources.all()
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        sources_with_credentials = models.DefaultSourceSettings.objects.all().with_credentials().values('source')
        available_sources = allowed_sources.\
            exclude(pk__in=ad_group_sources).\
            filter(pk__in=filtered_sources).\
            filter(pk__in=sources_with_credentials).\
            order_by('name')

        sources = []
        for source in available_sources:
            sources.append({
                'id': source.id,
                'name': source.name,
                'can_target_existing_regions': region_targeting_helper.can_target_existing_regions(
                    source, ad_group_settings),
                'can_retarget': retargeting_helper.can_add_source_with_retargeting(source, ad_group_settings)
            })

        return self.create_api_response({
            'sources': sorted(sources, key=lambda source: source['name']),
            'sources_waiting': [],
        })

    @influx.timer('dash.api')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        source_id = json.loads(request.body)['source_id']
        source = models.Source.objects.get(id=source_id)

        core.entity.AdGroupSource.objects.create(request, ad_group, source, write_history=True, k1_sync=True)

        return self.create_api_response(None)


class Account(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_add_account'):
            raise exc.MissingDataError()

        agency = models.Agency.objects.all().filter(
            users=request.user
        ).first()

        account = models.Account.objects.create(
            request,
            name=core.entity.helpers.create_default_name(models.Account.objects, 'New account'),
            agency=agency,
        )

        response = {
            'name': account.name,
            'id': account.id
        }

        return self.create_api_response(response)


class AccountCampaigns(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_campaigns_view'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        name = core.entity.helpers.create_default_name(models.Campaign.objects.filter(account=account), 'New campaign')

        language = constants.Language.ENGLISH if self.rest_proxy else None
        campaign = models.Campaign.objects.create(request, account, name, language=language)

        response = {
            'name': campaign.name,
            'id': campaign.id
        }

        return self.create_api_response(response)


class AdGroupSourceSettings(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request, ad_group_id, source_id):
        resource = json.loads(request.body)
        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        try:
            ad_group_source = models.AdGroupSource.objects.get(ad_group=ad_group, source_id=source_id)
        except models.AdGroupSource.DoesNotExist:
            raise exc.MissingDataError(message='Requested source not found')

        form = forms.AdGroupSourceSettingsForm(resource)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        if (request.user.has_perm('zemauth.can_manage_settings_in_local_currency')):
            for field in ad_group_source.settings.multicurrency_fields:
                form.cleaned_data['local_{}'.format(field)] = form.cleaned_data.pop(field, None)

        data = {k: v for k, v in list(form.cleaned_data.items()) if v is not None}

        response = ad_group_source.settings.update(request, k1_sync=True, **data)

        allowed_sources = {source.id for source in ad_group.campaign.account.allowed_sources.all()}
        campaign_settings = ad_group.campaign.get_current_settings()
        ad_group_settings = ad_group.get_current_settings()

        return self.create_api_response({
            'editable_fields': helpers.get_editable_fields(
                ad_group,
                ad_group_source,
                ad_group_settings,
                ad_group_source.get_current_settings(),
                campaign_settings,
                allowed_sources,
                campaign_stop.can_enable_media_source(
                    ad_group_source, ad_group.campaign, campaign_settings, ad_group_settings)
            ),
            'autopilot_changed_sources': response['autopilot_changed_sources_text'],
            'enabling_autopilot_sources_allowed': helpers.enabling_autopilot_single_source_allowed(
                ad_group,
            )
        })


class AllAccountsOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    @db_for_reads.use_stats_read_replica()
    def get(self, request):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        # infobox only filters by agency and account type
        view_filter = helpers.ViewFilter(request=request)

        header = {
            'title': None,
            'level': constants.InfoboxLevel.ALL_ACCOUNTS,
            'level_verbose': constants.InfoboxLevel.get_text(constants.InfoboxLevel.ALL_ACCOUNTS),
        }

        performance_settings = []
        if request.user.has_perm('zemauth.can_access_all_accounts_infobox'):
            basic_settings = self._basic_all_accounts_settings(request.user, start_date, end_date, view_filter)
            performance_settings = self._append_performance_all_accounts_settings(
                performance_settings, request.user, view_filter
            )
            performance_settings = [setting.as_dict() for setting in performance_settings]
        elif request.user.has_perm('zemauth.can_access_agency_infobox'):
            basic_settings = self._basic_agency_settings(request.user, start_date, end_date, view_filter)
            performance_settings = self._append_performance_agency_settings(performance_settings, request.user)
            performance_settings = [setting.as_dict() for setting in performance_settings]
        else:
            raise exc.AuthorizationError()

        response = {
            'header': header,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings if len(performance_settings) > 0 else None
        }

        return self.create_api_response(response)

    def _basic_agency_settings(self, user, start_date, end_date, view_filter):
        settings = []
        count_active_accounts = infobox_helpers.count_active_agency_accounts(user)
        settings.append(infobox_helpers.OverviewSetting(
            'Active accounts:',
            count_active_accounts,
            section_start=True,
            tooltip='Number of accounts with at least one campaign running'
        ))

        return [setting.as_dict() for setting in settings]

    def _basic_all_accounts_settings(self, user, start_date, end_date, view_filter):
        settings = []

        constraints = {}
        if view_filter.filtered_agencies:
            constraints['campaign__account__agency__in']\
                = view_filter.filtered_agencies
        if view_filter.filtered_account_types:
            latest_accset = models.AccountSettings.objects.all().group_current_settings()
            latest_typed_accset = models.AccountSettings.objects.all().filter(
                id__in=latest_accset
            ).filter(
                account_type__in=view_filter.filtered_account_types
            ).values_list('account__id', flat=True)
            constraints['campaign__account__id__in'] = latest_typed_accset

        count_active_accounts = infobox_helpers.count_active_accounts(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        settings.append(infobox_helpers.OverviewSetting(
            'Active accounts:',
            count_active_accounts,
            section_start=True,
            tooltip='Number of accounts with at least one campaign running'
        ))

        weekly_logged_users = infobox_helpers.count_weekly_logged_in_users(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        settings.append(infobox_helpers.OverviewSetting(
            'Logged-in users:',
            weekly_logged_users,
            tooltip="Number of users who logged-in in the past 7 days"
        ))

        weekly_active_users = infobox_helpers.get_weekly_active_users(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        weekly_active_user_emails = [u.email for u in weekly_active_users]
        email_list_setting = infobox_helpers.OverviewSetting(
            'Active users:',
            '{}'.format(len(weekly_active_users)),
            tooltip='Users who made self-managed actions in the past 7 days'
        )

        if weekly_active_user_emails != []:
            email_list_setting = email_list_setting.comment(
                'Show more',
                '<br />'.join(weekly_active_user_emails),
            )
        settings.append(email_list_setting)

        weekly_sf_actions = infobox_helpers.count_weekly_selfmanaged_actions(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        settings.append(infobox_helpers.OverviewSetting(
            'Self-managed actions:',
            weekly_sf_actions,
            tooltip="Number of actions taken by self-managed users "
                    "in the past 7 days"
        ))

        return [setting.as_dict() for setting in settings]

    def _append_performance_agency_settings(self, overview_settings, user):
        accounts = models.Account.objects.all().filter_by_user(user)
        currency = stats.helpers.get_report_currency(
            user, accounts, permission='zemauth.can_see_infobox_in_local_currency')

        uses_bcm_v2 = accounts.all_use_bcm_v2()

        use_local_currency = currency != constants.Currency.USD
        yesterday_costs = infobox_helpers.get_yesterday_agency_spend(accounts, use_local_currency)
        yesterday_cost = yesterday_costs['yesterday_etfm_cost'] if uses_bcm_v2 else yesterday_costs['e_yesterday_cost']

        currency_symbol = core.multicurrency.get_currency_symbol(currency)
        overview_settings.append(infobox_helpers.OverviewSetting(
            'Yesterday spend:',
            lc_helper.format_currency(yesterday_cost, curr=currency_symbol),
            tooltip='Yesterday spend' if uses_bcm_v2 else 'Yesterday media spend',
            section_start=True
        ))

        mtd_costs = infobox_helpers.get_mtd_agency_spend(accounts, use_local_currency)
        mtd_cost = mtd_costs['etfm_cost'] if uses_bcm_v2 else mtd_costs['e_media_cost']
        overview_settings.append(infobox_helpers.OverviewSetting(
            'Month-to-date spend:',
            lc_helper.format_currency(mtd_cost, curr=currency_symbol),
            tooltip='Month-to-date spend' if uses_bcm_v2 else 'Month-to-date media spend'))

        return overview_settings

    def _append_performance_all_accounts_settings(self, overview_settings, user, view_filter):
        accounts = models.Account.objects\
                                 .filter_by_user(user)\
                                 .filter_by_agencies(view_filter.filtered_agencies)\
                                 .filter_by_account_types(view_filter.filtered_account_types)
        currency = stats.helpers.get_report_currency(
            user, accounts, permission='zemauth.can_see_infobox_in_local_currency')

        use_local_currency = currency != constants.Currency.USD
        yesterday_costs = infobox_helpers.get_yesterday_all_accounts_spend(
            accounts,
            use_local_currency,
        )

        uses_bcm_v2 = settings.ALL_ACCOUNTS_USE_BCM_V2
        yesterday_cost = yesterday_costs['yesterday_etfm_cost'] if uses_bcm_v2 else yesterday_costs['e_yesterday_cost']

        currency_symbol = core.multicurrency.get_currency_symbol(currency)
        overview_settings.append(infobox_helpers.OverviewSetting(
            'Yesterday spend:',
            lc_helper.format_currency(yesterday_cost, curr=currency_symbol),
            tooltip='Yesterday spend' if uses_bcm_v2 else 'Yesterday media spend',
            section_start=True
        ))

        mtd_costs = infobox_helpers.get_mtd_all_accounts_spend(
            accounts,
            use_local_currency,
        )
        mtd_cost = mtd_costs['etfm_cost'] if uses_bcm_v2 else mtd_costs['e_media_cost']
        overview_settings.append(infobox_helpers.OverviewSetting(
            'Month-to-date spend:',
            lc_helper.format_currency(mtd_cost, curr=currency_symbol),
            tooltip='Month-to-date spend' if uses_bcm_v2 else 'Month-to-date media spend'))

        return overview_settings


class Demo(api_common.BaseApiView):

    def get(self, request):
        if not request.user.has_perm('zemauth.can_request_demo_v3'):
            raise Http404('Forbidden')

        instance = self._start_instance()

        email_helper.send_official_email(
            agency_or_user=request.user,
            recipient_list=[request.user.email],
            **email_helper.params_from_template(
                constants.EmailTemplateType.DEMO_RUNNING,
                **instance
            )
        )

        return self.create_api_response(instance)

    def _start_instance(self):
        request = urllib.request.Request(settings.DK_DEMO_UP_ENDPOINT)
        response = request_signer.urllib_secure_open(request, settings.DK_API_KEY)

        status_code = response.getcode()
        if status_code != 200:
            raise Exception('Invalid response status code. status code: {}'.format(status_code))

        ret = json.loads(response.read())
        if ret['status'] != 'success':
            raise Exception('Request not successful. status: {}'.format(ret['status']))

        return {
            'url': ret.get('instance_url'),
            'password': ret.get('instance_password'),
        }


def healthcheck(request):
    return HttpResponse('OK')


def oauth_authorize(request, source_name):
    credentials_id = request.GET.get('credentials_id')

    if not credentials_id:
        logger.warning('Missing credentials id')
        return redirect('index')

    credentials = models.SourceCredentials.objects.get(id=credentials_id)
    decrypted = json.loads(credentials.decrypt())

    if 'client_id' not in decrypted or 'client_secret' not in decrypted:
        logger.error('client_id and/or client_secret not in credentials')
        return redirect('index')

    state = {
        'credentials_id': credentials_id,
    }

    redirect_uri = request.build_absolute_uri(reverse('source.oauth.redirect', kwargs={'source_name': source_name}))
    redirect_uri = redirect_uri.replace('http://', 'https://')

    params = {
        'client_id': decrypted['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'state': base64.b64encode(json.dumps(state))
    }

    url = settings.SOURCE_OAUTH_URIS[source_name]['auth_uri'] + '?' + urllib.parse.urlencode(params)
    return redirect(url)


def oauth_redirect(request, source_name):
    # Token requests are implemented using urllib2 requests because Yahoo only supports credentials in
    # Authorization header while oauth2client sends it in reqeust body (for get_token calls, after that
    # it puts access token into header).

    code = request.GET.get('code')
    state = request.GET.get('state')

    if not state:
        logger.error('Missing state in OAuth2 redirect')
        return redirect('index')

    try:
        state = json.loads(base64.b64decode(state))
    except (TypeError, ValueError):
        logger.error('Invalid state in OAuth2 redirect')
        return redirect('index')

    credentials = models.SourceCredentials.objects.get(id=state['credentials_id'])
    decrypted = json.loads(credentials.decrypt())

    redirect_uri = request.build_absolute_uri(reverse('source.oauth.redirect', kwargs={'source_name': source_name}))
    redirect_uri = redirect_uri.replace('http://', 'https://')

    headers = {
        'Authorization': 'Basic {}'.format(base64.b64encode(decrypted['client_id'] + ':' + decrypted['client_secret']))
    }

    data = {
        'redirect_uri': redirect_uri,
        'code': code,
        'grant_type': 'authorization_code'
    }

    req = urllib.request.Request(
        settings.SOURCE_OAUTH_URIS[source_name]['token_uri'],
        data=urllib.parse.urlencode(data),
        headers=headers
    )
    r = urllib.request.urlopen(req)

    if r.getcode() == http.client.OK:
        decrypted['oauth_tokens'] = json.loads(r.read())
        decrypted['oauth_created_dt'] = datetime.datetime.utcnow().isoformat()
        credentials.credentials = json.dumps(decrypted)
        credentials.save()

    return redirect(reverse('admin:dash_sourcecredentials_change', args=(credentials.id,)))


class LiveStreamAllow(api_common.BaseApiView):

    def post(self, request):
        data = json.loads(request.body)
        email_helper.send_livestream_email(request.user, data['session_url'])
        return self.create_api_response({})
