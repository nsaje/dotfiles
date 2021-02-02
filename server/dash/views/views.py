# -*- coding: utf-8 -*-
import base64
import datetime
import decimal
import http.client
import json
import urllib.error
import urllib.parse
import urllib.request
from functools import partial

from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

import core.features.delivery_status
import core.features.multicurrency
import core.models.ad_group_source.exceptions
import core.models.campaign.exceptions
import core.models.helpers
import core.models.settings.ad_group_source_settings.exceptions
import dash.features.campaign_pacing
import demo
import stats.helpers
import zemauth.access
from dash import constants
from dash import forms
from dash import infobox_helpers
from dash import models
from dash.common.views_base import DASHAPIBaseView
from dash.features.custom_flags.slack_logger import SlackLoggerMixin
from dash.views import helpers
from utils import email_helper
from utils import exc
from utils import k1_helper
from utils import lc_helper
from utils import metrics_compat
from utils import threads
from utils import zlogging
from zemauth.features.entity_permission import Permission

logger = zlogging.getLogger(__name__)

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
        "url_postfix": "&settingsScrollTo=zemLegacyCampaignGoalsSettings",
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
        models.Agency.objects.all()
        .filter(Q(entitypermission__user__id=request.user.id) | Q(account__entitypermission__user__id=request.user.id))
        .first()
    )
    whitelabel = associated_agency and associated_agency.white_label or None
    return render(
        request,
        "index.html",
        {
            "staticUrl": settings.CLIENT_STATIC_URL,
            "debug": settings.DEBUG,
            "whitelabel": whitelabel and whitelabel.theme,
            "faviconUrl": whitelabel and whitelabel.favicon_url,
            "dashboardTitle": whitelabel and whitelabel.dashboard_title,
            "termsOfServiceUrl": whitelabel and whitelabel.terms_of_service_url,
            "copyrightHolder": whitelabel and whitelabel.copyright_holder,
            "copyrightHolderUrl": whitelabel and whitelabel.copyright_holder_url,
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
        ad_group_source = models.AdGroupSource.objects.select_related("ad_group__campaign__account").get(
            ad_group__id=int(ad_group_id), source__id=int(source_id)
        )
    except models.AdGroupSource.DoesNotExist:
        raise Http404()

    credentials = ad_group_source.source_credentials and ad_group_source.source_credentials.decrypt()
    if ad_group_source.source.source_type.type == constants.SourceType.OUTBRAIN:
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


class AdGroupOverview(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def get(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)
        view_filter = forms.ViewFilterForm(request.GET)
        if not view_filter.is_valid():
            raise exc.ValidationError(errors=dict(view_filter.errors))

        start_date = view_filter.cleaned_data.get("start_date")
        end_date = view_filter.cleaned_data.get("end_date")
        async_perf_query = threads.AsyncFunction(partial(infobox_helpers.get_yesterday_adgroup_spend, ad_group))
        async_perf_query.start()

        filtered_sources = view_filter.cleaned_data.get("filtered_sources")
        ad_group_settings = ad_group.get_current_settings()
        ad_group_running_status = core.features.delivery_status.get_ad_group_detailed_delivery_status(ad_group)

        agency_uses_realtime_autopilot = ad_group.campaign.account.agency_uses_realtime_autopilot()

        header = {
            "title": ad_group.name,
            "active": ad_group_running_status,
            "level": constants.InfoboxLevel.ADGROUP,
            "level_verbose": "{}: ".format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ADGROUP)),
        }

        delivery = {
            "status": ad_group_running_status,
            "text": infobox_helpers.get_entity_delivery_text(ad_group_running_status, agency_uses_realtime_autopilot),
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
        settings.extend([s.as_dict() for s in infobox_helpers.create_bid_value_overview_settings(ad_group)])

        return settings

    def _performance_settings(
        self, ad_group, user, ad_group_settings, start_date, end_date, async_query, filtered_sources
    ):
        settings = []

        currency = ad_group.campaign.account.currency

        yesterday_costs = async_query.join_and_get_result() or 0
        daily_cap = infobox_helpers.calculate_daily_ad_group_cap(ad_group)

        settings.append(infobox_helpers.create_yesterday_data_setting().as_dict())
        settings.append(infobox_helpers.create_yesterday_spend_setting(yesterday_costs, daily_cap, currency).as_dict())

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


class CampaignOverview(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def get(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.READ, campaign_id)
        campaign_settings = campaign.get_current_settings()

        view_filter = forms.ViewFilterForm(request.GET)
        if not view_filter.is_valid():
            raise exc.ValidationError(errors=dict(view_filter.errors))
        start_date = view_filter.cleaned_data.get("start_date")
        end_date = view_filter.cleaned_data.get("end_date")

        campaign_running_status = core.features.delivery_status.get_campaign_detailed_delivery_status(campaign)

        agency_uses_realtime_autopilot = campaign.account.agency_uses_realtime_autopilot()

        header = {
            "title": campaign.name,
            "active": campaign_running_status,
            "level": constants.InfoboxLevel.CAMPAIGN,
            "level_verbose": "{}: ".format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.CAMPAIGN)),
        }

        delivery = {
            "status": campaign_running_status,
            "text": infobox_helpers.get_entity_delivery_text(campaign_running_status, agency_uses_realtime_autopilot),
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

    @metrics_compat.timer("dash.api")
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

    @metrics_compat.timer("dash.api")
    def _performance_settings(self, campaign, user, campaign_settings, start_date, end_date):
        settings = []
        campaign_pacing = dash.features.campaign_pacing.CampaignPacing(campaign)
        pacing_data = campaign_pacing.data

        settings.append(infobox_helpers.create_yesterday_data_setting().as_dict())

        currency = campaign.account.currency
        currency_symbol = core.features.multicurrency.get_currency_symbol(currency)

        pacing_info_text = """
            <p>Campaign spend (in blue) displays the total spend on campaign during the specified period.</p>
            <p>Campaign pacing (expressed as % in brackets) is the quotient between campaign total spend and
             the total available budget during pacing period. Only budget available in the pacing period is considered.
             If the campaign budget period extends into the future, the amount of total available budget is proportional
             to the days that fall within the pacing period.</p>
        """
        pacing_settings = infobox_helpers.OverviewSetting("Campaign pacing:", tooltip=pacing_info_text)
        for window, data in pacing_data.items():
            pacing_settings.add_child(
                infobox_helpers.OverviewSetting(
                    "Yesterday:"
                    if window == dash.features.campaign_pacing.service.PACING_WINDOW_1_DAY
                    else f"Last {window} days:",
                    lc_helper.format_currency(data.attributed_spend, curr=currency_symbol),
                    description="{:.2f}% on plan".format(data.pacing or 0),
                ).as_dict()
            )
        settings.append(pacing_settings.as_dict())

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


class AccountOverview(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def get(self, request, account_id):
        account = zemauth.access.get_account(request.user, Permission.READ, account_id, select_related_users=True)

        account_running_status = core.features.delivery_status.get_account_detailed_delivery_status(account)

        agency_uses_realtime_autopilot = account.agency_uses_realtime_autopilot()

        header = {
            "title": account.name,
            "active": account_running_status,
            "level": constants.InfoboxLevel.ACCOUNT,
            "level_verbose": "{}: ".format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ACCOUNT)),
        }

        delivery = {
            "status": account_running_status,
            "text": infobox_helpers.get_entity_delivery_text(account_running_status, agency_uses_realtime_autopilot),
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

        currency_symbol = core.features.multicurrency.get_currency_symbol(account.currency)

        account_budget = infobox_helpers.get_total_account_budgets_amount(account)
        account_budget_available = infobox_helpers.calculate_available_account_budget(account)
        allocated_budget_setting = infobox_helpers.OverviewSetting(
            "Allocated budget:",
            lc_helper.format_currency(account_budget, curr=currency_symbol),
            description="{} remaining".format(
                lc_helper.format_currency(account_budget_available, curr=currency_symbol)
            ),
        )
        settings.append(allocated_budget_setting.as_dict())

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

        settings.append(infobox_helpers.create_yesterday_data_setting().as_dict())
        settings.append(
            infobox_helpers.create_yesterday_spend_setting(yesterday_costs, daily_budget, currency).as_dict()
        )

        return settings


class AvailableSources(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def get(self, request):
        user_accounts = models.Account.objects.all().filter_by_entity_permission(request.user, Permission.READ)

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


class AdGroupSources(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def get(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)

        allowed_sources = ad_group.campaign.account.allowed_sources.all()
        existing_ad_group_sources = ad_group.adgroupsource_set.exclude(ad_review_only=True)
        filtered_sources = helpers.get_filtered_sources(request.GET.get("filtered_sources"))
        sources_with_credentials = models.DefaultSourceSettings.objects.all().with_credentials().values("source")
        available_sources = (
            allowed_sources.exclude(pk__in=existing_ad_group_sources.values_list("source_id"))
            .filter(pk__in=filtered_sources)
            .filter(pk__in=sources_with_credentials)
            .order_by("name")
        )

        if ad_group.campaign.type == constants.CampaignType.VIDEO:
            available_sources = available_sources.filter(supports_video=True)

        if ad_group.campaign.type == constants.CampaignType.DISPLAY:
            available_sources = available_sources.filter(supports_display=True)

        sources = []
        for source in available_sources:
            sources.append({"id": source.id, "name": source.name})

        return self.create_api_response(
            {"sources": sorted(sources, key=lambda source: source["name"]), "sources_waiting": []}
        )

    @metrics_compat.timer("dash.api")
    def put(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        source_id = json.loads(request.body)["source_id"]
        source = models.Source.objects.get(id=source_id)

        try:
            core.models.AdGroupSource.objects.create(request, ad_group, source, write_history=True, k1_sync=True)

        except (
            core.models.ad_group_source.exceptions.SourceNotAllowed,
            core.models.ad_group_source.exceptions.RetargetingNotSupported,
            core.models.ad_group_source.exceptions.SourceAlreadyExists,
            core.models.ad_group_source.exceptions.VideoNotSupported,
            core.models.ad_group_source.exceptions.DisplayNotSupported,
        ) as err:
            raise exc.ValidationError(str(err))

        return self.create_api_response(None)


class AdGroupSourceSettings(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def put(self, request, ad_group_id, source_id):
        resource = json.loads(request.body)
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

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

        self._update_ad_group_source(request, ad_group_source, data)

        allowed_sources = {source.id for source in ad_group.campaign.account.allowed_sources.all()}
        campaign_settings = ad_group.campaign.get_current_settings()
        ad_group_settings = ad_group.get_current_settings()

        return self.create_api_response(
            {
                "editable_fields": helpers.get_editable_fields(
                    request.user,
                    ad_group,
                    ad_group_source,
                    ad_group_settings,
                    ad_group_source.get_current_settings(),
                    campaign_settings,
                    allowed_sources,
                ),
                "enabling_autopilot_sources_allowed": ad_group.campaign.account.agency_uses_realtime_autopilot()
                or helpers.enabling_autopilot_single_source_allowed(ad_group),
            }
        )

    def _update_ad_group_source(self, request, ad_group_source, data):
        try:
            return ad_group_source.settings.update(request, k1_sync=True, **data)

        except (
            core.models.settings.ad_group_source_settings.exceptions.CPCNegative,
            core.models.settings.ad_group_source_settings.exceptions.CannotSetCPC,
            core.models.settings.ad_group_source_settings.exceptions.B1SourcesCPCNegative,
            core.models.settings.ad_group_source_settings.exceptions.CPCInvalid,
        ) as err:
            raise exc.ValidationError(errors={"cpc_cc": [str(err)]})

        except (
            core.models.settings.ad_group_source_settings.exceptions.CPMNegative,
            core.models.settings.ad_group_source_settings.exceptions.CannotSetCPM,
            core.models.settings.ad_group_source_settings.exceptions.B1SourcesCPMNegative,
        ) as err:
            raise exc.ValidationError(errors={"cpm": [str(err)]})

        except (
            core.models.settings.ad_group_source_settings.exceptions.DailyBudgetNegative,
            core.models.settings.ad_group_source_settings.exceptions.BudgetUpdateWhileSourcesGroupEnabled,
        ) as err:
            raise exc.ValidationError(errors={"daily_budget_cc": [str(err)]})

        except (
            core.models.settings.ad_group_source_settings.exceptions.AutopilotDailySpendCapTooLow,
            core.models.settings.ad_group_source_settings.exceptions.MediaSourceNotConnectedToFacebook,
        ) as err:
            raise exc.ValidationError(errors={"state": [str(err)]})

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


class AllAccountsOverview(DASHAPIBaseView):
    @metrics_compat.timer("dash.api")
    def get(self, request):
        # infobox only filters by agency and account type
        view_filter = forms.ViewFilterForm(request.GET)
        if not view_filter.is_valid():
            raise exc.ValidationError(errors=dict(view_filter.errors))
        start_date = view_filter.cleaned_data.get("start_date")
        end_date = view_filter.cleaned_data.get("end_date")
        header = {
            "title": None,
            "level": constants.InfoboxLevel.ALL_ACCOUNTS,
            "level_verbose": constants.InfoboxLevel.get_text(constants.InfoboxLevel.ALL_ACCOUNTS),
        }

        performance_settings = []
        if request.user.has_perm_on_all_entities(Permission.READ):
            basic_settings = self._basic_all_accounts_settings(request.user, start_date, end_date, view_filter)
            performance_settings = self._append_performance_all_accounts_settings(
                performance_settings, request.user, view_filter
            )
            performance_settings = [setting.as_dict() for setting in performance_settings]
        else:
            basic_settings = self._basic_agency_settings(request.user, start_date, end_date, view_filter)
            performance_settings = self._append_performance_agency_settings(
                performance_settings, request.user, view_filter
            )
            performance_settings = [setting.as_dict() for setting in performance_settings]

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
        if view_filter.cleaned_data.get("filtered_agencies"):
            constraints["campaign__account__agency__in"] = view_filter.cleaned_data.get("filtered_agencies")
        if view_filter.cleaned_data.get("filtered_account_types"):
            latest_accset = models.AccountSettings.objects.all().group_current_settings()
            latest_typed_accset = (
                models.AccountSettings.objects.all()
                .filter(id__in=latest_accset)
                .filter(account_type__in=view_filter.cleaned_data.get("filtered_account_types"))
                .values_list("account__id", flat=True)
            )
            constraints["campaign__account__id__in"] = latest_typed_accset

        count_active_accounts = infobox_helpers.count_active_accounts(
            view_filter.cleaned_data.get("filtered_agencies"), view_filter.cleaned_data.get("filtered_account_types")
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
            view_filter.cleaned_data.get("filtered_agencies"), view_filter.cleaned_data.get("filtered_account_types")
        )
        settings.append(
            infobox_helpers.OverviewSetting(
                "Logged-in users:", weekly_logged_users, tooltip="Number of users who logged-in in the past 7 days"
            )
        )

        return [setting.as_dict() for setting in settings]

    def _append_performance_agency_settings(self, overview_settings, user, view_filter):
        accounts = (
            models.Account.objects.all()
            .filter_by_entity_permission(user, Permission.READ)
            .exclude_archived(view_filter.cleaned_data.get("show_archived"))
        )

        currency = stats.helpers.get_report_currency(user, accounts)

        use_local_currency = currency != constants.Currency.USD
        yesterday_costs = infobox_helpers.get_yesterday_accounts_spend(accounts, use_local_currency)
        yesterday_cost = yesterday_costs["yesterday_etfm_cost"]

        currency_symbol = core.features.multicurrency.get_currency_symbol(currency)
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Yesterday spend:", lc_helper.format_currency(yesterday_cost, curr=currency_symbol), section_start=True
            )
        )

        mtd_costs = infobox_helpers.get_mtd_accounts_spend(accounts, use_local_currency)
        mtd_cost = mtd_costs["etfm_cost"]
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Month-to-date spend:", lc_helper.format_currency(mtd_cost, curr=currency_symbol)
            )
        )

        return overview_settings

    def _append_performance_all_accounts_settings(self, overview_settings, user, view_filter):
        overview_settings.append(infobox_helpers.create_yesterday_data_setting())

        accounts = (
            models.Account.objects.filter_by_entity_permission(user, Permission.READ)
            .filter_by_agencies(view_filter.cleaned_data.get("filtered_agencies"))
            .filter_by_account_types(view_filter.cleaned_data.get("filtered_account_types"))
            .exclude_archived(view_filter.cleaned_data.get("show_archived"))
        )

        currency = stats.helpers.get_report_currency(user, accounts)

        use_local_currency = currency != constants.Currency.USD
        yesterday_costs = infobox_helpers.get_yesterday_accounts_spend(accounts, use_local_currency)
        yesterday_cost = yesterday_costs["yesterday_etfm_cost"]

        currency_symbol = core.features.multicurrency.get_currency_symbol(currency)
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Yesterday spend:", lc_helper.format_currency(yesterday_cost, curr=currency_symbol), section_start=True
            )
        )

        mtd_costs = infobox_helpers.get_mtd_accounts_spend(accounts, use_local_currency)
        mtd_cost = mtd_costs["etfm_cost"]
        overview_settings.append(
            infobox_helpers.OverviewSetting(
                "Month-to-date spend:", lc_helper.format_currency(mtd_cost, curr=currency_symbol)
            )
        )

        return overview_settings


