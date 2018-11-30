import decimal
import json
import logging
import re

from django.conf import settings
from django.contrib.auth import models as authmodels
from django.db import transaction
from django.db.models import Prefetch
from django.db.models import Q
from django.http import Http404

import core.features.goals
import core.features.goals.campaign_goal.exceptions
import core.features.goals.conversion_goal.exceptions
import core.features.multicurrency
import core.models.ad_group.exceptions
import core.models.settings.ad_group_settings.exceptions
import core.models.settings.ad_group_source_settings.exceptions
import core.models.settings.campaign_settings.exceptions
import restapi.campaigngoal.serializers
import utils.exc
from automation import autopilot
from dash import campaign_goals
from dash import constants
from dash import content_insights_helper
from dash import facebook_helper
from dash import forms
from dash import models
from dash import retargeting_helper
from dash.features import custom_flags
from dash.features import ga
from dash.features import native_server
from dash.views import helpers
from utils import api_common
from utils import dates_helper
from utils import db_for_reads
from utils import email_helper
from utils import exc
from utils import k1_helper
from utils import redirector_helper
from utils import slack
from zemauth.models import User as ZemUser

logger = logging.getLogger(__name__)

CONVERSION_PIXEL_INACTIVE_DAYS = 7
CONTENT_INSIGHTS_TABLE_ROW_COUNT = 10
SUBAGENCY_MAP = {198: (196, 198)}


