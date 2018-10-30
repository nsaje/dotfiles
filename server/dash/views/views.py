# -*- coding: utf-8 -*-
import base64
import datetime
import decimal
import http.client
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from functools import partial

import influx
import pytz
from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

import analytics.projections
import core.features.multicurrency
import core.models.ad_group_source.exceptions
import core.models.helpers
import core.models.settings.ad_group_source_settings.exceptions
import stats.helpers
from dash import campaign_goals
from dash import constants
from dash import forms
from dash import infobox_helpers
from dash import models
from dash import region_targeting_helper
from dash import retargeting_helper
from dash.features import native_server
from dash.views import helpers
from utils import api_common
from utils import db_for_reads
from utils import email_helper
from utils import exc
from utils import lc_helper
from utils import request_signer
from utils import threads

logger = logging.getLogger(__name__)

YAHOO_DASH_URL = "https://gemini.yahoo.com/advertiser/{advertiser_id}/campaign/{campaign_id}"
OUTBRAIN_DASH_URL = (
    "https://my.outbrain.com/amplify/site/marketers/{marketer_id}/reports/content?campaignId={campaign_id}"
)
FACEBOOK_DASH_URL = "https://business.facebook.com/ads/manager/campaign/?ids={campaign_id}&business_id={business_id}"

CAMPAIGN_NOT_CONFIGURED_SCENARIOS = {
    "multiple_missing": {
        "message": "You are not able to add an ad group because campaign is missing some required configuration.",
        "action_text": "Configure the campaign",
        "url_postfix": "",
    },
    "goal_missing": {
        "message": "You are not able to add an ad group because campaign goal is not defined.",
        "action_text": "Configure the campaign goal",
        "url_postfix": "&settingsScrollTo=zemCampaignGoalsSettings",
    },
    "language_missing": {
        "message": "You are not able to add an ad group because campaign language is not defined.",
        "action_text": "Configure the campaign language",
        "url_postfix": "&settingsScrollTo=zemCampaignGeneralSettings",
    },
    "type_missing": {
        "message": "You are not able to add an ad group because campaign type is not defined.",
        "action_text": "Configure the campaign type",
        "url_postfix": "&settingsScrollTo=zemCampaignGeneralSettings",
    },
}


def index(request):
    associated_agency = (
        models.Agency.objects.all().filter(Q(users__id=request.user.id) | Q(account__users__id=request.user.id)).first()
    )
    return render(
        request,
        "index.html",
        {
            "staticUrl": settings.CLIENT_STATIC_URL,
            "debug": settings.DEBUG,
            "whitelabel": associated_agency and associated_agency.whitelabel,
            "custom_favicon_url": associated_agency and associated_agency.custom_favicon_url,
            "custom_dashboard_title": associated_agency and associated_agency.custom_dashboard_title,
        },
    )


def supply_dash_redirect(request):
    # We do not authorization validation here since it only redirects to third-party
    # dashboards and if user can't access them, there is no harm done.
    ad_group_id = request.GET.get("ad_group_id")
    source_id = request.GET.get("source_id")

    validation_errors = {}
    if not ad_group_id:
        validation_errors["ad_group_id"] = "Missing param ad_group_id."

    if not source_id:
        validation_errors["source_id"] = "Missing param source_id."

    if validation_errors:
        raise exc.ValidationError(errors=validation_errors)

    try:
        ad_group_source = models.AdGroupSource.objects.select_related("ad_group__campaign__account__yahoo_account").get(
            ad_group__id=int(ad_group_id), source__id=int(source_id)
        )
    except models.AdGroupSource.DoesNotExist:
        raise Http404()

    credentials = ad_group_source.source_credentials and ad_group_source.source_credentials.decrypt()
    if ad_group_source.source.source_type.type == constants.SourceType.YAHOO:
        url = YAHOO_DASH_URL.format(
            advertiser_id=ad_group_source.ad_group.campaign.account.yahoo_account.advertiser_id,
            campaign_id=ad_group_source.source_campaign_key,
        )
    elif ad_group_source.source.source_type.type == constants.SourceType.OUTBRAIN:
        if "campaign_id" not in ad_group_source.source_campaign_key:
            raise Http404()
        url = OUTBRAIN_DASH_URL.format(
            campaign_id=ad_group_source.source_campaign_key["campaign_id"],
            marketer_id=str(ad_group_source.source_campaign_key["marketer_id"]),
        )
    elif ad_group_source.source.source_type.type == constants.SourceType.FACEBOOK:
        url = FACEBOOK_DASH_URL.format(
            campaign_id=ad_group_source.source_campaign_key, business_id=json.loads(credentials)["business_id"]
        )
    else:
        raise exc.MissingDataError()

    return render(request, "redirect.html", {"url": url})