class Demo(DASHAPIBaseView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_request_demo_v3"):
            raise Http404("Forbidden")

        _, url, password = demo.request_demo()

        email_helper.send_official_email(
            agency_or_user=request.user,
            recipient_list=[request.user.email],
            **email_helper.params_from_template(constants.EmailTemplateType.DEMO_RUNNING, url=url, password=password),
        )

        return self.create_api_response({"url": url, "password": password})


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
    # Authorization header while oauth2client sends it in request body (for get_token calls, after that
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


class PushMetrics(DASHAPIBaseView, SlackLoggerMixin):
    def get(self, request, ad_group_id, switch):
        ad_group = models.AdGroup.objects.get(id=ad_group_id)
        old_ad_group = models.AdGroup.objects.get(id=ad_group_id)
        if not request.user.has_perm("zemauth.can_enable_push_metrics"):
            raise exc.AuthorizationError()
        if ad_group.custom_flags is None:
            ad_group.custom_flags = {}
        ad_group.custom_flags["b1_push_metrics"] = switch == "enable"
        ad_group.save(None)
        k1_helper.update_ad_group(ad_group, priority=True)
        self.log_custom_flags_event_to_slack(old_ad_group, ad_group, user=request.user.email)
        timestamp = datetime.datetime.now().timestamp()
        url = f"https://redash-zemanta.outbrain.com/dashboard/wizard?p_ad_group_id={ad_group_id}&p_w643_toggle={timestamp}"
        return redirect(url)