class AdGroupSettings(api_common.BaseApiView):
    def get(self, request, ad_group_id):
        if not request.user.has_perm("dash.settings_view"):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        settings = ad_group.get_current_settings()

        response = {"settings": self.get_dict(request, settings, ad_group), "archived": settings.archived}

        if self.rest_proxy:
            return self.create_api_response(response)

        response.update(
            {
                "default_settings": self.get_default_settings_dict(ad_group),
                "action_is_waiting": False,
                "retargetable_adgroups": self.get_retargetable_adgroups(
                    request, ad_group, settings.retargeting_ad_groups + settings.exclusion_retargeting_ad_groups
                ),
                "audiences": self.get_audiences(
                    request, ad_group, settings.audience_targeting + settings.exclusion_audience_targeting
                ),
                "warnings": self.get_warnings(request, settings),
                "can_archive": ad_group.can_archive(),
                "can_restore": ad_group.can_restore(),
            }
        )
        if request.user.has_perm("zemauth.can_see_backend_hacks"):
            response["hacks"] = models.CustomHack.objects.all().filter_applied(ad_group=ad_group).filter_active(
                True
            ).to_dict_list() + custom_flags.helpers.get_all_custom_flags_on_ad_group(ad_group)

        return self.create_api_response(response)

    def put(self, request, ad_group_id):
        if not request.user.has_perm("dash.settings_view"):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        resource = json.loads(request.body)
        form = forms.AdGroupSettingsForm(ad_group, request.user, resource.get("settings", {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        for field in ad_group.settings.multicurrency_fields:
            form.cleaned_data["local_{}".format(field)] = form.cleaned_data.pop(field, None)
        form_data = native_server.transform_ad_group_settings(ad_group, form.cleaned_data)

        self._update_adgroup(request, ad_group, form_data)

        response = {
            "settings": self.get_dict(request, ad_group.settings, ad_group),
            "default_settings": self.get_default_settings_dict(ad_group),
            "action_is_waiting": False,
            "archived": ad_group.settings.archived,
        }

        return self.create_api_response(response)

    def _update_adgroup(self, request, ad_group, data):
        try:
            ad_group.update_bidding_type(request, data.get("bidding_type"))
            ad_group.settings.update(request, **data)

        except core.models.ad_group.exceptions.CannotChangeBiddingType as err:
            raise utils.exc.ValidationError(errors={"bidding_type": [str(err)]})

        except utils.exc.MultipleValidationError as err:
            self._handle_multiple_error(err)

        except (
            core.models.settings.ad_group_settings.exceptions.CannotChangeAdGroupState,
            core.models.settings.ad_group_settings.exceptions.CantEnableB1SourcesGroup,
        ) as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})

        except core.models.settings.ad_group_settings.exceptions.AutopilotB1SourcesNotEnabled as err:
            raise utils.exc.ValidationError(errors={"autopilot_state": [str(err)]})

        except (
            core.models.settings.ad_group_settings.exceptions.DailyBudgetAutopilotNotDisabled,
            core.models.settings.ad_group_source_settings.exceptions.DailyBudgetNegative,
        ) as err:
            raise utils.exc.ValidationError(errors={"b1_sources_group_daily_budget": [str(err)]})

        except (
            core.models.settings.ad_group_settings.exceptions.CPCAutopilotNotDisabled,
            core.models.settings.ad_group_settings.exceptions.CannotSetB1SourcesCPC,
            core.models.settings.ad_group_source_settings.exceptions.B1SourcesCPCNegative,
        ) as err:
            raise utils.exc.ValidationError(errors={"b1_sources_group_cpc_cc": [str(err)]})

        except (
            core.models.settings.ad_group_settings.exceptions.CPMAutopilotNotDisabled,
            core.models.settings.ad_group_settings.exceptions.CannotSetB1SourcesCPM,
            core.models.settings.ad_group_source_settings.exceptions.B1SourcesCPMNegative,
        ) as err:
            raise utils.exc.ValidationError(errors={"b1_sources_group_cpm": [str(err)]})

        except (
            core.models.settings.ad_group_settings.exceptions.AutopilotDailyBudgetTooLow,
            core.models.settings.ad_group_settings.exceptions.AutopilotDailyBudgetTooHigh,
        ) as err:
            raise utils.exc.ValidationError(errors={"autopilot_daily_budget": [str(err)]})

        except core.models.settings.ad_group_settings.exceptions.AdGroupNotPaused as err:
            raise utils.exc.ValidationError(errors={"b1_sources_group_enabled": [str(err)]})

        except core.models.settings.ad_group_settings.exceptions.B1DailyBudgetTooHigh as err:
            raise utils.exc.ValidationError(errors={"daily_budget_cc": [str(err)]})

        except core.models.settings.ad_group_settings.exceptions.BluekaiCategoryInvalid as err:
            raise utils.exc.ValidationError(str(err))

        except core.models.settings.ad_group_settings.exceptions.YahooDesktopCPCTooLow as err:
            raise utils.exc.ValidationError(errors={"target_devices": [str(err)]})

        except core.models.settings.ad_group_settings.exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"whitelist_publisher_groups": [str(err)]})

        except core.models.settings.ad_group_settings.exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"blacklist_publisher_groups": [str(err)]})

        except core.models.settings.ad_group_source_settings.exceptions.CPCPrecisionExceeded as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_cpc_cc": [
                        "CPC on {} cannot exceed {} decimal place{}.".format(
                            err.data.get("source_name"),
                            err.data.get("value"),
                            "s" if err.data.get("value") != 1 else "",
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.CPMPrecisionExceeded as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_cpm": [
                        "CPM on {} cannot exceed {} decimal place{}.".format(
                            err.data.get("source_name"),
                            err.data.get("value"),
                            "s" if err.data.get("value") != 1 else "",
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MinimalCPCTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_cpc_cc": [
                        "Minimum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalCPCTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_cpc_cc": [
                        "Maximum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MinimalCPMTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_cpm": [
                        "Minimum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalCPMTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_cpm": [
                        "Maximum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MinimalDailyBudgetTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_daily_budget": [
                        "Please provide daily spend cap of at least {}.".format(
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_CEILING, ad_group.settings.get_currency()
                            )
                        )
                    ]
                }
            )

        except core.models.settings.ad_group_source_settings.exceptions.MaximalDailyBudgetTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "b1_sources_group_daily_budget": [
                        "Maximum allowed daily spend cap is {}. "
                        "If you want use a higher daily spend cap, please contact support.".format(
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_FLOOR, ad_group.settings.get_currency()
                            )
                        )
                    ]
                }
            )

    def _handle_multiple_error(self, err):
        errors = {}
        for e in err.errors:
            if isinstance(e, core.models.settings.ad_group_settings.exceptions.CannotSetCPC):
                errors.setdefault("cpc_cc", []).append(str(e))

            if isinstance(e, core.models.settings.ad_group_settings.exceptions.CannotSetCPM):
                errors.setdefault("max_cpm", []).append(str(e))

            if isinstance(e, core.models.settings.ad_group_settings.exceptions.MaxCPCTooLow):
                errors.setdefault("cpc_cc", []).append(str(e))

            elif isinstance(e, core.models.settings.ad_group_settings.exceptions.MaxCPCTooHigh):
                errors.setdefault("cpc_cc", []).append(str(e))

            elif isinstance(e, core.models.settings.ad_group_settings.exceptions.MaxCPMTooLow):
                errors.setdefault("max_cpm", []).append(str(e))

            elif isinstance(e, core.models.settings.ad_group_settings.exceptions.MaxCPMTooHigh):
                errors.setdefault("max_cpm", []).append(str(e))

            elif isinstance(e, core.models.settings.ad_group_settings.exceptions.EndDateBeforeStartDate):
                errors.setdefault("end_date", []).append(str(e))

            elif isinstance(e, core.models.settings.ad_group_settings.exceptions.EndDateInThePast):
                errors.setdefault("end_date", []).append(str(e))

            elif isinstance(e, core.models.settings.ad_group_settings.exceptions.TrackingCodeInvalid):
                errors.setdefault("tracking_code", []).append(str(e))

        raise utils.exc.ValidationError(errors=errors)

    def get_warnings(self, request, ad_group_settings):
        warnings = {}

        ad_group_sources = ad_group_settings.ad_group.adgroupsource_set.all().select_related("source", "settings")
        supports_retargeting, unsupported_sources = retargeting_helper.supports_retargeting(ad_group_sources)
        if not supports_retargeting:
            retargeting_warning = {"sources": [s.name for s in unsupported_sources]}
            warnings["retargeting"] = retargeting_warning

        return warnings

    def get_dict(self, request, settings, ad_group):
        if not settings:
            return {}

        result = {
            "id": str(ad_group.pk),
            "campaign_id": str(ad_group.campaign_id),
            "name": settings.ad_group_name,
            "state": settings.state,
            "bidding_type": ad_group.bidding_type,
            "start_date": settings.start_date,
            "end_date": settings.end_date,
            "cpc_cc": "{:.3f}".format(settings.local_cpc_cc) if settings.local_cpc_cc is not None else "",
            "max_cpm": "{:.3f}".format(settings.local_max_cpm) if settings.local_max_cpm is not None else "",
            "daily_budget_cc": "{:.2f}".format(settings.daily_budget_cc)
            if settings.daily_budget_cc is not None
            else "",
            "tracking_code": settings.tracking_code,
            "autopilot_on_campaign": ad_group.campaign.settings.autopilot,
            "autopilot_state": settings.autopilot_state,
            "autopilot_daily_budget": "{:.2f}".format(settings.local_autopilot_daily_budget)
            if settings.local_autopilot_daily_budget is not None
            else "",
            "retargeting_ad_groups": settings.retargeting_ad_groups,
            "exclusion_retargeting_ad_groups": settings.exclusion_retargeting_ad_groups,
            "notes": settings.notes,
            "interest_targeting": settings.interest_targeting,
            "exclusion_interest_targeting": settings.exclusion_interest_targeting,
            "audience_targeting": settings.audience_targeting,
            "exclusion_audience_targeting": settings.exclusion_audience_targeting,
            "redirect_pixel_urls": settings.redirect_pixel_urls,
            "redirect_javascript": settings.redirect_javascript,
            "dayparting": settings.dayparting,
            "b1_sources_group_enabled": settings.b1_sources_group_enabled,
            "b1_sources_group_daily_budget": settings.local_b1_sources_group_daily_budget,
            "b1_sources_group_cpc_cc": settings.local_b1_sources_group_cpc_cc,
            "b1_sources_group_cpm": settings.local_b1_sources_group_cpm,
            "b1_sources_group_state": settings.b1_sources_group_state,
            "whitelist_publisher_groups": settings.whitelist_publisher_groups,
            "blacklist_publisher_groups": settings.blacklist_publisher_groups,
            "delivery_type": settings.delivery_type,
        }

        # This two properties are very expensive to calculate and are never used by the REST api.
        if not self.rest_proxy:
            primary_campaign_goal = campaign_goals.get_primary_campaign_goal(ad_group.campaign)
            result["autopilot_min_budget"] = autopilot.get_adgroup_minimum_daily_budget(ad_group, settings)
            result["autopilot_optimization_goal"] = primary_campaign_goal.type if primary_campaign_goal else None

        if request.user.has_perm("zemauth.can_set_click_capping"):
            result["click_capping_daily_ad_group_max_clicks"] = settings.click_capping_daily_ad_group_max_clicks
            result["click_capping_daily_click_budget"] = settings.click_capping_daily_click_budget

        # TODO (refactor-workaround) Re-use restapi serializers
        from restapi.serializers.targeting import (
            DevicesSerializer,
            OSsSerializer,
            PlacementsSerializer,
            AudienceSerializer,
            TargetRegionsSerializer,
            BrowsersSerializer,
        )

        result["target_regions"] = TargetRegionsSerializer(settings.target_regions).data
        result["exclusion_target_regions"] = TargetRegionsSerializer(settings.exclusion_target_regions).data
        result["target_devices"] = DevicesSerializer(settings.target_devices).data
        result["target_os"] = OSsSerializer(settings.target_os).data
        result["target_browsers"] = BrowsersSerializer(settings.target_browsers).data
        result["target_placements"] = PlacementsSerializer(settings.target_placements).data
        result["bluekai_targeting"] = AudienceSerializer(settings.bluekai_targeting).data
        result["bluekai_targeting_old"] = AudienceSerializer(settings.bluekai_targeting, use_list_repr=True).data

        if request.user.has_perm("zemauth.can_set_frequency_capping"):
            result["frequency_capping"] = settings.frequency_capping

        return result

    def get_default_settings_dict(self, ad_group):
        settings = ad_group.campaign.get_current_settings()
        result = dict()

        # TODO (refactor-workaround) Re-use restapi serializers
        from restapi.serializers.targeting import (
            DevicesSerializer,
            OSsSerializer,
            PlacementsSerializer,
            TargetRegionsSerializer,
        )

        result["target_regions"] = TargetRegionsSerializer(settings.target_regions).data
        result["exclusion_target_regions"] = TargetRegionsSerializer(settings.exclusion_target_regions).data
        result["target_devices"] = DevicesSerializer(settings.target_devices).data
        result["target_os"] = OSsSerializer(settings.target_os).data
        result["target_placements"] = PlacementsSerializer(settings.target_placements).data

        return result

    def get_retargetable_adgroups(self, request, ad_group, existing_targetings):
        """
        Get adgroups that can retarget this adgroup
        """
        if not request.user.has_perm("zemauth.can_view_retargeting_settings"):
            return []

        account = ad_group.campaign.account

        if account.id == 305:  # OEN
            return []

        ad_groups = models.AdGroup.objects.filter(campaign__account=account).select_related("campaign").order_by("id")

        ad_group_settings = (
            models.AdGroupSettings.objects.all()
            .filter(ad_group__campaign__account=account)
            .group_current_settings()
            .values_list("ad_group__id", "archived")
        )
        archived_map = {adgs[0]: adgs[1] for adgs in ad_group_settings}

        if request.user.has_perm("zemauth.can_target_custom_audiences"):
            result = [
                {
                    "id": adg.id,
                    "name": adg.name,
                    "archived": archived_map.get(adg.id) or False,
                    "campaign_name": adg.campaign.name,
                }
                for adg in ad_groups
                if not archived_map.get(adg.id) or adg.id in existing_targetings
            ]
        else:
            result = [
                {
                    "id": adg.id,
                    "name": adg.name,
                    "archived": archived_map.get(adg.id) or False,
                    "campaign_name": adg.campaign.name,
                }
                for adg in ad_groups
            ]

        return result

    def get_audiences(self, request, ad_group, existing_targetings):
        if not request.user.has_perm("zemauth.can_target_custom_audiences"):
            return []

        audiences = (
            models.Audience.objects.filter(pixel__account_id=ad_group.campaign.account.pk)
            .filter(Q(archived=False) | Q(pk__in=existing_targetings))
            .order_by("name")
        )

        return [
            {"id": audience.pk, "name": audience.name, "archived": audience.archived or False} for audience in audiences
        ]


class AdGroupSettingsState(api_common.BaseApiView):
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        current_settings = ad_group.get_current_settings()
        return self.create_api_response({"id": str(ad_group.pk), "state": current_settings.state})

    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        data = json.loads(request.body)
        new_state = data.get("state")

        campaign_settings = ad_group.campaign.get_current_settings()
        helpers.validate_ad_groups_state([ad_group], ad_group.campaign, campaign_settings, new_state)

        try:
            ad_group.settings.update(request, state=new_state)

        except core.models.settings.ad_group_settings.exceptions.CannotChangeAdGroupState as err:
            raise utils.exc.ValidationError(error={"state": [str(err)]})

        return self.create_api_response({"id": str(ad_group.pk), "state": new_state})