class User(api_common.BaseApiView):
    @influx.timer("dash.api")
    def get(self, request, user_id):
        response = {}

        if user_id == "current":
            response["user"] = self.get_dict(request.user)

        return self.create_api_response(response)

    def get_dict(self, user):
        if not user:
            return {}

        agency = helpers.get_user_agency(user)
        return {
            "id": str(user.pk),
            "email": user.email,
            "name": user.get_full_name(),
            "agency": agency.id if agency else None,
            "permissions": user.get_all_permissions_with_access_levels(),
            "timezone_offset": pytz.timezone(settings.DEFAULT_TIME_ZONE)
            .utcoffset(datetime.datetime.utcnow(), is_dst=True)
            .total_seconds(),
        }


class AccountArchive(api_common.BaseApiView):
    @influx.timer("dash.api")
    def post(self, request, account_id):
        if not request.user.has_perm("zemauth.archive_restore_entity"):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)
        account.archive(request)
        return self.create_api_response({})


class AccountRestore(api_common.BaseApiView):
    @influx.timer("dash.api")
    def post(self, request, account_id):
        if not request.user.has_perm("zemauth.archive_restore_entity"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.restore(request)
        return self.create_api_response({})


class CampaignArchive(api_common.BaseApiView):
    @influx.timer("dash.api")
    def post(self, request, campaign_id):
        if not request.user.has_perm("zemauth.archive_restore_entity"):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.archive(request)
        return self.create_api_response({})


class CampaignRestore(api_common.BaseApiView):
    @influx.timer("dash.api")
    def post(self, request, campaign_id):
        if not request.user.has_perm("zemauth.archive_restore_entity"):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.restore(request)

        return self.create_api_response({})


class AdGroupOverview(api_common.BaseApiView):
    @influx.timer("dash.api")
    @db_for_reads.use_stats_read_replica()
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        view_filter = helpers.ViewFilter(request)

        start_date = view_filter.start_date
        end_date = view_filter.end_date

        async_perf_query = threads.AsyncFunction(partial(infobox_helpers.get_yesterday_adgroup_spend, ad_group))
        async_perf_query.start()

        filtered_sources = view_filter.filtered_sources
        ad_group_settings = ad_group.get_current_settings()

        ad_group_running_status = infobox_helpers.get_adgroup_running_status(request.user, ad_group, filtered_sources)

        header = {
            "title": ad_group.name,
            "active": ad_group_running_status,
            "level": constants.InfoboxLevel.ADGROUP,
            "level_verbose": "{}: ".format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ADGROUP)),
        }

        delivery = {
            "status": ad_group_running_status,
            "text": infobox_helpers.get_entity_delivery_text(ad_group_running_status),
        }

        basic_settings = self._basic_settings(request.user, ad_group)
        performance_settings = self._performance_settings(
            ad_group, request.user, ad_group_settings, start_date, end_date, async_perf_query, filtered_sources
        )
        for setting in performance_settings[1:]:
            setting["section_start"] = True

        response = {
            "header": header,
            "delivery": delivery,
            "basic_settings": basic_settings,
            "performance_settings": performance_settings,
        }
        return self.create_api_response(response)

    def _basic_settings(self, user, ad_group):
        settings = []

        start_date, end_date, no_ad_groups_or_budgets = self._calculate_flight_dates(ad_group)
        flight_time, flight_time_left_days = infobox_helpers.format_flight_time(
            start_date, end_date, no_ad_groups_or_budgets
        )
        days_left_description = None
        if flight_time_left_days is not None:
            days_left_description = "{} days left".format(flight_time_left_days)
        flight_time_setting = infobox_helpers.OverviewSetting(
            "Flight time:",
            flight_time,
            days_left_description,
            tooltip="Ad group's flight time is calculated from campaign budgets' and ad group's flight times.",
        )
        settings.append(flight_time_setting.as_dict())

        return settings

    def _performance_settings(
        self, ad_group, user, ad_group_settings, start_date, end_date, async_query, filtered_sources
    ):
        settings = []

        currency = ad_group.campaign.account.currency

        yesterday_costs = async_query.join_and_get_result() or 0
        daily_cap = infobox_helpers.calculate_daily_ad_group_cap(ad_group)

        settings.append(
            infobox_helpers.create_yesterday_spend_setting(
                yesterday_costs, daily_cap, currency, uses_bcm_v2=ad_group.campaign.account.uses_bcm_v2
            ).as_dict()
        )

        if user.has_perm("zemauth.campaign_goal_performance"):
            settings.extend(
                infobox_helpers.get_primary_campaign_goal_ad_group(user, ad_group, start_date, end_date, currency)
            )

        return settings

    def _calculate_flight_dates(self, ad_group):
        budgets_start_date, budgets_end_date = infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            ad_group.campaign, ad_group.settings.start_date, ad_group.settings.end_date
        )

        start_date, end_date = infobox_helpers.calculate_flight_dates(
            ad_group.settings.start_date, ad_group.settings.end_date, budgets_start_date, budgets_end_date
        )

        no_ad_groups_or_budgets = budgets_start_date is None

        return start_date, end_date, no_ad_groups_or_budgets


