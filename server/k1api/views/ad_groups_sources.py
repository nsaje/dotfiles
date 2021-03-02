from django.conf import settings

import automation.campaignstop.service
import dash.constants
import dash.features.custom_flags
import dash.models
from dash import constants
from utils import converters
from utils import db_router
from utils import url_helper
from utils import zlogging

from .base import K1APIView

logger = zlogging.getLogger(__name__)


class AdGroupSourcesView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        """
        Returns a list of non-archived ad group sources together with their current source settings.

        Filterable by ad_group_ids, source_type and slug.
        """
        ad_group_ids = request.GET.get("ad_group_ids")
        source_types = request.GET.get("source_types")
        slugs = request.GET.get("source_slugs")
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")
        if source_types:
            source_types = source_types.split(",")
        if slugs:
            slugs = slugs.split(",")

        # get ad groups we're interested in
        ad_groups = (
            dash.models.AdGroup.objects.all().exclude_archived().select_related("settings", "campaign__account__agency")
        )
        if ad_group_ids:
            ad_groups = ad_groups.filter(id__in=ad_group_ids)
        ad_group_map = {ad_group.id: ad_group for ad_group in ad_groups}

        campaigns = set(ad_group.campaign for ad_group in ad_groups)
        campaignstop_map = automation.campaignstop.get_campaignstop_states(campaigns)

        ad_group_sources = (
            dash.models.AdGroupSource.objects.all()
            .filter(ad_group__in=ad_groups)
            .filter(source__deprecated=False)
            .select_related("settings", "source__source_type")
        )

        # filter which sources we want
        if source_types:
            ad_group_sources = ad_group_sources.filter(source__source_type__type__in=source_types)
        if slugs:
            ad_group_sources = ad_group_sources.filter(source__bidder_slug__in=slugs)

        # build a map of today's campaign budgets
        budgets = (
            dash.models.BudgetLineItem.objects.all().filter_today().distinct("campaign_id").select_related("credit")
        )
        if ad_group_ids:
            budgets = budgets.filter(campaign__in=campaigns)
        campaigns_budgets_map = {budget.campaign_id: budget for budget in budgets}

        # build the list of objects
        ad_group_source_dicts = []
        for ad_group_source in ad_group_sources:
            ad_group = ad_group_map[ad_group_source.ad_group_id]
            allowed_to_run = campaignstop_map[ad_group.campaign.id]["allowed_to_run"]
            if self._is_ad_group_source_enabled(ad_group, ad_group_source, allowed_to_run):
                source_state = constants.AdGroupSettingsState.ACTIVE
            else:
                source_state = constants.AdGroupSettingsState.INACTIVE
            # NOTE(nsaje): taking adgroupsource.blockers into account here is not necessary, since the
            # executor should know when it has a blocking action pending

            tracking_code = url_helper.combine_tracking_codes(ad_group.settings.get_tracking_codes(), "")

            service_fee = None
            license_fee = None
            margin = None
            if ad_group.campaign_id in campaigns_budgets_map:
                service_fee = campaigns_budgets_map[ad_group.campaign_id].credit.service_fee
                license_fee = campaigns_budgets_map[ad_group.campaign_id].credit.license_fee
                margin = campaigns_budgets_map[ad_group.campaign_id].margin

            # TODO: RTAP: remove when everyone uses realtime autopilot
            daily_budget_cc = ad_group_source.settings.get_external_daily_budget_cc(service_fee, license_fee, margin)

            if ad_group.is_blocked_by_custom_flag() or ad_group.is_disabled:
                source_state = constants.AdGroupSettingsState.INACTIVE
            source = {
                "ad_group_id": ad_group_source.ad_group_id,
                "source_id": ad_group_source.source.id,
                "slug": ad_group_source.source.bidder_slug,
                "source_campaign_key": ad_group_source.source_campaign_key,
                "tracking_code": tracking_code,
                "state": source_state,
                "daily_budget_cc": format(daily_budget_cc, ".4f"),
                "blockers": ad_group_source.blockers,
            }
            if ad_group_source.ad_review_only:
                source["ad_review_only"] = True
            ad_group_source_dicts.append(source)

        return self.response_ok(ad_group_source_dicts)

    def _is_ad_group_source_enabled(self, ad_group, ad_group_source, allowed_to_run):
        if ad_group.id == settings.AD_LOOKUP_AD_GROUP_ID:
            return True

        # Ensure APT demand is always enabled on APT supply and nowhere else
        if ad_group.campaign.account_id == settings.APT_ACCOUNT_ID:
            if ad_group_source.source_id in settings.APT_SOURCE_IDS:
                return True
            return False

        if not allowed_to_run:
            return False

        if ad_group.settings.state != constants.AdGroupSettingsState.ACTIVE:
            return False

        if ad_group_source.settings.state != constants.AdGroupSourceSettingsState.ACTIVE:
            return False

        if (
            ad_group_source.source.source_type.type == constants.SourceType.B1
            and ad_group.settings.b1_sources_group_enabled
            and ad_group.settings.b1_sources_group_state != constants.AdGroupSourceSettingsState.ACTIVE
        ):
            return False

        return True

    def put(self, request):
        """
        Updates ad group source settings.
        """
        ad_group_id = request.GET.get("ad_group_id")
        bidder_slug = request.GET.get("source_slug")
        data = request.data

        if not (ad_group_id and bidder_slug and data):
            return self.response_error("Must provide ad_group_id, source_slug and conf", status=404)

        try:
            ad_group_source = dash.models.AdGroupSource.objects.get(
                ad_group__id=ad_group_id, source__bidder_slug=bidder_slug
            )
        except dash.models.AdGroupSource.DoesNotExist:
            return self.response_error(
                "No AdGroupSource exists for ad_group_id: %s with bidder_slug %s" % (ad_group_id, bidder_slug),
                status=404,
            )
        ad_group_source_settings = ad_group_source.get_current_settings()
        new_settings = ad_group_source_settings.copy_settings()

        settings_changed = False
        for key, val in list(data.items()):
            if key == "cpc_cc":
                logger.error("K1API - unexpected update of ad group source cpc_cc")
                new_settings.cpc_cc = converters.cc_to_decimal(val)
                settings_changed = True
            elif key == "daily_budget_cc":
                logger.error("K1API - unexpected update of ad group source daily_budget_cc")
                new_settings.daily_budget_cc = converters.cc_to_decimal(val)
                settings_changed = True
            elif key == "state":
                new_settings.state = val
                settings_changed = True
            elif key == "source_campaign_key":
                if ad_group_source.source_campaign_key and val != ad_group_source.source_campaign_key:
                    return self.response_error("Cannot change existing source_campaign_key", status=400)
                ad_group_source.source_campaign_key = val
                ad_group_source.save()
            else:
                return self.response_error("Invalid setting!", status=400)

        if settings_changed:
            new_settings.save(None, system_user=dash.constants.SystemUserType.K1_USER)
        return self.response_ok([])


class AdGroupSourceBlockersView(K1APIView):
    def put(self, request):
        """
        Add/remove a blocker of an ad group source.
        """
        ad_group_id = request.GET.get("ad_group_id")
        blockers_update = request.data
        response = {}

        ad_group_sources = dash.models.AdGroupSource.objects.only("blockers", "source").filter(
            ad_group_id=ad_group_id, source__bidder_slug__in=blockers_update.keys()
        )

        for ags in ad_group_sources:
            blockers = blockers_update.get(ags.source.bidder_slug, {})
            changes = 0
            for key, value in list(blockers.items()):
                if not (isinstance(key, str) and (isinstance(value, str) or value is None)):
                    return self.response_error(
                        "Bad input: blocker key should be a string and value should be either a string or None",
                        status=400,
                    )
                if value and value != ags.blockers.get(key):
                    ags.blockers[key] = value
                    changes += 1
                if not value and key in ags.blockers:
                    del ags.blockers[key]
                    changes += 1

            if changes:
                ags.save()

            response[ags.source.bidder_slug] = ags.blockers

        return self.response_ok(response)