class CampaignGoalValidation(api_common.BaseApiView):
    def post(self, request, campaign_id):
        if not request.user.has_perm("zemauth.can_see_campaign_goals"):
            raise exc.MissingDataError()
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_goal = json.loads(request.body)
        goal_form = forms.CampaignGoalForm(campaign_goal, campaign_id=campaign.pk)

        errors = {}
        result = {}
        if not goal_form.is_valid():
            errors.update(dict(goal_form.errors))

        if "type" in campaign_goal and campaign_goal["type"] == constants.CampaignGoalKPI.CPA:
            if not campaign_goal.get("id"):
                conversion_form = forms.ConversionGoalForm(
                    campaign_goal.get("conversion_goal", {}), campaign_id=campaign.pk
                )
                if conversion_form.is_valid():
                    result["conversion_goal"] = conversion_form.cleaned_data
                else:
                    errors["conversion_goal"] = conversion_form.errors

        if errors:
            raise exc.ValidationError(errors=errors)

        return self.create_api_response(result)


class CampaignSettings(api_common.BaseApiView):
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        response = {
            "settings": self.get_dict(request, campaign.settings, campaign),
            "archived": campaign.settings.archived,
            "language": campaign.settings.language,
        }
        if request.user.has_perm("zemauth.can_see_campaign_goals"):
            response["goals"] = self.get_campaign_goals(request, campaign)
            response["goals_defaults"] = restapi.campaigngoal.serializers.CampaignGoalsDefaultsSerializer(
                core.features.goals.get_campaign_goals_defaults(campaign.account)
            ).data

        if self.rest_proxy:
            return self.create_api_response(response)

        response["can_archive"] = campaign.can_archive()
        response["can_restore"] = campaign.can_restore()

        if request.user.has_perm("zemauth.can_modify_campaign_manager"):
            response["campaign_managers"] = self.get_campaign_managers(request, campaign, campaign.settings)

        if request.user.has_perm("zemauth.can_see_backend_hacks"):
            response["hacks"] = models.CustomHack.objects.all().filter_applied(campaign=campaign).filter_active(
                True
            ).to_dict_list() + custom_flags.helpers.get_all_custom_flags_on_campaign(campaign)

        return self.create_api_response(response)

    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        resource = json.loads(request.body)

        settings_dict = resource.get("settings", {})

        settings_form = forms.CampaignSettingsForm(campaign, settings_dict)
        errors = {}
        if not settings_form.is_valid():
            errors.update(dict(settings_form.errors))

        current = models.CampaignGoal.objects.filter(campaign=campaign)
        changes = resource.get("goals", {"added": [], "removed": [], "primary": None, "modified": {}})
        changes = native_server.apply_set_goals_hacks(campaign, changes)

        # If the view is used via a REST API proxy, don't require goals to be already defined,
        # since that produces a chicken-and-egg problem. REST API combines POST and PUT calls into one
        # on campaign creation and thus can't have campaign goals created yet.
        if not self.rest_proxy and len(current) - len(changes["removed"]) + len(changes["added"]) <= 0:
            errors["no_goals"] = "At least one goal must be defined"
            raise exc.ValidationError(errors=errors)

        form_data = native_server.transform_campaign_settings(campaign, settings_form.cleaned_data)

        with transaction.atomic():
            try:
                campaign.update_type(form_data.get("type"))
                campaign.settings.update(request, **form_data)

            except core.models.campaign.exceptions.CannotChangeType as err:
                raise utils.exc.ValidationError(errors={"type": [str(err)]})

            except core.models.settings.campaign_settings.exceptions.CannotChangeLanguage as err:
                raise utils.exc.ValidationError(errors={"language": [str(err)]})

            except core.models.settings.campaign_settings.exceptions.PublisherWhitelistInvalid as err:
                raise utils.exc.ValidationError(errors={"whitelist_publisher_groups": [str(err)]})

            except core.models.settings.campaign_settings.exceptions.PublisherBlacklistInvalid as err:
                raise utils.exc.ValidationError(errors={"blacklist_publisher_groups": [str(err)]})

            goal_errors = self.set_goals(request, campaign, changes)

            if any(goal_error for goal_error in goal_errors):
                errors["goals"] = goal_errors

            if errors:
                raise exc.ValidationError(errors=errors)

            native_server.apply_campaign_change_hacks(request, campaign, changes)

        response = {
            "settings": self.get_dict(request, campaign.settings, campaign),
            "archived": campaign.settings.archived,
        }

        if request.user.has_perm("zemauth.can_see_campaign_goals"):
            response["goals"] = self.get_campaign_goals(request, campaign)

        return self.create_api_response(response)

    def set_goals(self, request, campaign, changes):
        if not request.user.has_perm("zemauth.can_see_campaign_goals"):
            return []

        new_primary_id = None
        errors = []
        for goal in changes["added"]:
            is_primary = goal["primary"]

            goal["primary"] = False

            with transaction.atomic():
                conversion_goal = goal.get("conversion_goal")
                if conversion_goal:
                    conversion_form = forms.ConversionGoalForm(
                        {
                            "type": conversion_goal.get("type"),
                            "conversion_window": conversion_goal.get("conversion_window"),
                            "goal_id": conversion_goal.get("goal_id"),
                        },
                        campaign_id=campaign.pk,
                    )
                    if not conversion_form.is_valid():
                        raise exc.ValidationError(errors=conversion_form.errors)
                    errors.append(dict(conversion_form.errors))

                    try:
                        new_conversion_goal = models.ConversionGoal.objects.create(
                            request,
                            campaign,
                            conversion_goal_type=conversion_form.cleaned_data["type"],
                            goal_id=conversion_form.cleaned_data["goal_id"],
                            conversion_window=conversion_form.cleaned_data["conversion_window"],
                        )

                    except core.features.goals.conversion_goal.exceptions.ConversionGoalLimitExceeded as err:
                        raise utils.exc.ValidationError(str(err))

                    except core.features.goals.conversion_goal.exceptions.ConversionWindowRequired as err:
                        raise utils.exc.ValidationError(errors={"conversion_window": [str(err)]})

                    except core.features.goals.conversion_goal.exceptions.ConversionPixelInvalid as err:
                        raise utils.exc.ValidationError(errors={"goal_id": [str(err)]})

                    except core.features.goals.conversion_goal.exceptions.ConversionGoalNotUnique as err:
                        raise utils.exc.ValidationError(str(err))

                    except core.features.goals.conversion_goal.exceptions.GoalIDInvalid as err:
                        raise utils.exc.ValidationError(errors={"goal_id": [str(err)]})

                else:
                    goal_form = forms.CampaignGoalForm(goal, campaign_id=campaign.pk)
                    errors.append(dict(goal_form.errors))
                    if not goal_form.is_valid():
                        raise exc.ValidationError(errors=goal_form.errors)

                try:
                    goal_added = models.CampaignGoal.objects.create(
                        request,
                        campaign,
                        goal_type=constants.CampaignGoalKPI.CPA if conversion_goal else goal_form.cleaned_data["type"],
                        value=goal["value"],
                        primary=False if conversion_goal else goal_form.cleaned_data["primary"],
                        conversion_goal=new_conversion_goal if conversion_goal else None,
                    )

                except core.features.goals.campaign_goal.exceptions.ConversionGoalLimitExceeded as err:
                    raise utils.exc.ValidationError(str(err))

                except core.features.goals.campaign_goal.exceptions.MultipleSameTypeGoals as err:
                    raise utils.exc.ValidationError(str(err))

                except core.features.goals.campaign_goal.exceptions.ConversionGoalRequired as err:
                    raise utils.exc.ValidationError(str(err))

            if is_primary:
                new_primary_id = goal_added.pk

        for goal_id, value in changes["modified"].items():
            goal = models.CampaignGoal.objects.get(pk=goal_id)
            goal.add_local_value(request, value)

        removed_goals = {goal["id"] for goal in changes["removed"]}
        for goal_id in removed_goals:
            campaign_goals.delete_campaign_goal(request, goal_id, campaign)

        new_primary_id = new_primary_id or changes["primary"]
        if new_primary_id and new_primary_id not in removed_goals:
            try:
                goal = models.CampaignGoal.objects.get(pk=new_primary_id)
                goal.set_primary(request)
            except exc.ValidationError as error:
                errors.append(str(error))

        return errors

    def get_campaign_goals(self, request, campaign):
        ret = []
        goals = (
            models.CampaignGoal.objects.filter(campaign=campaign)
            .prefetch_related(Prefetch("values", queryset=models.CampaignGoalValue.objects.order_by("created_dt")))
            .select_related("conversion_goal")
            .order_by("id")
        )

        for campaign_goal in goals:
            goal_blob = campaign_goal.to_dict(with_values=True, local_values=True)
            conversion_goal = campaign_goal.conversion_goal
            if conversion_goal is not None and conversion_goal.type == constants.ConversionGoalType.PIXEL:
                goal_blob["conversion_goal"]["pixel_url"] = conversion_goal.pixel.get_url()
            ret.append(goal_blob)
        return ret

    def get_dict(self, request, settings, campaign):
        if not settings:
            return {}

        result = {
            "id": str(campaign.pk),
            "account_id": str(campaign.account_id),
            "name": campaign.name,
            "campaign_goal": settings.campaign_goal,
            "language": settings.language,
            "type": campaign.type,
            "enable_ga_tracking": settings.enable_ga_tracking,
            "ga_property_id": settings.ga_property_id,
            "ga_tracking_type": settings.ga_tracking_type,
            "enable_adobe_tracking": settings.enable_adobe_tracking,
            "adobe_tracking_param": settings.adobe_tracking_param,
            "whitelist_publisher_groups": settings.whitelist_publisher_groups,
            "blacklist_publisher_groups": settings.blacklist_publisher_groups,
            "autopilot": settings.autopilot,
        }

        if request.user.has_perm("zemauth.can_modify_campaign_manager"):
            result["campaign_manager"] = (
                str(settings.campaign_manager_id) if settings.campaign_manager_id is not None else None
            )

        if request.user.has_perm("zemauth.can_modify_campaign_iab_category"):
            result["iab_category"] = settings.iab_category

        if settings.enable_ga_tracking and settings.ga_property_id:
            try:
                result["ga_property_readable"] = ga.is_readable(settings.ga_property_id)
            except Exception:
                logger.exception("Google Analytics validation failed")

        # TODO (refactor-workaround) Re-use restapi serializers
        from restapi.serializers.targeting import (
            DevicesSerializer,
            OSsSerializer,
            PlacementsSerializer,
            TargetRegionsSerializer,
        )

        result["target_regions"] = TargetRegionsSerializer(settings.target_regions).data
        result["exclusion_target_regions"] = TargetRegionsSerializer(settings.exclusion_target_regions).data
        result["target_devices"] = DevicesSerializer(settings.target_devices).data
        result["target_os"] = OSsSerializer(settings.target_os).data
        result["target_placements"] = PlacementsSerializer(settings.target_placements).data

        if request.user.has_perm("zemauth.can_set_frequency_capping"):
            result["frequency_capping"] = settings.frequency_capping

        return result

    def get_campaign_managers(self, request, campaign, settings):
        users = helpers.get_users_for_manager(request.user, campaign.account, settings.campaign_manager)
        return [{"id": str(user.id), "name": helpers.get_user_full_name_or_email(user)} for user in users]