class AdGroupArchive(api_common.BaseApiView):
    @influx.timer("dash.api")
    def post(self, request, ad_group_id):
        if not request.user.has_perm("zemauth.archive_restore_entity"):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.archive(request)
        return self.create_api_response({})


class AdGroupRestore(api_common.BaseApiView):
    @influx.timer("dash.api")
    def post(self, request, ad_group_id):
        if not request.user.has_perm("zemauth.archive_restore_entity"):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.restore(request)

        return self.create_api_response({})


class CampaignAdGroups(api_common.BaseApiView):
    @influx.timer("dash.api")
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        self._validate_campaign_ready(request, campaign)
        ad_group = core.models.AdGroup.objects.create(request, campaign, is_restapi=self.rest_proxy)
        native_server.apply_ad_group_create_hacks(request, ad_group)
        return self.create_api_response({"name": ad_group.name, "id": ad_group.id})

    @staticmethod
    def _validate_campaign_ready(request, campaign):
        primary_goal = campaign_goals.get_primary_campaign_goal(campaign)
        scenario = None

        if not primary_goal and not campaign.settings.language and not campaign.type:
            scenario = "multiple_missing"
        elif not primary_goal:
            scenario = "goal_missing"
        elif not campaign.settings.language:
            scenario = "language_missing"
        elif not campaign.type:
            scenario = "type_missing"

        if scenario:
            url = (
                request.build_absolute_uri("/v2/analytics/campaign/{}?settings".format(campaign.id))
                + CAMPAIGN_NOT_CONFIGURED_SCENARIOS[scenario]["url_postfix"]
            )
            raise exc.ValidationError(
                data={
                    "message": CAMPAIGN_NOT_CONFIGURED_SCENARIOS[scenario]["message"],
                    "action": {"text": CAMPAIGN_NOT_CONFIGURED_SCENARIOS[scenario]["action_text"], "url": url},
                }
            )


class CampaignOverview(api_common.BaseApiView):
    @influx.timer("dash.api")
    @db_for_reads.use_stats_read_replica()
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_settings = campaign.get_current_settings()

        view_filter = helpers.ViewFilter(request)
        start_date = view_filter.start_date
        end_date = view_filter.end_date

        campaign_running_status = infobox_helpers.get_campaign_running_status(campaign)

        header = {
            "title": campaign.name,
            "active": campaign_running_status,
            "level": constants.InfoboxLevel.CAMPAIGN,
            "level_verbose": "{}: ".format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.CAMPAIGN)),
        }

        delivery = {
            "status": campaign_running_status,
            "text": infobox_helpers.get_entity_delivery_text(campaign_running_status),
        }

        basic_settings = self._basic_settings(request.user, campaign, campaign_settings)

        performance_settings = self._performance_settings(
            campaign, request.user, campaign_settings, start_date, end_date
        )

        for setting in performance_settings[1:]:
            setting["section_start"] = True

        response = {
            "header": header,
            "delivery": delivery,
            "basic_settings": basic_settings,
            "performance_settings": performance_settings,
        }
        return self.create_api_response(response)

    @influx.timer("dash.api")
    def _basic_settings(self, user, campaign, campaign_settings):
        settings = []

        campaign_manager_setting = infobox_helpers.OverviewSetting(
            "Campaign Manager:", infobox_helpers.format_username(campaign_settings.campaign_manager)
        )
        settings.append(campaign_manager_setting.as_dict())

        start_date, end_date, no_ad_groups_or_budgets = self._calculate_flight_dates(campaign)
        flight_time, flight_time_left_days = infobox_helpers.format_flight_time(
            start_date, end_date, no_ad_groups_or_budgets
        )
        flight_time_left_description = None
        if flight_time_left_days is not None:
            flight_time_left_description = "{} days left".format(flight_time_left_days)
        flight_time_setting = infobox_helpers.OverviewSetting(
            "Flight time:",
            flight_time,
            flight_time_left_description,
            tooltip="Campaign's flight time is calculated from budgets' and ad groups' flight times.",
        )
        settings.append(flight_time_setting.as_dict())

        currency = campaign.account.currency
        currency_symbol = core.features.multicurrency.get_currency_symbol(currency)

        total_spend = infobox_helpers.get_total_campaign_budgets_amount(user, campaign)
        total_spend_available = infobox_helpers.calculate_available_campaign_budget(campaign)
        campaign_budget_setting = infobox_helpers.OverviewSetting(
            "Campaign budget:",
            lc_helper.format_currency(total_spend, curr=currency_symbol),
            "{} remaining".format(lc_helper.format_currency(total_spend_available, curr=currency_symbol)),
        )
        settings.append(campaign_budget_setting.as_dict())
        return settings

    @influx.timer("dash.api")
    def _performance_settings(self, campaign, user, campaign_settings, start_date, end_date):
        settings = []

        monthly_proj = analytics.projections.CurrentMonthBudgetProjections("campaign", campaign=campaign)

        pacing = monthly_proj.total("pacing") or decimal.Decimal("0")

        currency = campaign.account.currency
        currency_symbol = core.features.multicurrency.get_currency_symbol(currency)

        daily_cap = infobox_helpers.calculate_daily_campaign_cap(campaign)
        yesterday_costs = infobox_helpers.get_yesterday_campaign_spend(campaign) or 0
        settings.append(
            infobox_helpers.create_yesterday_spend_setting(
                yesterday_costs, daily_cap, currency, uses_bcm_v2=campaign.account.uses_bcm_v2
            ).as_dict()
        )

        attributed_media_spend = monthly_proj.total("attributed_media_spend")
        if attributed_media_spend is not None:
            settings.append(
                infobox_helpers.OverviewSetting(
                    "Campaign pacing:",
                    lc_helper.format_currency(attributed_media_spend, curr=currency_symbol),
                    description="{:.2f}% on plan".format(pacing or 0),
                ).as_dict()
            )

        if user.has_perm("zemauth.campaign_goal_performance"):
            settings.extend(infobox_helpers.get_primary_campaign_goal(user, campaign, start_date, end_date, currency))

        return settings

    def _calculate_flight_dates(self, campaign):
        ags_start_date, ags_end_date = self._calculate_ad_groups_flight_dates(campaign)

        budgets_start_date, budgets_end_date = infobox_helpers.calculate_budgets_flight_dates_for_date_range(
            campaign, ags_start_date, ags_end_date
        )

        start_date, end_date = infobox_helpers.calculate_flight_dates(
            ags_start_date, ags_end_date, budgets_start_date, budgets_end_date
        )

        no_ad_groups_or_budgets = ags_start_date is None or budgets_start_date is None

        return start_date, end_date, no_ad_groups_or_budgets

    def _calculate_ad_groups_flight_dates(self, campaign):
        start_date = None
        end_date = None
        never_finishes = False

        ad_groups_settings = (
            models.AdGroupSettings.objects.filter(ad_group__campaign=campaign)
            .group_current_settings()
            .values_list("start_date", "end_date")
        )

        for ags in ad_groups_settings:
            ag_start_date = ags[0]
            ag_end_date = ags[1]

            if start_date is None:
                start_date = ag_start_date
            else:
                start_date = min(start_date, ag_start_date)

            if end_date is None:
                end_date = ag_end_date
            else:
                end_date = max(end_date, ag_end_date or end_date)

            if ag_end_date is None:
                never_finishes = True

        if never_finishes:
            end_date = None

        return start_date, end_date


