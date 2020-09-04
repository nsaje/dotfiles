from decimal import Decimal

from django.db.models import Count
from django.db.models import F

import analytics.constants
import analytics.helpers
import analytics.statements
import dash.campaign_goals
import dash.constants
import dash.infobox_helpers
import dash.models
from utils import zlogging

logger = zlogging.getLogger(__name__)

CAMPAIGN_REPORT_HEADER = ("Account", "Campaign ID", "URL", "CS Rep", "Yesterday spend", "Daily Spend Cap", "Delivery")
AD_GROUP_REPORT_HEADER = (
    "Account",
    "Ad group ID",
    "URL",
    "CS Rep",
    "End date",
    "Yesterday spend",
    "Daily Spend Cap",
    "Delivery",
)
CAMPAIGN_URL = "https://one.zemanta.com/v2/analytics/campaign/{}"
AD_GROUP_URL = "https://one.zemanta.com/v2/analytics/adgroup/{}"

ENGAGEMENT_GOALS = (
    dash.constants.CampaignGoalKPI.TIME_ON_SITE,
    dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE,
    dash.constants.CampaignGoalKPI.PAGES_PER_SESSION,
    dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS,
    dash.constants.CampaignGoalKPI.CPV,
    dash.constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
    dash.constants.CampaignGoalKPI.CP_NEW_VISITOR,
    dash.constants.CampaignGoalKPI.CP_PAGE_VIEW,
    dash.constants.CampaignGoalKPI.CPCV,
)
DEFAULT_ACCOUNT_TYPES = (
    dash.constants.AccountType.PILOT,
    dash.constants.AccountType.ACTIVATED,
    dash.constants.AccountType.MANAGED,
)

UNBILLABLE_SEGMENT_PARTS = ("outbrain", "lr-", "lotame", "obs", "obi", "obl", "weborama")
MIN_B1_ACTIVE_SOURCES_FOR_INTEREST_TARGETING = 5


def check_campaign_delivery(campaign, campaign_stats, prev_campaign_stats):
    visits = campaign_stats.get("visits") or prev_campaign_stats.get("visits", 0)
    conversions = campaign_stats.get("conversions", 0)
    if not campaign.campaign_goals:
        logger.warning("Campaign has no primary goal set!", campaign=campaign.id)
        return
    primary_goal = campaign.campaign_goals[0]
    is_postclick_enabled = campaign.settings.enable_ga_tracking or campaign.settings.enable_adobe_tracking

    if campaign.settings.iab_category == dash.constants.IABCategory.IAB24:
        return analytics.constants.CampaignDeliveryStatus.IAB_UNDEFINED
    if primary_goal.type in ENGAGEMENT_GOALS:
        if not is_postclick_enabled:
            return analytics.constants.CampaignDeliveryStatus.MISSING_POSTCLICK_SETUP
        if visits <= 0:
            return analytics.constants.CampaignDeliveryStatus.MISSING_POSTCLICK_STATS
    if primary_goal.type == dash.constants.CampaignGoalKPI.CPA and not conversions:
        return analytics.constants.CampaignDeliveryStatus.CPA_NO_CONVERSIONS
    if not campaign.ad_groups_active:
        return analytics.constants.CampaignDeliveryStatus.NO_ACTIVE_AD_GROUPS
    if campaign.ending_budgets:
        return analytics.constants.CampaignDeliveryStatus.CAMPAIGN_WITH_ENDING_BUDGET
    return analytics.constants.CampaignDeliveryStatus.OK