class ConversionPixel(api_common.BaseApiView):
    def get(self, request, account_id):
        account_id = int(account_id)
        account = helpers.get_account(request.user, account_id)

        audience_enabled_only = request.GET.get("audience_enabled_only", "") == "1"

        pixels = models.ConversionPixel.objects.filter(account=account)
        if audience_enabled_only:
            pixels = pixels.filter(Q(audience_enabled=True) | Q(additional_pixel=True))

        yesterday = dates_helper.local_yesterday()
        rows = [self._format_pixel(pixel, request.user, date=yesterday) for pixel in pixels]

        return self.create_api_response(
            {"rows": rows, "conversion_pixel_tag_prefix": settings.CONVERSION_PIXEL_PREFIX + str(account.id) + "/"}
        )

    def post(self, request, account_id):
        account_id = int(account_id)

        account = helpers.get_account(request.user, account_id)  # check access to account

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError()

        form = forms.ConversionPixelForm(data)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        try:
            models.ConversionPixel.objects.get(account_id=account_id, name=form.cleaned_data["name"])
            form.add_error("name", "Conversion pixel with this name already exists.")
            raise exc.ValidationError(errors=dict(form.errors))
        except models.ConversionPixel.DoesNotExist:
            pass

        redirect_url = ""
        if request.user.has_perm("zemauth.can_redirect_pixels"):
            redirect_url = form.cleaned_data["redirect_url"]

        notes = ""
        if request.user.has_perm("zemauth.can_see_pixel_notes"):
            notes = form.cleaned_data["notes"]

        additional_pixel = False
        if form.cleaned_data["additional_pixel"]:
            if request.user.has_perm("zemauth.can_promote_additional_pixel"):
                additional_pixel = form.cleaned_data["additional_pixel"]
            else:
                raise exc.AuthorizationError("Not authorized to set pixel to additional pixel.")

        with transaction.atomic():
            conversion_pixel = models.ConversionPixel.objects.create(
                account_id=account_id,
                name=form.cleaned_data["name"],
                audience_enabled=form.cleaned_data["audience_enabled"] or False,
                redirect_url=redirect_url,
                notes=notes,
                additional_pixel=additional_pixel,
            )

            # This check is done after insertion because we use READ COMMITED
            # isolation level.
            if conversion_pixel.audience_enabled:
                audience_pixels = (
                    models.ConversionPixel.objects.filter(account_id=account_id)
                    .filter(audience_enabled=True)
                    .exclude(pk=conversion_pixel.id)
                )
                if audience_pixels:
                    msg = (
                        "This pixel cannot be used for building custom audiences "
                        "because another pixel is already used: {}."
                    ).format(audience_pixels[0].name)
                    raise exc.ValidationError(errors={"audience_enabled": msg})

                k1_helper.update_account(account, msg="conversion_pixel.create")

                changes_text = "Added conversion pixel with audience enabled named {}.".format(conversion_pixel.name)
                account.write_history(
                    changes_text,
                    user=request.user,
                    action_type=constants.HistoryActionType.CONVERSION_PIXEL_AUDIENCE_ENABLED,
                )

            elif conversion_pixel.additional_pixel:
                audience_pixels = (
                    models.ConversionPixel.objects.filter(account_id=account_id)
                    .filter(audience_enabled=True)
                    .exclude(pk=conversion_pixel.id)
                )
                if not audience_pixels:
                    msg = (
                        "The pixel's account has no audience pixel set. Set an audience pixel before setting an"
                        " additional audience pixel."
                    )
                    form.add_error("additional_pixel", msg)
                    raise exc.ValidationError(errors=dict(form.errors))

                k1_helper.update_account(account, msg="conversion_pixel.create")
                changes_text = 'Created a pixel named "{}" as additional audience pixel.'.format(conversion_pixel.name)
                account.write_history(
                    changes_text,
                    user=request.user,
                    action_type=constants.HistoryActionType.CONVERSION_PIXEL_CREATE_AS_ADDITIONAL,
                )
            else:
                changes_text = "Added conversion pixel named {}.".format(conversion_pixel.name)
                account.write_history(
                    changes_text, user=request.user, action_type=constants.HistoryActionType.CONVERSION_PIXEL_CREATE
                )

        if redirect_url:
            redirector_helper.update_pixel(conversion_pixel)

        email_helper.send_account_pixel_notification(account, request)

        return self.create_api_response(self._format_pixel(conversion_pixel, request.user))

    def put(self, request, conversion_pixel_id):
        try:
            conversion_pixel = models.ConversionPixel.objects.get(id=conversion_pixel_id)
        except models.ConversionPixel.DoesNotExist:
            raise exc.MissingDataError("Conversion pixel does not exist")

        try:
            account = helpers.get_account(request.user, conversion_pixel.account_id)  # check access to account
        except exc.MissingDataError:
            raise exc.MissingDataError("Conversion pixel does not exist")

        try:
            data = json.loads(request.body)
        except ValueError:
            raise exc.ValidationError()

        form = forms.ConversionPixelForm(data)
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        with transaction.atomic():
            self._write_audience_enabled_change_to_history(request, account, conversion_pixel, form.cleaned_data)

            if "audience_enabled" in form.cleaned_data and form.cleaned_data["audience_enabled"]:
                conversion_pixel.audience_enabled = form.cleaned_data["audience_enabled"]

            if "archived" in form.cleaned_data and request.user.has_perm("zemauth.archive_restore_entity"):
                self._write_archived_change_to_history(request, account, conversion_pixel, form.cleaned_data)
                conversion_pixel.archived = form.cleaned_data["archived"]

                if conversion_pixel.archived and (
                    conversion_pixel.audience_enabled or conversion_pixel.additional_pixel
                ):
                    raise exc.ValidationError(
                        errors={"audience_enabled": ("Cannot archive pixel used for " "building custom audiences.")}
                    )

            if request.user.has_perm("zemauth.can_redirect_pixels"):
                self._write_redirect_change_to_history(request, account, conversion_pixel, form.cleaned_data)
                conversion_pixel.redirect_url = form.cleaned_data["redirect_url"]
                redirector_helper.update_pixel(conversion_pixel)

            if request.user.has_perm("zemauth.can_see_pixel_notes"):
                conversion_pixel.notes = form.cleaned_data["notes"]

            if form.cleaned_data["additional_pixel"] and request.user.has_perm("zemauth.can_promote_additional_pixel"):

                if not conversion_pixel.account.conversionpixel_set.filter(audience_enabled=True).count():
                    form.add_error(
                        "additional_pixel",
                        (
                            "The pixel's account has no audience pixel set. Set an "
                            "audience pixel before setting an additional audience pixel."
                        ),
                    )
                    raise exc.ValidationError(errors=dict(form.errors))
                self._write_additional_pixel_change_to_history(request, account, conversion_pixel, form.cleaned_data)
                conversion_pixel.additional_pixel = form.cleaned_data["additional_pixel"]

            self._write_name_change_to_history(request, account, conversion_pixel, form.cleaned_data)
            conversion_pixel.name = form.cleaned_data["name"]
            conversion_pixel.save()

            # This check is done after insertion because we use READ COMMITED
            # isolation level.
            if conversion_pixel.audience_enabled or conversion_pixel.additional_pixel:
                audience_pixels = (
                    models.ConversionPixel.objects.filter(account_id=conversion_pixel.account_id)
                    .filter(audience_enabled=True)
                    .exclude(pk=conversion_pixel.id)
                )
                if audience_pixels and not conversion_pixel.additional_pixel:
                    msg = "This pixel cannot be used for building custom audiences because another pixel is already used: {}.".format(
                        audience_pixels[0].name
                    )  # noqa
                    raise exc.ValidationError(errors={"audience_enabled": msg})
                k1_helper.update_account(conversion_pixel.account, msg="conversion_pixel.update")
                self._r1_upsert_audiences(conversion_pixel)

        return self.create_api_response(self._format_pixel(conversion_pixel, request.user))

    def _r1_upsert_audiences(self, conversion_pixel):
        audiences = models.Audience.objects.filter(pixel_id=conversion_pixel.id).filter(archived=False)
        for audience in audiences:
            redirector_helper.upsert_audience(audience)

    def _write_archived_change_to_history(self, request, account, conversion_pixel, data):
        if data["archived"] == conversion_pixel.archived:
            return

        changes_text = "{} conversion pixel named {}.".format(
            "Archived" if data["archived"] else "Restored", conversion_pixel.name
        )
        account.write_history(
            changes_text, user=request.user, action_type=constants.HistoryActionType.CONVERSION_PIXEL_ARCHIVE_RESTORE
        )

    def _write_name_change_to_history(self, request, account, conversion_pixel, data):
        if data["name"] == conversion_pixel.name:
            return

        changes_text = "Renamed conversion pixel named {} to {}.".format(conversion_pixel.name, data["name"])
        account.write_history(
            changes_text, user=request.user, action_type=constants.HistoryActionType.CONVERSION_PIXEL_RENAME
        )

    def _write_additional_pixel_change_to_history(self, request, account, conversion_pixel, data):
        if data["additional_pixel"] == conversion_pixel.additional_pixel:
            return
        elif data["additional_pixel"]:
            account.write_history(
                'Set pixel "{}" as an additional audience pixel.'.format(conversion_pixel.name),
                user=request.user,
                action_type=constants.HistoryActionType.CONVERSION_PIXEL_SET_ADDITIONAL_PIXEL,
            )

    def _write_audience_enabled_change_to_history(self, request, account, conversion_pixel, data):
        if data["audience_enabled"] and not conversion_pixel.audience_enabled:
            change_text = "Pixel {} enabled for building audiences".format(data["name"])
            account.write_history(
                change_text,
                user=request.user,
                action_type=constants.HistoryActionType.CONVERSION_PIXEL_AUDIENCE_ENABLED,
            )

    def _write_redirect_change_to_history(self, request, account, conversion_pixel, data):
        if data["redirect_url"] == conversion_pixel.redirect_url:
            return

        if data["redirect_url"]:
            changes_text = "Set redirect url of pixel named {} to {}.".format(
                conversion_pixel.name, data["redirect_url"]
            )
        else:
            changes_text = "Removed redirect url of pixel named {}.".format(conversion_pixel.name)
        account.write_history(
            changes_text, user=request.user, action_type=constants.HistoryActionType.CONVERSION_PIXEL_SET_REDIRECT_URL
        )

    def _format_pixel(self, pixel, user, date=None):
        if date is None:
            date = dates_helper.local_yesterday()
        data = {
            "id": pixel.id,
            "name": pixel.name,
            "url": pixel.get_url(),
            "audience_enabled": pixel.audience_enabled,
            "additional_pixel": pixel.additional_pixel,
            "archived": pixel.archived,
        }
        if user.has_perm("zemauth.can_see_pixel_traffic"):
            data["last_triggered"] = pixel.last_triggered
            data["impressions"] = 0
            if pixel.last_triggered and pixel.last_triggered.date() >= date:
                data["impressions"] = pixel.impressions
        if user.has_perm("zemauth.can_redirect_pixels"):
            data["redirect_url"] = pixel.redirect_url
        if user.has_perm("zemauth.can_see_pixel_notes"):
            data["notes"] = pixel.notes
        return data