class AccountOverview(api_common.BaseApiView):
    @influx.timer("dash.api")
    @db_for_reads.use_stats_read_replica()
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id, select_related_users=True)

        account_running_status = infobox_helpers.get_account_running_status(account)

        header = {
            "title": account.name,
            "active": account_running_status,
            "level": constants.InfoboxLevel.ACCOUNT,
            "level_verbose": "{}: ".format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ACCOUNT)),
        }

        delivery = {
            "status": account_running_status,
            "text": infobox_helpers.get_entity_delivery_text(account_running_status),
        }

        basic_settings = self._basic_settings(request.user, account)

        performance_settings = self._performance_settings(account, request.user)
        for setting in performance_settings[1:]:
            setting["section_start"] = True

        response = {
            "header": header,
            "delivery": delivery,
            "basic_settings": basic_settings,
            "performance_settings": performance_settings,
        }

        return self.create_api_response(response)

    def _basic_settings(self, user, account):
        settings = []

        account_settings = account.get_current_settings()
        account_manager_setting = infobox_helpers.OverviewSetting(
            "Account Manager:", infobox_helpers.format_username(account_settings.default_account_manager)
        )
        settings.append(account_manager_setting.as_dict())

        sales_manager_setting_label = "Sales Representative:"
        cs_manager_setting_label = "CS Representative:"

        sales_manager_setting = infobox_helpers.OverviewSetting(
            sales_manager_setting_label, infobox_helpers.format_username(account_settings.default_sales_representative)
        )
        settings.append(sales_manager_setting.as_dict())

        cs_manager_setting = infobox_helpers.OverviewSetting(
            cs_manager_setting_label, infobox_helpers.format_username(account_settings.default_cs_representative)
        )
        settings.append(cs_manager_setting.as_dict())

        allocated_credit, available_credit = infobox_helpers.calculate_allocated_and_available_credit(account)

        currency_symbol = core.features.multicurrency.get_currency_symbol(account.currency)
        allocated_credit_text = lc_helper.format_currency(allocated_credit, curr=currency_symbol)
        unallocated_credit_text = lc_helper.format_currency(available_credit, curr=currency_symbol)

        allocated_credit_setting = infobox_helpers.OverviewSetting(
            "Allocated credit:", allocated_credit_text, description="{} unallocated".format(unallocated_credit_text)
        )
        settings.append(allocated_credit_setting.as_dict())

        credit_refund = infobox_helpers.calculate_credit_refund(account)
        if credit_refund:
            credit_refund_text = lc_helper.format_currency(credit_refund, curr=currency_symbol)
            credit_refund_setting = infobox_helpers.OverviewSetting(
                "Refunded credit:", credit_refund_text, description=""
            )
            settings.append(credit_refund_setting.as_dict())

        return settings

    def _performance_settings(self, account, user):
        settings = []

        currency = account.currency
        daily_budget = infobox_helpers.calculate_daily_account_cap(account)
        yesterday_costs = infobox_helpers.get_yesterday_account_spend(account)
        settings.append(
            infobox_helpers.create_yesterday_spend_setting(
                yesterday_costs, daily_budget, currency, uses_bcm_v2=account.uses_bcm_v2
            ).as_dict()
        )

        return settings