def check_ad_group_delivery(ad_group, approved_ad_sources_count):
    rtb_as_1_mvp_enabled = ad_group.settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE
    if not ad_group.content_ads:
        return analytics.constants.AdGroupDeliveryStatus.MISSING_ADS
    if not approved_ad_sources_count:
        return analytics.constants.AdGroupDeliveryStatus.NO_ADS_APPROVED
    if not ad_group.sources_b1_active and not ad_group.sources_api_active:
        return analytics.constants.AdGroupDeliveryStatus.NO_ACTIVE_SOURCES
    if ad_group.settings.b1_sources_group_enabled and rtb_as_1_mvp_enabled and not ad_group.sources_b1_active:
        return analytics.constants.AdGroupDeliveryStatus.RTB_AS_1_NO_SOURCES
    if ad_group.settings.whitelist_publisher_groups:
        if ad_group.settings.interest_targeting:
            return analytics.constants.AdGroupDeliveryStatus.WHITELIST_AND_INTERESTS
        if ad_group.settings.bluekai_targeting:
            return analytics.constants.AdGroupDeliveryStatus.WHITELIST_AND_DATA
    if (
        not ad_group.sources_api_active
        and ad_group.settings.interest_targeting
        and len(ad_group.sources_b1_active) <= MIN_B1_ACTIVE_SOURCES_FOR_INTEREST_TARGETING
    ):
        return analytics.constants.AdGroupDeliveryStatus.TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING
    if len(ad_group.content_ads_inactive) == len(ad_group.content_ads):
        return analytics.constants.AdGroupDeliveryStatus.NO_ACTIVE_ADS
    if ad_group.settings.interest_targeting and ad_group.settings.bluekai_targeting:
        return analytics.constants.AdGroupDeliveryStatus.INTEREST_TARGETING_AND_BLUEKAI
    return analytics.constants.AdGroupDeliveryStatus.OK


def _prepare_campaign_data(running_campaigns, campaign_stats, prev_campaign_stats, skip_ok=True):
    campaign_data = []
    for campaign in running_campaigns:
        delivery = check_campaign_delivery(
            campaign, campaign_stats.get(campaign.id, {}), prev_campaign_stats.get(campaign.id, {})
        )
        if skip_ok and delivery == "ok":
            continue
        cap = Decimal(dash.infobox_helpers.calculate_daily_campaign_cap(campaign))
        spend = campaign_stats.get(campaign.id, {}).get("media", Decimal(0)) + campaign_stats.get(campaign.id, {}).get(
            "data", Decimal(0)
        )
        campaign_data.append(
            (
                "{}".format(campaign.account.get_long_name()),
                campaign.id,
                CAMPAIGN_URL.format(campaign.id),
                campaign.account.settings.default_cs_representative,
                spend,
                cap,
                delivery,
                campaign.get_all_custom_flags().get("z1_stop_delivery_monitoring", False),
            )
        )
    return campaign_data


def _prepare_ad_group_data(running_ad_groups, ad_group_stats, skip_ok=True):
    ad_group_data = []
    ad_group_count_content_ad_sources = {
        ads["ad_group"]: ads["count_content_ad_sources"]
        for ads in dash.models.ContentAdSource.objects.filter(
            submission_status=dash.constants.ContentAdSubmissionStatus.APPROVED,
            content_ad__ad_group__in=[i.id for i in running_ad_groups],
        )
        .values(ad_group=F("content_ad__ad_group_id"))
        .annotate(count_content_ad_sources=Count("id"))
    }

    for ad_group in running_ad_groups:
        delivery = check_ad_group_delivery(ad_group, ad_group_count_content_ad_sources.get(ad_group.id, 0))
        if skip_ok and delivery == "ok":
            continue
        cap = Decimal(dash.infobox_helpers.calculate_daily_ad_group_cap(ad_group))
        spend = ad_group_stats.get(ad_group.id, {}).get("media", Decimal(0)) + ad_group_stats.get(ad_group.id, {}).get(
            "data", Decimal(0)
        )
        ad_group_data.append(
            (
                "{}".format(ad_group.campaign.account.get_long_name()),
                ad_group.id,
                AD_GROUP_URL.format(ad_group.id),
                ad_group.campaign.account.settings.default_cs_representative,
                ad_group.settings.end_date or "none",
                spend,
                cap,
                delivery,
                ad_group.get_all_custom_flags().get("z1_stop_delivery_monitoring", False),
            )
        )
    return ad_group_data