class AccountSettings(api_common.BaseApiView):
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        account_settings = account.get_current_settings()

        response = {
            "settings": self.get_dict(request, account_settings, account),
            "can_archive": account.can_archive(),
            "can_restore": account.can_restore(),
            "archived": account_settings.archived,
        }

        self._add_agencies(request, response)

        if request.user.has_perm("zemauth.can_modify_account_manager"):
            response["account_managers"] = self.get_account_managers(request, account, account_settings)

        if request.user.has_perm("zemauth.can_set_account_sales_representative"):
            response["sales_reps"] = self.get_sales_representatives(account)
        if request.user.has_perm("zemauth.can_set_account_cs_representative"):
            response["cs_reps"] = self.get_cs_representatives(account)
        if request.user.has_perm("zemauth.can_set_account_ob_representative"):
            response["ob_reps"] = self.get_ob_representatives()
        if request.user.has_perm("zemauth.can_see_backend_hacks"):
            response["hacks"] = models.CustomHack.objects.all().filter_applied(account=account).filter_active(
                True
            ).to_dict_list() + custom_flags.helpers.get_all_custom_flags_on_account(account)

        return self.create_api_response(response)

    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.AccountSettingsForm(account, resource.get("settings", {}))
        settings = self.save_settings(request, account, form)
        response = {
            "settings": self.get_dict(request, settings, account),
            "can_archive": account.can_archive(),
            "can_restore": account.can_restore(),
        }

        self._add_agencies(request, response)

        return self.create_api_response(response)

    def _add_agencies(self, request, response):
        if request.user.has_perm("zemauth.can_set_agency_for_account"):
            response["agencies"] = list(
                models.Agency.objects.all().values(
                    "name", "sales_representative", "cs_representative", "ob_representative", "default_account_type"
                )
            )

    def save_settings(self, request, account, form):
        old_name = account.name

        with transaction.atomic():
            # Form is additionally validated in self.set_allowed_sources method
            if not form.is_valid():
                data = self.get_validation_error_data(request, account)
                raise exc.ValidationError(errors=dict(form.errors), data=data)

            self._validate_essential_account_settings(request.user, form)

            self.set_account(request, account, form.cleaned_data)

            settings = account.get_current_settings().copy_settings()
            self.set_settings(settings, account, form.cleaned_data)

            if (
                "allowed_sources" in form.cleaned_data
                and form.cleaned_data["allowed_sources"] is not None
                and not request.user.has_perm("zemauth.can_modify_allowed_sources")
            ):
                raise exc.AuthorizationError()

            if "account_type" in form.cleaned_data and form.cleaned_data["account_type"]:
                if not request.user.has_perm("zemauth.can_modify_account_type"):
                    raise exc.AuthorizationError()
                settings.account_type = form.cleaned_data["account_type"]

            if "salesforce_url" in form.cleaned_data and form.cleaned_data["salesforce_url"]:
                if not request.user.has_perm("zemauth.can_see_salesforce_url"):
                    raise exc.AuthorizationError()
                settings.salesforce_url = form.cleaned_data["salesforce_url"]

            if "allowed_sources" in form.cleaned_data and form.cleaned_data["allowed_sources"] is not None:
                changes_text = self.set_allowed_sources(
                    settings, account, request.user.has_perm("zemauth.can_see_all_available_sources"), form
                )
                account.write_history(
                    changes_text, action_type=constants.HistoryActionType.SETTINGS_CHANGE, user=request.user
                )

            if "facebook_page" in form.data:
                if not request.user.has_perm("zemauth.can_modify_facebook_page"):
                    raise exc.AuthorizationError()
                facebook_account = self.get_or_create_facebook_account(account)
                self.set_facebook_page(facebook_account, form)
                facebook_account.save()

            if request.user.has_perm("zemauth.can_set_white_blacklist_publisher_groups"):
                if "whitelist_publisher_groups" in form.cleaned_data:
                    settings.whitelist_publisher_groups = form.cleaned_data["whitelist_publisher_groups"]
                if "blacklist_publisher_groups" in form.cleaned_data:
                    settings.blacklist_publisher_groups = form.cleaned_data["blacklist_publisher_groups"]

            if request.user.has_perm("zemauth.can_set_auto_add_new_sources"):
                if "auto_add_new_sources" in form.cleaned_data:
                    settings.auto_add_new_sources = form.cleaned_data["auto_add_new_sources"]

            if "frequency_capping" in form.cleaned_data and form.cleaned_data["frequency_capping"]:
                if not request.user.has_perm("zemauth.can_set_frequency_capping"):
                    raise exc.AuthorizationError()
                settings.frequency_capping = form.cleaned_data["frequency_capping"]

            account.save(request)
            settings.save(request, action_type=constants.HistoryActionType.SETTINGS_CHANGE)

            if account.name != old_name and "New account" in old_name:
                slack_msg = (
                    "Account #<https://one.zemanta.com/v2/analytics/account/{id}|{id}> {name} was created"
                    "{agency}.".format(
                        id=account.id,
                        name=account.name,
                        agency=" for agency {}".format(account.agency.name) if account.agency else "",
                    )
                )
                try:
                    slack.publish(text=slack_msg, channel="z1-new-accounts")
                except Exception:
                    logger.exception("Connection error with Slack.")

            return settings

    def _validate_essential_account_settings(self, user, form):
        if (
            "default_sales_representative" in form.cleaned_data
            and form.cleaned_data["default_sales_representative"] is not None
            and not user.has_perm("zemauth.can_set_account_sales_representative")
        ):
            raise exc.AuthorizationError()

        if (
            "default_cs_representative" in form.cleaned_data
            and form.cleaned_data["default_cs_representative"] is not None
            and not user.has_perm("zemauth.can_set_account_cs_representative")
        ):
            raise exc.AuthorizationError()

        if (
            "ob_representative" in form.cleaned_data
            and form.cleaned_data["ob_representative"] is not None
            and not user.has_perm("zemauth.can_set_account_ob_representative")
        ):
            raise exc.AuthorizationError()

        if (
            "name" in form.cleaned_data
            and form.cleaned_data["name"] is not None
            and not user.has_perm("zemauth.can_modify_account_name")
        ):
            raise exc.AuthorizationError()

        if (
            "default_account_manager" in form.cleaned_data
            and form.cleaned_data["default_account_manager"] is not None
            and not user.has_perm("zemauth.can_modify_account_manager")
        ):
            raise exc.AuthorizationError()

    def get_validation_error_data(self, request, account):
        data = {}
        if not request.user.has_perm("zemauth.can_modify_allowed_sources"):
            return data

        data["allowed_sources"] = self.get_allowed_sources(
            account,
            request.user.has_perm("zemauth.can_see_all_available_sources"),
            [source.id for source in account.allowed_sources.all()],
        )
        return data

    def set_account(self, request, account, resource):
        if resource["name"]:
            account.name = resource["name"]
        if resource["currency"]:
            account.currency = resource["currency"]
        if resource["agency"]:
            if not request.user.has_perm("zemauth.can_set_agency_for_account"):
                raise exc.AuthorizationError()

            try:
                agency = models.Agency.objects.get(name=resource["agency"])
                account.agency = agency
                if not account.yahoo_account:
                    account.yahoo_account = agency.yahoo_account
            except models.Agency.DoesNotExist:
                agency = models.Agency.objects.create(
                    request,
                    name=resource["agency"],
                    sales_representative=resource["default_sales_representative"],
                    cs_representative=resource["default_cs_representative"],
                    ob_representative=resource["ob_representative"],
                )
                account.agency = agency

    def get_non_removable_sources(self, account, sources_to_be_removed):
        return list(
            models.AdGroupSource.objects.all()
            .filter(settings__state=constants.AdGroupSourceSettingsState.ACTIVE)
            .filter(ad_group__settings__state=constants.AdGroupSettingsState.ACTIVE)
            .filter(ad_group__campaign__account=account.id)
            .filter(source__in=sources_to_be_removed)
            .values_list("source_id", flat=True)
            .distinct()
        )

    def add_error_to_account_agency_form(self, form, to_be_removed):
        source_names = [source.name for source in models.Source.objects.filter(id__in=to_be_removed).order_by("id")]
        media_sources = ", ".join(source_names)
        if len(source_names) > 1:
            msg = "Can't save changes because media sources {} are still used on this account.".format(media_sources)
        else:
            msg = "Can't save changes because media source {} is still used on this account.".format(media_sources)

        form.add_error("allowed_sources", msg)

    def set_allowed_sources(self, settings, account, can_see_all_available_sources, account_agency_form):
        allowed_sources_dict = account_agency_form.cleaned_data.get("allowed_sources")

        if not allowed_sources_dict:
            return

        all_available_sources = self.get_all_media_sources(account, can_see_all_available_sources)
        current_allowed_sources = self.get_allowed_media_sources(account, can_see_all_available_sources)
        new_allowed_sources = self.filter_allowed_sources_dict(all_available_sources, allowed_sources_dict)

        new_allowed_sources_set = set(new_allowed_sources)
        current_allowed_sources_set = set(current_allowed_sources)

        to_be_removed = current_allowed_sources_set.difference(new_allowed_sources_set)
        to_be_added = new_allowed_sources_set.difference(current_allowed_sources_set)

        non_removable_sources = self.get_non_removable_sources(account, to_be_removed)
        if len(non_removable_sources) > 0:
            self.add_error_to_account_agency_form(account_agency_form, non_removable_sources)
            return

        changes_text = None
        if to_be_added or to_be_removed:
            changes_text = self.get_changes_text_for_media_sources(to_be_added, to_be_removed)
            account.allowed_sources.add(*list(to_be_added))
            account.allowed_sources.remove(*list(to_be_removed))
        return changes_text

    def get_or_create_facebook_account(self, account):
        try:
            facebook_account = account.facebookaccount
        except models.FacebookAccount.DoesNotExist:
            facebook_account = models.FacebookAccount.objects.create(
                account=account, status=constants.FacebookPageRequestType.EMPTY
            )
        return facebook_account

    def set_facebook_page(self, facebook_account, form):
        new_url = form.cleaned_data["facebook_page"]
        credentials = facebook_helper.get_credentials()
        facebook_helper.update_facebook_account(
            facebook_account, new_url, credentials["business_id"], credentials["access_token"]
        )

    def get_all_media_sources(self, account, can_see_all_available_sources):
        if account.agency and account.agency.allowed_sources.count() > 0:
            return list(account.agency.allowed_sources.all())
        qs_sources = models.Source.objects.all()
        if not can_see_all_available_sources:
            qs_sources = qs_sources.filter(released=True)

        return list(qs_sources)

    def get_allowed_media_sources(self, account, can_see_all_available_sources):
        qs_allowed_sources = account.allowed_sources.all()
        if not can_see_all_available_sources:
            qs_allowed_sources = qs_allowed_sources.filter(released=True)

        return list(qs_allowed_sources)

    def filter_allowed_sources_dict(self, sources, allowed_sources_dict):
        allowed_sources = []
        for source in sources:
            if source.id in allowed_sources_dict:
                value = allowed_sources_dict[source.id]
                if value.get("allowed", False):
                    allowed_sources.append(source)

        return allowed_sources

    def set_settings(self, settings, account, resource):
        settings.account = account
        if resource["name"]:
            settings.name = resource["name"]
        if resource["default_account_manager"]:
            settings.default_account_manager = resource["default_account_manager"]
        if resource["default_sales_representative"]:
            settings.default_sales_representative = resource["default_sales_representative"]
        if resource["default_cs_representative"]:
            settings.default_cs_representative = resource["default_cs_representative"]
        if resource["ob_representative"]:
            settings.ob_representative = resource["ob_representative"]

    def get_allowed_sources(self, account, include_unreleased_sources, allowed_sources_ids_list):
        allowed_sources_dict = {}

        all_sources_queryset = models.Source.objects.all()
        if account.agency and account.agency.allowed_sources.count() > 0:
            all_sources_queryset = account.agency.allowed_sources.all()
        if not include_unreleased_sources:
            all_sources_queryset = all_sources_queryset.filter(released=True)

        all_sources = list(all_sources_queryset)

        for source in all_sources:
            if source.id not in allowed_sources_ids_list and source.deprecated:
                continue

            source_settings = {"name": source.name, "released": source.released, "deprecated": source.deprecated}
            if source.id in allowed_sources_ids_list:
                source_settings["allowed"] = True
            allowed_sources_dict[source.id] = source_settings

        return allowed_sources_dict

    def add_facebook_account_to_result(self, result, account):
        try:
            result["facebook_page"] = account.facebookaccount.page_url
            result["facebook_status"] = models.constants.FacebookPageRequestType.get_text(
                account.facebookaccount.status
            )
        except models.FacebookAccount.DoesNotExist:
            result["facebook_status"] = models.constants.FacebookPageRequestType.get_text(
                models.constants.FacebookPageRequestType.EMPTY
            )

    def get_dict(self, request, settings, account):
        if not settings:
            return {}

        result = {"id": str(account.pk), "archived": settings.archived, "currency": account.currency}
        if request.user.has_perm("zemauth.can_modify_account_name"):
            result["name"] = account.name
        if request.user.has_perm("zemauth.can_modify_account_manager"):
            result["default_account_manager"] = (
                str(settings.default_account_manager.id) if settings.default_account_manager is not None else None
            )
        if request.user.has_perm("zemauth.can_set_account_sales_representative"):
            result["default_sales_representative"] = (
                str(settings.default_sales_representative.id)
                if settings.default_sales_representative is not None
                else None
            )
        if request.user.has_perm("zemauth.can_set_account_cs_representative"):
            result["default_cs_representative"] = (
                str(settings.default_cs_representative.id) if settings.default_cs_representative is not None else None
            )
        if request.user.has_perm("zemauth.can_set_account_ob_representative"):
            result["ob_representative"] = str(settings.ob_representative_id) if settings.ob_representative_id else None
        if request.user.has_perm("zemauth.can_modify_account_type"):
            result["account_type"] = settings.account_type
        if request.user.has_perm("zemauth.can_modify_allowed_sources"):
            result["allowed_sources"] = self.get_allowed_sources(
                account,
                request.user.has_perm("zemauth.can_see_all_available_sources"),
                [source.id for source in account.allowed_sources.all()],
            )
        if request.user.has_perm("zemauth.can_modify_facebook_page"):
            self.add_facebook_account_to_result(result, account)
        if request.user.has_perm("zemauth.can_set_agency_for_account"):
            if account.agency:
                result["agency"] = account.agency.name
            else:
                result["agency"] = ""
        if request.user.has_perm("zemauth.can_see_salesforce_url"):
            result["salesforce_url"] = settings.salesforce_url
        if request.user.has_perm("zemauth.can_set_auto_add_new_sources"):
            result["auto_add_new_sources"] = settings.auto_add_new_sources

        result["whitelist_publisher_groups"] = settings.whitelist_publisher_groups
        result["blacklist_publisher_groups"] = settings.blacklist_publisher_groups

        if request.user.has_perm("zemauth.can_set_frequency_capping"):
            result["frequency_capping"] = settings.frequency_capping

        return result

    def get_changes_text_for_media_sources(self, added_sources, removed_sources):
        sources_text_list = []
        if added_sources:
            added_sources_names = [source.name for source in added_sources]
            added_sources_text = "Added allowed media sources ({})".format(", ".join(added_sources_names))
            sources_text_list.append(added_sources_text)

        if removed_sources:
            removed_sources_names = [source.name for source in removed_sources]
            removed_sources_text = "Removed allowed media sources ({})".format(", ".join(removed_sources_names))
            sources_text_list.append(removed_sources_text)

        return ", ".join(sources_text_list)

    def get_account_managers(self, request, account, settings):
        users = helpers.get_users_for_manager(request.user, account, settings.default_account_manager)
        return self.format_user_list(users)

    def get_sales_representatives(self, account):
        users = ZemUser.objects.get_users_with_perm("campaign_settings_sales_rep").filter(is_active=True)
        if account.agency_id in SUBAGENCY_MAP:
            subagencies = models.Agency.objects.filter(pk__in=SUBAGENCY_MAP[account.agency_id])
            users &= ZemUser.objects.filter(agency__in=subagencies).distinct()
        return self.format_user_list(users)

    def get_cs_representatives(self, account):
        users = ZemUser.objects.get_users_with_perm("campaign_settings_cs_rep").filter(is_active=True)
        if account.agency_id in SUBAGENCY_MAP:
            subagencies = models.Agency.objects.filter(pk__in=SUBAGENCY_MAP[account.agency_id])
            users &= ZemUser.objects.filter(agency__in=subagencies).distinct()
        return self.format_user_list(users)

    def get_ob_representatives(self):
        users = ZemUser.objects.get_users_with_perm("can_be_ob_representative").filter(is_active=True)
        return self.format_user_list(users)

    def format_user_list(self, users):
        return [{"id": str(user.id), "name": helpers.get_user_full_name_or_email(user)} for user in users]


