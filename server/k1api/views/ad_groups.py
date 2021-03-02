from django.conf import settings

import automation.campaignstop.service
import core.features.publisher_groups
import dash.constants
import dash.features.custom_flags
import dash.models
from utils import db_router
from utils import zlogging

from .base import K1APIView

logger = zlogging.getLogger(__name__)


EVENT_RETARGET_ADGROUP = "redirect_adgroup"
EVENT_CUSTOM_AUDIENCE = "aud"

BLOCKED_AGENCIES = (151, 165, 191)
BLOCKED_ACCOUNTS = (523,)


class AdGroupsView(K1APIView):
    """
    Returns a list of non-archived ad groups together with their current settings.

    Filterable by ad_group_ids, source_type and slug.
    """

    @db_router.use_read_replica()
    def get(self, request):
        limit = int(request.GET.get("limit", 1000000))
        marker = request.GET.get("marker")
        ad_group_ids = request.GET.get("ad_group_ids")
        source_types = request.GET.get("source_types")
        slugs = request.GET.get("source_slugs")
        only_active = request.GET.get("only_active") == "true"
        exclude_display = request.GET.get("exclude_display", "false").lower() == "true"

        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")
        if source_types:
            source_types = source_types.split(",")
        if slugs:
            slugs = slugs.split(",")

        ad_groups, campaigns_budgets_map, campaignstop_states = self._get_ad_groups(
            ad_group_ids, source_types, slugs, only_active, exclude_display, marker, limit
        )

        campaign_ids = set(ad_group.campaign_id for ad_group in ad_groups)
        campaign_goal_types = self._get_campaign_goal_types(list(campaign_ids))
        campaign_goals = self._get_campaign_goals(list(campaign_ids))

        all_custom_flags = {
            flag.id: flag.get_default_value() for flag in dash.features.custom_flags.CustomFlag.objects.all()
        }

        ad_group_dicts = []
        for ad_group in ad_groups:
            if ad_group.settings is None:
                logger.error("K1API - ad group settings are None")
                continue

            agency_settings = None
            agency_name = ""
            if ad_group.campaign.account.agency:
                agency_settings = ad_group.campaign.account.agency.settings
                agency_name = ad_group.campaign.account.agency.name

            blacklist = ad_group.settings.blacklist_publisher_groups
            whitelist = ad_group.settings.whitelist_publisher_groups

            # Cache ad_group on settings to avoid additional DB queries.
            ad_group = ad_group.settings.ad_group

            b1_autopilot_state = (
                dash.constants.B1AutopilotState.ACTIVE
                if ad_group.campaign.account.agency_uses_realtime_autopilot()
                and ad_group.settings.autopilot_state != dash.constants.AdGroupSettingsAutopilotState.INACTIVE
                else dash.constants.B1AutopilotState.INACTIVE
            )

            blacklist, whitelist = core.features.publisher_groups.concat_publisher_group_targeting(
                ad_group,
                ad_group.settings,
                ad_group.campaign,
                ad_group.campaign.settings,
                ad_group.campaign.account,
                ad_group.campaign.account.settings,
                ad_group.campaign.account.agency,
                agency_settings,
            )

            service_fee = None
            license_fee = None
            margin = None
            if ad_group.campaign_id in campaigns_budgets_map:
                service_fee = campaigns_budgets_map[ad_group.campaign_id].credit.service_fee
                license_fee = campaigns_budgets_map[ad_group.campaign_id].credit.license_fee
                margin = campaigns_budgets_map[ad_group.campaign_id].margin

            bid = ad_group.settings.get_external_bid(service_fee, license_fee, margin)

            b1_sources_group_daily_budget = ad_group.settings.get_external_b1_sources_group_daily_budget(
                service_fee, license_fee, margin
            )

            # FIXME: k1 doesn't update missing keys, find a better solution
            flags = {}
            flags.update(all_custom_flags)
            flags.update(ad_group.get_all_custom_flags())

            ad_group_dict = {
                "id": ad_group.id,
                "name": ad_group.name,
                "external_name": ad_group.get_external_name(),
                "start_date": self._get_start_date(ad_group.settings, campaignstop_states),
                "end_date": self._get_end_date(ad_group.settings, campaignstop_states),
                "time_zone": settings.DEFAULT_TIME_ZONE,
                "bidding_type": ad_group.bidding_type,
                "bid": format(bid, ".4f"),
                "autopilot_state": b1_autopilot_state,
                "brand_name": ad_group.settings.brand_name,
                "display_url": ad_group.settings.display_url,
                "tracking_codes": ad_group.settings.get_tracking_codes(),
                "enable_ga_tracking": ad_group.campaign.settings.enable_ga_tracking,
                "enable_adobe_tracking": ad_group.campaign.settings.enable_adobe_tracking,
                "adobe_tracking_param": ad_group.campaign.settings.adobe_tracking_param,
                "target_devices": ad_group.settings.target_devices,
                "target_os": ad_group.settings.target_os,
                "target_browsers": ad_group.settings.target_browsers,
                "exclusion_target_browsers": ad_group.settings.exclusion_target_browsers,
                "target_connection_types": ad_group.settings.target_connection_types,
                "target_placements": ad_group.settings.target_environments,  # TODO: plac: remove after k1 merge
                "target_environments": ad_group.settings.target_environments,
                "target_regions": ad_group.settings.target_regions,
                "exclusion_target_regions": ad_group.settings.exclusion_target_regions,
                "iab_category": ad_group.campaign.settings.iab_category,
                "campaign_language": ad_group.campaign.settings.language,
                "retargeting": self._get_retargeting(ad_group.settings),
                "demographic_targeting": ad_group.settings.bluekai_targeting,
                "interest_targeting": ad_group.settings.interest_targeting,
                "exclusion_interest_targeting": ad_group.settings.exclusion_interest_targeting,
                "language_targeting_enabled": ad_group.settings.language_targeting_enabled,
                "campaign_id": ad_group.campaign.id,
                "campaign_name": ad_group.campaign.name,
                "campaign_type": ad_group.campaign.type,
                "account_id": ad_group.campaign.account.id,
                "account_name": ad_group.campaign.account.name,
                "agency_id": ad_group.campaign.account.agency_id,
                "agency_name": agency_name,
                "goal_types": campaign_goal_types[ad_group.campaign.id],
                "goals": campaign_goals[ad_group.campaign.id],
                "dayparting": ad_group.settings.dayparting,
                "b1_sources_group": {
                    "enabled": ad_group.settings.b1_sources_group_enabled,
                    "daily_budget": b1_sources_group_daily_budget,
                    "state": ad_group.settings.b1_sources_group_state,
                },
                "whitelist_publisher_groups": whitelist,
                "blacklist_publisher_groups": blacklist,
                "delivery_type": ad_group.settings.delivery_type,
                "click_capping_daily_ad_group_max_clicks": ad_group.settings.click_capping_daily_ad_group_max_clicks,
                "click_capping_daily_click_budget": ad_group.settings.click_capping_daily_click_budget,
                "custom_flags": flags,
                "amplify_review": ad_group.amplify_review,
                "freqcap_account": ad_group.campaign.account.settings.frequency_capping,
                "freqcap_campaign": ad_group.campaign.settings.frequency_capping,
                "freqcap_adgroup": ad_group.settings.frequency_capping,
                "additional_data": ad_group.settings.additional_data,
            }

            ad_group_dicts.append(ad_group_dict)

        return self.response_ok(ad_group_dicts)

    @staticmethod
    def _get_retargeting(ad_group_settings):
        retargeting = []

        for retargeting_ad_group_id in ad_group_settings.retargeting_ad_groups:
            retargeting.append(
                {"event_type": EVENT_RETARGET_ADGROUP, "event_id": str(retargeting_ad_group_id), "exclusion": False}
            )

        for retargeting_ad_group_id in ad_group_settings.exclusion_retargeting_ad_groups:
            retargeting.append(
                {"event_type": EVENT_RETARGET_ADGROUP, "event_id": str(retargeting_ad_group_id), "exclusion": True}
            )

        for audience_id in ad_group_settings.audience_targeting:
            retargeting.append({"event_type": EVENT_CUSTOM_AUDIENCE, "event_id": str(audience_id), "exclusion": False})

        for audience_id in ad_group_settings.exclusion_audience_targeting:
            retargeting.append({"event_type": EVENT_CUSTOM_AUDIENCE, "event_id": str(audience_id), "exclusion": True})

        return retargeting

    @staticmethod
    def _get_start_date(ad_group_settings, campaignstop_states):
        campaign = ad_group_settings.ad_group.campaign
        min_allowed_start_date = campaignstop_states.get(campaign.id, {}).get("min_allowed_start_date")
        if min_allowed_start_date is None:
            return ad_group_settings.start_date

        if ad_group_settings.start_date is None:
            return min_allowed_start_date

        return max(ad_group_settings.start_date, min_allowed_start_date)

    @staticmethod
    def _get_end_date(ad_group_settings, campaignstop_states):
        if ad_group_settings.ad_group.id == settings.AD_LOOKUP_AD_GROUP_ID:
            return None
        if ad_group_settings.ad_group.campaign.account_id == settings.APT_ACCOUNT_ID:
            return None
        campaign = ad_group_settings.ad_group.campaign
        max_allowed_end_date = campaignstop_states.get(campaign.id, {}).get("max_allowed_end_date")
        if max_allowed_end_date is None:
            return ad_group_settings.end_date

        if ad_group_settings.end_date is None:
            return max_allowed_end_date

        return min(ad_group_settings.end_date, max_allowed_end_date)

    @staticmethod
    def _get_campaign_goal_types(campaign_ids):
        """
        returns a map campaign_id:[goal_type,...]
        the first element in the list is the type of the primary goal
        """
        campaign_goals = {cid: [] for cid in campaign_ids}
        for goal in dash.models.CampaignGoal.objects.filter(campaign__in=campaign_ids):
            campaign_goals[goal.campaign_id].append((goal.primary, goal.type))
        for cid in list(campaign_goals.keys()):
            campaign_goals[cid] = [tup[1] for tup in sorted(campaign_goals[cid], reverse=True)]
        return campaign_goals

    @staticmethod
    def _get_campaign_goals(campaign_ids):
        """
        returns a map campaign_id:[goals_dict,...]
        the first element in the list is the type of the primary goal
        """
        campaign_goals = {cid: [] for cid in campaign_ids}
        for goal in (
            dash.models.CampaignGoal.objects.filter(campaign__in=campaign_ids)
            .select_related("conversion_goal")
            .prefetch_related("values")
        ):
            campaign_goals[goal.campaign_id].append(goal)

        campaign_goals_dicts = {}
        for cid, goals in campaign_goals.items():
            sorted_goals = sorted(goals, key=lambda x: (x.primary, x.pk), reverse=True)
            campaign_goals_dicts[cid] = [goal.to_dict(with_values=True) for goal in sorted_goals]
        return campaign_goals_dicts

    @staticmethod
    def _get_ad_groups(ad_group_ids, source_types, slugs, only_active, exclude_display, marker, limit):
        ad_groups = dash.models.AdGroup.objects.all()

        if ad_group_ids:
            ad_groups = ad_groups.filter(pk__in=ad_group_ids)
        if marker:
            ad_groups = ad_groups.filter(pk__gt=int(marker))

        if source_types or slugs:
            ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__in=ad_groups).filter(
                source__deprecated=False
            )
            if source_types:
                ad_group_sources = ad_group_sources.filter(source__source_type__type__in=source_types)
            if slugs:
                ad_group_sources = ad_group_sources.filter(source__bidder_slug__in=slugs)
            ad_groups = ad_groups.filter(pk__in=ad_group_sources.values("ad_group_id"))

        if only_active:
            ad_groups = ad_groups.filter(settings__state=dash.constants.AdGroupSettingsState.ACTIVE)
        if exclude_display:
            ad_groups = ad_groups.exclude_display()

        ad_groups = ad_groups.exclude_archived()

        # apply pagination
        ad_groups = ad_groups.order_by("pk")[:limit]

        ad_groups = ad_groups.select_related(
            "settings", "campaign__settings", "campaign__account__settings", "campaign__account__agency__settings"
        )

        campaignstop_states = automation.campaignstop.get_campaignstop_states(
            set(ad_group.campaign for ad_group in ad_groups)
        )

        budgets = (
            dash.models.BudgetLineItem.objects.filter(
                campaign_id__in=set([ad_group.campaign_id for ad_group in ad_groups])
            )
            .filter_today()
            .distinct("campaign_id")
            .select_related("credit", "campaign")
        )
        campaigns_budgets_map = {budget.campaign_id: budget for budget in budgets}

        return ad_groups, campaigns_budgets_map, campaignstop_states