class AvailableSources(api_common.BaseApiView):
    @influx.timer("dash.api")
    def get(self, request):
        user_accounts = models.Account.objects.all().filter_by_user(request.user)
        user_sources = (
            models.Source.objects.filter(account__in=user_accounts)
            .filter(deprecated=False)
            .distinct()
            .only("id", "name", "deprecated")
        )

        sources = []
        for source in user_sources:
            sources.append({"id": str(source.id), "name": source.name, "deprecated": source.deprecated})

        return self.create_api_response({"sources": sources})


class AdGroupSources(api_common.BaseApiView):
    @influx.timer("dash.api")
    def get(self, request, ad_group_id):
        if not request.user.has_perm("zemauth.ad_group_sources_add_source"):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group_settings = ad_group.get_current_settings()

        allowed_sources = ad_group.campaign.account.allowed_sources.all()
        existing_ad_group_sources = ad_group.adgroupsource_set.exclude(ad_review_only=True)
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get("filtered_sources"))
        sources_with_credentials = models.DefaultSourceSettings.objects.all().with_credentials().values("source")
        available_sources = (
            allowed_sources.exclude(pk__in=existing_ad_group_sources.values_list("source_id"))
            .filter(pk__in=filtered_sources)
            .filter(pk__in=sources_with_credentials)
            .order_by("name")
        )

        if ad_group.campaign.type == constants.CampaignType.VIDEO:
            available_sources = available_sources.filter(supports_video=True)

        sources = []
        for source in available_sources:
            sources.append(
                {
                    "id": source.id,
                    "name": source.name,
                    "can_target_existing_regions": region_targeting_helper.can_target_existing_regions(
                        source, ad_group_settings
                    ),
                    "can_retarget": retargeting_helper.can_add_source_with_retargeting(source, ad_group_settings),
                }
            )

        return self.create_api_response(
            {"sources": sorted(sources, key=lambda source: source["name"]), "sources_waiting": []}
        )

    @influx.timer("dash.api")
    def put(self, request, ad_group_id):
        if not request.user.has_perm("zemauth.ad_group_sources_add_source"):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        source_id = json.loads(request.body)["source_id"]
        source = models.Source.objects.get(id=source_id)

        try:
            core.models.AdGroupSource.objects.create(request, ad_group, source, write_history=True, k1_sync=True)

        except (
            core.models.ad_group_source.exceptions.SourceNotAllowed,
            core.models.ad_group_source.exceptions.RetargetingNotSupported,
            core.models.ad_group_source.exceptions.SourceAlreadyExists,
            core.models.ad_group_source.exceptions.VideoNotSupported,
        ) as err:
            raise exc.ValidationError(str(err))

        return self.create_api_response(None)


class Account(api_common.BaseApiView):
    @influx.timer("dash.api")
    def put(self, request):
        if not request.user.has_perm("zemauth.all_accounts_accounts_add_account"):
            raise exc.MissingDataError()

        agency = models.Agency.objects.all().filter(users=request.user).first()

        account = models.Account.objects.create(
            request, name=core.models.helpers.create_default_name(models.Account.objects, "New account"), agency=agency
        )

        response = {"name": account.name, "id": account.id}

        return self.create_api_response(response)


class AccountCampaigns(api_common.BaseApiView):
    @influx.timer("dash.api")
    def put(self, request, account_id):
        if not request.user.has_perm("zemauth.account_campaigns_view"):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        form = forms.CampaignForm(json.loads(request.body))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        name = core.models.helpers.create_default_name(models.Campaign.objects.filter(account=account), "New campaign")
        type = form.cleaned_data.get("campaign_type")
        language = constants.Language.ENGLISH if self.rest_proxy else None
        campaign = models.Campaign.objects.create(request, account, name, language=language, type=type, send_mail=True)
        native_server.apply_campaign_create_hacks(request, campaign)

        response = {"name": campaign.name, "id": campaign.id}

        return self.create_api_response(response)