class AccountUsers(api_common.BaseApiView):
    def get(self, request, account_id):
        if not request.user.has_perm("zemauth.account_agency_access_permissions"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        agency_users = account.agency.users.all() if account.agency else []

        users = [self._get_user_dict(u) for u in account.users.all()]
        agency_managers = [self._get_user_dict(u, agency_managers=True) for u in agency_users]

        if request.user.has_perm("zemauth.can_see_agency_managers_under_access_permissions"):
            users = agency_managers + users

        return self.create_api_response(
            {"users": users, "agency_managers": agency_managers if account.agency else None}
        )

    def put(self, request, account_id):
        if not request.user.has_perm("zemauth.account_agency_access_permissions"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.UserForm(resource)
        is_valid = form.is_valid()

        # in case the user already exists and form contains
        # first name and last name, error is returned. In case
        # the form only contains email, user is added to the account.
        if form.cleaned_data.get("email") is None:
            self._raise_validation_error(form.errors)

        first_name = form.cleaned_data.get("first_name")
        last_name = form.cleaned_data.get("last_name")
        email = form.cleaned_data.get("email")

        try:

            user = ZemUser.objects.get(email__iexact=email)

            if (first_name == user.first_name and last_name == user.last_name) or (not first_name and not last_name):
                created = False
            else:
                self._raise_validation_error(
                    form.errors,
                    message='The user with e-mail {} is already registred as "{}". '
                    "Please contact technical support if you want to change the user's "
                    "name or leave first and last names blank if you just want to add "
                    "access to the account for this user.".format(user.email, user.get_full_name()),
                )
        except ZemUser.DoesNotExist:
            if not is_valid:
                self._raise_validation_error(form.errors)

            user = ZemUser.objects.create_user(email, first_name=first_name, last_name=last_name)
            self._add_user_to_groups(user)
            native_server.apply_create_user_hacks(user, account)
            email_helper.send_email_to_new_user(user, request, agency=account.agency)

            created = True

        # we check account for this user to prevent multiple additions
        if not len(account.users.filter(pk=user.pk)):
            account.users.add(user)

            changes_text = "Added user {} ({})".format(user.get_full_name(), user.email)

            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = changes_text
            new_settings.save(request, changes_text=changes_text)

        return self.create_api_response({"user": self._get_user_dict(user)}, status_code=201 if created else 200)

    def _add_user_to_groups(self, user):
        perm = authmodels.Permission.objects.get(codename="group_new_user_add")
        groups = authmodels.Group.objects.filter(permissions=perm)
        for group in groups:
            group.user_set.add(user)

    def _raise_validation_error(self, errors, message=None):
        raise exc.ValidationError(
            errors=dict(errors), pretty_message=message or "Please specify the user's first name, last name and email."
        )

    def delete(self, request, account_id, user_id):
        if not request.user.has_perm("zemauth.account_agency_access_permissions"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        remove_from_all_accounts = request.GET.get("remove_from_all_accounts")
        try:
            user = ZemUser.objects.get(pk=user_id)
        except ZemUser.DoesNotExist:
            raise exc.MissingDataError()

        with transaction.atomic():
            self._remove_user(request, account, user, remove_from_all_accounts=remove_from_all_accounts)

        return self.create_api_response({"user_id": user.id})

    def _remove_user(self, request, account, user, remove_from_all_accounts=False):
        self._remove_user_from_account(account, user, request.user)

        is_agency_manager = account.agency and account.agency.users.filter(pk=user.pk).exists()
        if account.agency and (is_agency_manager or remove_from_all_accounts):
            for other_account in account.agency.account_set.all().exclude(pk=account.pk):
                self._remove_user_from_account(other_account, user, request.user)

        if is_agency_manager:
            groups = authmodels.Group.objects.filter(
                permissions=authmodels.Permission.objects.get(codename="group_agency_manager_add")
            )
            user.groups.remove(*groups)

            account.agency.users.remove(user)
            changes_text = "Removed agency user {} ({})".format(user.get_full_name(), user.email)
            account.agency.write_history(changes_text, user=request.user)

    def _remove_user_from_account(self, account, removed_user, request_user):
        if len(account.users.filter(pk=removed_user.pk)):
            account.users.remove(removed_user)
            changes_text = "Removed user {} ({})".format(removed_user.get_full_name(), removed_user.email)
            account.write_history(changes_text, user=request_user)

    def _get_user_dict(self, user, agency_managers=False):
        return {
            "id": user.id,
            "name": user.get_full_name(),
            "email": user.email,
            "last_login": user.last_login and user.last_login.date(),
            "is_active": not user.last_login or user.last_login != user.date_joined,
            "is_agency_manager": agency_managers,
            "can_use_restapi": user.has_perm("zemauth.can_use_restapi"),
        }


class AccountUserAction(api_common.BaseApiView):
    ACTIVATE = "activate"
    PROMOTE = "promote"
    DOWNGRADE = "downgrade"
    ENABLE_API = "enable_api"

    def __init__(self):
        self.actions = {
            AccountUserAction.ACTIVATE: self._activate,
            AccountUserAction.PROMOTE: self._promote,
            AccountUserAction.DOWNGRADE: self._downgrade,
            AccountUserAction.ENABLE_API: self._enable_api,
        }
        self.permissions = {
            AccountUserAction.ACTIVATE: "zemauth.account_agency_access_permissions",
            AccountUserAction.PROMOTE: "zemauth.can_promote_agency_managers",
            AccountUserAction.DOWNGRADE: "zemauth.can_promote_agency_managers",
            AccountUserAction.ENABLE_API: "zemauth.can_manage_restapi_access",
        }

    def post(self, request, account_id, user_id, action):
        if action not in self.actions:
            raise Http404("Action does not exist")

        if not request.user.has_perm(self.permissions[action]):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)

        try:
            user = ZemUser.objects.get(pk=user_id)
        except ZemUser.DoesNotExist:
            raise exc.ValidationError(pretty_message="Cannot {action} nonexisting user.".format(action=action))
        if user not in account.users.all() and (not account.is_agency() or user not in account.agency.users.all()):
            raise exc.AuthorizationError()

        self.actions[action](request, user, account)

        return self.create_api_response()

    def _activate(self, request, user, account):
        email_helper.send_email_to_new_user(user, request)

        changes_text = "Resent activation mail {} ({})".format(user.get_full_name(), user.email)
        account.write_history(changes_text, user=request.user)

    def _promote(self, request, user, account):
        groups = self._get_agency_manager_groups()

        self._check_is_agency_account(account)
        self._check_if_already_agency_user(account, user)

        account.agency.users.add(user)
        account.users.remove(user)
        user.groups.add(*groups)

    def _downgrade(self, request, user, account):
        groups = self._get_agency_manager_groups()

        self._check_is_agency_account(account)

        account.agency.users.remove(user)
        account.users.add(user)
        user.groups.remove(*groups)

    def _enable_api(self, request, user, account):
        perm = authmodels.Permission.objects.get(codename="can_use_restapi")
        api_group = authmodels.Group.objects.get(permissions=perm)

        if api_group not in user.groups.all():
            user.groups.add(api_group)
            changes_text = "{} was granted REST API access".format(user.email)
            account.write_history(changes_text=changes_text)
            email_helper.send_restapi_access_enabled_notification(user)

    def _check_is_agency_account(self, account):
        if not account.is_agency():
            raise exc.ValidationError(pretty_message="Cannot promote user on account without agency.")

    def _check_if_already_agency_user(self, account, user):
        agency = helpers.get_user_agency(user)
        if agency and account.agency != agency:
            raise exc.ValidationError(pretty_message="Cannot promote user on more then one agency.")

    def _get_agency_manager_groups(self):
        perm = authmodels.Permission.objects.get(codename="group_agency_manager_add")
        return authmodels.Group.objects.filter(permissions=perm)


class CampaignContentInsights(api_common.BaseApiView):
    @db_for_reads.use_stats_read_replica()
    def get(self, request, campaign_id):
        if not request.user.has_perm("zemauth.can_view_campaign_content_insights_side_tab"):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        view_filter = helpers.ViewFilter(request)
        start_date = view_filter.start_date
        end_date = view_filter.end_date

        best_performer_rows, worst_performer_rows = content_insights_helper.fetch_campaign_content_ad_metrics(
            request.user, campaign, start_date, end_date
        )
        return self.create_api_response(
            {
                "summary": "Title",
                "metric": "CTR",
                "best_performer_rows": best_performer_rows,
                "worst_performer_rows": worst_performer_rows,
            }
        )


class History(api_common.BaseApiView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_view_new_history_backend"):
            raise exc.AuthorizationError()
        # in case somebody wants to fetch entire history disallow it for the
        # moment
        entity_filter = self._extract_entity_filter(request)
        if not set(entity_filter.keys()).intersection({"ad_group", "campaign", "account", "agency"}):
            raise exc.MissingDataError()
        order = self._extract_order(request)
        response = {"history": self.get_history(entity_filter, order=order)}
        return self.create_api_response(response)

    def _extract_entity_filter(self, request):
        entity_filter = {}
        ad_group_raw = request.GET.get("ad_group")
        if ad_group_raw:
            entity_filter["ad_group"] = helpers.get_ad_group(request.user, int(ad_group_raw))
        campaign_raw = request.GET.get("campaign")
        if campaign_raw:
            entity_filter["campaign"] = helpers.get_campaign(request.user, int(campaign_raw))
        account_raw = request.GET.get("account")
        if account_raw:
            entity_filter["account"] = helpers.get_account(request.user, int(account_raw))
        agency_raw = request.GET.get("agency")
        if agency_raw:
            entity_filter["agency"] = helpers.get_agency(request.user, int(agency_raw))
        level_raw = request.GET.get("level")
        if level_raw and int(level_raw) in constants.HistoryLevel.get_all():
            entity_filter["level"] = int(level_raw)
        return entity_filter

    def _extract_order(self, request):
        order = ["-created_dt"]
        order_raw = request.GET.get("order") or ""
        if re.match("[-]?(created_dt|created_by)", order_raw):
            order = [order_raw]
        return order

    def get_history(self, filters, order=["-created_dt"]):
        history_entries = models.History.objects.filter(**filters).order_by(*order).select_related("created_by")

        history = []
        for history_entry in history_entries:
            history.append(
                {
                    "datetime": history_entry.created_dt,
                    "changed_by": history_entry.get_changed_by_text(),
                    "changes_text": history_entry.changes_text,
                }
            )
        return history


class Agencies(api_common.BaseApiView):
    def get(self, request):
        if not request.user.has_perm("zemauth.can_filter_by_agency"):
            raise exc.AuthorizationError()

        agencies = list(models.Agency.objects.all().filter_by_user(request.user).values("id", "name"))
        return self.create_api_response(
            {"agencies": [{"id": str(agency["id"]), "name": agency["name"]} for agency in agencies]}
        )


class FacebookAccountStatus(api_common.BaseApiView):
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        credentials = facebook_helper.get_credentials()
        try:
            pages = facebook_helper.get_all_pages(credentials["business_id"], credentials["access_token"])
            if pages is None:
                raise exc.BaseError("Error while accessing facebook page api.")
            page_status = pages.get(account.facebookaccount.page_id)
            account_status = self._get_account_status(page_status)
        except models.FacebookAccount.DoesNotExist:
            account_status = models.constants.FacebookPageRequestType.EMPTY
        except exc.BaseError:
            account_status = models.constants.FacebookPageRequestType.ERROR

        account_status_as_string = models.constants.FacebookPageRequestType.get_text(account_status)
        return self.create_api_response({"status": account_status_as_string})

    @staticmethod
    def _get_account_status(page_status):
        if page_status is None:
            return models.constants.FacebookPageRequestType.EMPTY
        elif page_status == "CONFIRMED":
            return models.constants.FacebookPageRequestType.CONNECTED
        elif page_status == "PENDING":
            return models.constants.FacebookPageRequestType.PENDING
        else:
            return models.constants.FacebookPageRequestType.INVALID