class AdGroupSourceSettings(api_common.BaseApiView):
    @influx.timer("dash.api")
    def put(self, request, ad_group_id, source_id):
        resource = json.loads(request.body)
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        try:
            ad_group_source = models.AdGroupSource.objects.get(ad_group=ad_group, source_id=source_id)
        except models.AdGroupSource.DoesNotExist:
            raise exc.MissingDataError(message="Requested source not found")

        form = forms.AdGroupSourceSettingsForm(resource)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        for field in ad_group_source.settings.multicurrency_fields:
            form.cleaned_data["local_{}".format(field)] = form.cleaned_data.pop(field, None)

        data = {k: v for k, v in list(form.cleaned_data.items()) if v is not None}
        data = native_server.transform_ad_group_source_settings(ad_group, data)

        response = self._update_ad_group_source(request, ad_group_source, data)

        allowed_sources = {source.id for source in ad_group.campaign.account.allowed_sources.all()}
        campaign_settings = ad_group.campaign.get_current_settings()
        ad_group_settings = ad_group.get_current_settings()

        return self.create_api_response(
            {
                "editable_fields": helpers.get_editable_fields(
                    ad_group,
                    ad_group_source,
                    ad_group_settings,
                    ad_group_source.get_current_settings(),
                    campaign_settings,
                    allowed_sources,
                ),
                "autopilot_changed_sources": response["autopilot_changed_sources_text"],
                "enabling_autopilot_sources_allowed": helpers.enabling_autopilot_single_source_allowed(ad_group),
            }
        )

    def _update_ad_group_source(self, request, ad_group_source, data):
        try:
            return ad_group_source.settings.update(request, k1_sync=True, **data)

        except core.models.settings.ad_group_source_settings.exceptions.DailyBudgetNegative as err:
            raise exc.ValidationError(errors={"daily_budget_cc": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.MinimalDailyBudgetTooLow as err:
            raise exc.ValidationError(
                errors={
                    "daily_budget_cc": [
                        "Please provide daily spend cap of at least {}.".format(
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                            )
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalDailyBudgetTooHigh as err:
            raise exc.ValidationError(
                errors={
                    "daily_budget_cc": [
                        "Maximum allowed daily spend cap is {}. "
                        "If you want use a higher daily spend cap, please contact support.".format(
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            )
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.CPCNegative as err:
            raise exc.ValidationError(errors={"cpc_cc": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.CPMNegative as err:
            raise exc.ValidationError(errors={"cpm": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.CPCPrecisionExceeded as err:
            raise exc.ValidationError(
                errors={
                    "cpc_cc": [
                        "CPC on {} cannot exceed {} decimal place{}.".format(
                            err.data.get("source_name"),
                            err.data.get("value"),
                            "s" if err.data.get("value") != 1 else "",
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.CPMPrecisionExceeded as err:
            raise exc.ValidationError(
                errors={
                    "cpm": [
                        "CPM on {} cannot exceed {} decimal place{}.".format(
                            err.data.get("source_name"),
                            err.data.get("value"),
                            "s" if err.data.get("value") != 1 else "",
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MinimalCPCTooLow as err:
            raise exc.ValidationError(
                errors={
                    "cpc_cc": [
                        "Minimum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalCPCTooHigh as err:
            raise exc.ValidationError(
                errors={
                    "cpc_cc": [
                        "Maximum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MinimalCPMTooLow as err:
            raise exc.ValidationError(
                errors={
                    "cpm": [
                        "Minimum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalCPMTooHigh as err:
            raise exc.ValidationError(
                errors={
                    "cpm": [
                        "Maximum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.CannotSetCPC as err:
            raise exc.ValidationError(errors={"cpc_cc": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.CannotSetCPM as err:
            raise exc.ValidationError(errors={"cpm": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.B1SourcesCPCNegative as err:
            raise exc.ValidationError(errors={"cpc_cc": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.B1SourcesCPMNegative as err:
            raise exc.ValidationError(errors={"cpm": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.CPCInvalid as err:
            raise exc.ValidationError(errors={"cpc_cc": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.RetargetingNotSupported as err:
            raise exc.ValidationError(errors={"state": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.MediaSourceNotConnectedToFacebook as err:
            raise exc.ValidationError(errors={"state": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.YahooCPCTooLow as err:
            raise exc.ValidationError(errors={"state": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.AutopilotDailySpendCapTooLow as err:
            raise exc.ValidationError(errors={"state": [str(err)]})


class AllAccountsOverview(api_common.BaseApiView):
    @influx.timer("dash.api")
    @db_for_reads.use_stats_read_replica()
    def get(self, request):
        # infobox only filters by agency and account type
        view_filter = helpers.ViewFilter(request=request)
        start_date = view_filter.start_date
        end_date = view_filter.end_date

        header = {
            "title": None,
            "level": constants.InfoboxLevel.ALL_ACCOUNTS,
            "level_verbose": constants.InfoboxLevel.get_text(constants.InfoboxLevel.ALL_ACCOUNTS),
        }

        performance_settings = []
        if request.user.has_perm("zemauth.can_access_all_accounts_infobox"):
            basic_settings = self._basic_all_accounts_settings(request.user, start_date, end_date, view_filter)
            performance_settings = self._append_performance_all_accounts_settings(
                performance_settings, request.user, view_filter
            )
            performance_settings = [setting.as_dict() for setting in performance_settings]
        elif request.user.has_perm("zemauth.can_access_agency_infobox"):
            basic_settings = self._basic_agency_settings(request.user, start_date, end_date, view_filter)
            performance_settings = self._append_performance_agency_settings(
                performance_settings, request.user, view_filter
            )
            performance_settings = [setting.as_dict() for setting in performance_settings]
        else:
            raise exc.AuthorizationError()

        response = {
            "header": header,
            "basic_settings": basic_settings,
            "performance_settings": performance_settings if len(performance_settings) > 0 else None,
        }

        return self.create_api_response(response)

    def _basic_agency_settings(self, user, start_date, end_date, view_filter):
        settings = []
        count_active_accounts = infobox_helpers.count_active_agency_accounts(user)
        settings.append(
            infobox_helpers.OverviewSetting(
                "Active accounts:",
                count_active_accounts,
                section_start=True,
                tooltip="Number of accounts with at least one campaign running",
            )
        )

        return [setting.as_dict() for setting in settings]

    def _basic_all_accounts_settings(self, user, start_date, end_date, view_filter):
        settings = []

        constraints = {}
        if view_filter.filtered_agencies:
            constraints["campaign__account__agency__in"] = view_filter.filtered_agencies
        if view_filter.filtered_account_types:
            latest_accset = models.AccountSettings.objects.all().group_current_settings()
            latest_typed_accset = (
                models.AccountSettings.objects.all()
                .filter(id__in=latest_accset)
                .filter(account_type__in=view_filter.filtered_account_types)
                .values_list("account__id", flat=True)
            )
            constraints["campaign__account__id__in"] = latest_typed_accset

        count_active_accounts = infobox_helpers.count_active_accounts(
            view_filter.filtered_agencies, view_filter.filtered_account_types
        )
        settings.append(
            infobox_helpers.OverviewSetting(
                "Active accounts:",
                count_active_accounts,
                section_start=True,
                tooltip="Number of accounts with at least one campaign running",
            )
        )

        weekly_logged_users = infobox_helpers.count_weekly_logged_in_users(
            view_filter.filtered_agencies, view_filter.filtered_account_types
        )
        settings.append(
            infobox_helpers.OverviewSetting(
                "Logged-in users:", weekly_logged_users, tooltip="Number of users who logged-in in the past 7 days"
            )
        )

        weekly_active_users = infobox_helpers.get_weekly_active_users(
            view_filter.filtered_agencies, view_filter.filtered_account_types
        )
        weekly_active_user_emails = [u.email for u in weekly_active_users]
        email_list_setting = infobox_helpers.OverviewSetting(
            "Active users:",
            "{}".format(len(weekly_active_users)),
            tooltip="Users who made self-managed actions in the past 7 days",
        )

        if weekly_active_user_emails != []:
            email_list_setting = email_list_setting.comment("Show more", "<br />".join(weekly_active_user_emails))
        settings.append(email_list_setting)

        weekly_sf_actions = infobox_helpers.count_weekly_selfmanaged_actions(
            view_filter.filtered_agencies, view_filter.filtered_account_types
        )
        settings.append(
            infobox_helpers.OverviewSetting(
                "Self-managed actions:",
                weekly_sf_actions,
                tooltip="Number of actions taken by self-managed users " "in the past 7 days",
            )
        )

        return [setting.as_dict() for setting in settings]

    def _append_performance_agency_settings(self, overview_settings, user, view_filter):
        accounts = models.Account.objects.all().filter_by_user(user).exclude_archived(view_filter.show_archived)
        currency = stats.helpers.get_report_currency(user, accounts)

        uses_bcm_v2 = accounts.all_use_bcm_v2()

        use_local_currency = currency != constants.Currency.USD
        yesterday_costs = infobox_helpers.get_yesterday_accounts_spend(accounts, use_local_currency)
        yesterday_cost = yesterday_costs["yesterday_etfm_cost"] if uses_bcm_v2 else yesterday_costs["e_yesterday_cost"]

        currency_symbol = core.features.multicurrency.get_currency_symbol(currency)
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Yesterday spend:", lc_helper.format_currency(yesterday_cost, curr=currency_symbol), section_start=True
            )
        )

        mtd_costs = infobox_helpers.get_mtd_accounts_spend(accounts, use_local_currency)
        mtd_cost = mtd_costs["etfm_cost"] if uses_bcm_v2 else mtd_costs["e_media_cost"]
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Month-to-date spend:", lc_helper.format_currency(mtd_cost, curr=currency_symbol)
            )
        )

        return overview_settings

    def _append_performance_all_accounts_settings(self, overview_settings, user, view_filter):
        accounts = (
            models.Account.objects.filter_by_user(user)
            .filter_by_agencies(view_filter.filtered_agencies)
            .filter_by_account_types(view_filter.filtered_account_types)
            .exclude_archived(view_filter.show_archived)
        )
        currency = stats.helpers.get_report_currency(user, accounts)

        use_local_currency = currency != constants.Currency.USD
        yesterday_costs = infobox_helpers.get_yesterday_accounts_spend(accounts, use_local_currency)

        uses_bcm_v2 = settings.ALL_ACCOUNTS_USE_BCM_V2
        yesterday_cost = yesterday_costs["yesterday_etfm_cost"] if uses_bcm_v2 else yesterday_costs["e_yesterday_cost"]

        currency_symbol = core.features.multicurrency.get_currency_symbol(currency)
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Yesterday spend:", lc_helper.format_currency(yesterday_cost, curr=currency_symbol), section_start=True
            )
        )

        mtd_costs = infobox_helpers.get_mtd_accounts_spend(accounts, use_local_currency)
        mtd_cost = mtd_costs["etfm_cost"] if uses_bcm_v2 else mtd_costs["e_media_cost"]
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Month-to-date spend:", lc_helper.format_currency(mtd_cost, curr=currency_symbol)
            )
        )

        return overview_settings


class Demo(api_common.BaseApiView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_request_demo_v3"):
            raise Http404("Forbidden")

        instance = self._start_instance()

        email_helper.send_official_email(
            agency_or_user=request.user,
            recipient_list=[request.user.email],
            **email_helper.params_from_template(constants.EmailTemplateType.DEMO_RUNNING, **instance)
        )

        return self.create_api_response(instance)

    def _start_instance(self):
        request = urllib.request.Request(settings.DK_DEMO_UP_ENDPOINT)
        response = request_signer.urllib_secure_open(request, settings.DK_API_KEY)

        status_code = response.getcode()
        if status_code != 200:
            raise Exception("Invalid response status code. status code: {}".format(status_code))

        ret = json.loads(response.read())
        if ret["status"] != "success":
            raise Exception("Request not successful. status: {}".format(ret["status"]))

        return {"url": ret.get("instance_url"), "password": ret.get("instance_password")}


def healthcheck(request):
    return HttpResponse("OK")


def oauth_authorize(request, source_name):
    credentials_id = request.GET.get("credentials_id")

    if not credentials_id:
        logger.warning("Missing credentials id")
        return redirect("index")

    credentials = models.SourceCredentials.objects.get(id=credentials_id)
    decrypted = json.loads(credentials.decrypt())

    if "client_id" not in decrypted or "client_secret" not in decrypted:
        logger.error("client_id and/or client_secret not in credentials")
        return redirect("index")

    state = {"credentials_id": credentials_id}

    redirect_uri = request.build_absolute_uri(reverse("source.oauth.redirect", kwargs={"source_name": source_name}))
    redirect_uri = redirect_uri.replace("http://", "https://")

    params = {
        "client_id": decrypted["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": base64.b64encode(json.dumps(state)),
    }

    url = settings.SOURCE_OAUTH_URIS[source_name]["auth_uri"] + "?" + urllib.parse.urlencode(params)
    return redirect(url)


def oauth_redirect(request, source_name):
    # Token requests are implemented using urllib2 requests because Yahoo only supports credentials in
    # Authorization header while oauth2client sends it in reqeust body (for get_token calls, after that
    # it puts access token into header).

    code = request.GET.get("code")
    state = request.GET.get("state")

    if not state:
        logger.error("Missing state in OAuth2 redirect")
        return redirect("index")

    try:
        state = json.loads(base64.b64decode(state))
    except (TypeError, ValueError):
        logger.error("Invalid state in OAuth2 redirect")
        return redirect("index")

    credentials = models.SourceCredentials.objects.get(id=state["credentials_id"])
    decrypted = json.loads(credentials.decrypt())

    redirect_uri = request.build_absolute_uri(reverse("source.oauth.redirect", kwargs={"source_name": source_name}))
    redirect_uri = redirect_uri.replace("http://", "https://")

    headers = {
        "Authorization": "Basic {}".format(base64.b64encode(decrypted["client_id"] + ":" + decrypted["client_secret"]))
    }

    data = {"redirect_uri": redirect_uri, "code": code, "grant_type": "authorization_code"}

    req = urllib.request.Request(
        settings.SOURCE_OAUTH_URIS[source_name]["token_uri"], data=urllib.parse.urlencode(data), headers=headers
    )
    r = urllib.request.urlopen(req)

    if r.getcode() == http.client.OK:
        decrypted["oauth_tokens"] = json.loads(r.read())
        decrypted["oauth_created_dt"] = datetime.datetime.utcnow().isoformat()
        credentials.credentials = json.dumps(decrypted)
        credentials.save()

    return redirect(reverse("admin:dash_sourcecredentials_change", args=(credentials.id,)))


class LiveStreamAllow(api_common.BaseApiView):
    def post(self, request):
        data = json.loads(request.body)
        email_helper.send_livestream_email(request.user, data["session_url"])
        return self.create_api_response({})
