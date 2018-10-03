import datetime
from decimal import Decimal

import core.features.bcm
import core.models
import dash.constants
import dash.campaign_goals
import utils.csv_utils
import analytics.statements
import analytics.helpers
import analytics.projections
import analytics.constants
import dash.infobox_helpers

CAMPAIGN_REPORT_HEADER = ("Campaign", "Campaign ID", "URL", "CS Rep", "Yesterday spend", "Daily Spend Cap", "Delivery")
AD_GROUP_REPORT_HEADER = (
    "Ad group",
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

UNBILLABLE_SEGMENT_PARTS = ("outbrain", "lr-", "lotame", "obs", "obi", "obl")
HIGH_PACING_THRESHOLD = Decimal("200.0")
LOW_PACING_THRESHOLD = Decimal("50.0")
MIN_B1_ACTIVE_SOURCES_FOR_INTEREST_TARGETING = 5

IGNORED_VIDEO_COST_AD_GROUPS = (9709, 26439, 21383, 26442, 21385, 33364, 33360, 26438, 26470, 13224)


def generate_delivery_reports(account_types=[], skip_ok=True, check_pacing=True, generate_csv=True):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(1)

    # Filter ad groups that are running today and were running tomorrow
    valid_accounts = (
        core.models.account.Account.objects.all()
        .filter_by_account_types(account_types or DEFAULT_ACCOUNT_TYPES)
        .values_list("pk", flat=True)
    )
    running_ad_groups = (
        core.models.ad_group.AdGroup.objects.filter(campaign__account__id__in=valid_accounts)
        .filter_running()
        .filter_running(yesterday)
        .select_related("campaign", "campaign__account", "campaign__account__agency")
    )
    running_campaigns = core.models.campaign.Campaign.objects.filter(
        pk__in=set(running_ad_groups.values_list("campaign_id", flat=True))
    ).select_related("account", "account__agency")
    running_accounts = core.models.account.Account.objects.filter(pk__in=set(c.account_id for c in running_campaigns))

    account_settings_map = {
        sett.account_id: sett for sett in core.models.settings.AccountSettings.objects.all().group_current_settings()
    }
    campaign_settings_map = {
        sett.campaign_id: sett for sett in core.models.settings.CampaignSettings.objects.all().group_current_settings()
    }
    ad_group_settings_map = {
        sett.ad_group_id: sett for sett in core.models.settings.AdGroupSettings.objects.all().group_current_settings()
    }

    campaign_stats = analytics.helpers.get_stats_multiple(yesterday, campaign=running_campaigns)

    prev_campaign_stats = analytics.helpers.get_stats_multiple(
        yesterday - datetime.timedelta(1), campaign=running_campaigns
    )
    ad_group_stats = analytics.helpers.get_stats_multiple(yesterday, ad_group=running_ad_groups)

    campaign_projections = analytics.projections.CurrentMonthBudgetProjections(
        "campaign", date=today, accounts=running_accounts
    )

    campaign_data = _prepare_campaign_data(
        running_campaigns,
        campaign_settings_map,
        account_settings_map,
        campaign_stats,
        prev_campaign_stats,
        campaign_projections,
        skip_ok=skip_ok,
        check_pacing=check_pacing,
    )

    ad_group_data = _prepare_ad_group_data(
        running_ad_groups, ad_group_settings_map, ad_group_stats, account_settings_map, skip_ok=skip_ok
    )

    return {
        "campaign": analytics.statements.generate_csv(
            "csr/{}-campaign.csv".format(today),
            utils.csv_utils.tuplelist_to_csv([CAMPAIGN_REPORT_HEADER] + campaign_data),
        )
        if generate_csv
        else campaign_data,
        "ad_group": analytics.statements.generate_csv(
            "csr/{}-ad-group.csv".format(today),
            utils.csv_utils.tuplelist_to_csv([AD_GROUP_REPORT_HEADER] + ad_group_data),
        )
        if generate_csv
        else ad_group_data,
    }


def check_campaign_delivery(
    campaign, campaign_settings, campaign_stats, prev_campaign_stats, projections, check_pacing=True
):
    visits = campaign_stats.get("visits") or prev_campaign_stats.get("visits") or 0
    budgets = core.features.bcm.budget_line_item.BudgetLineItem.objects.filter(campaign=campaign).filter_active()
    active_amount = sum(b.allocated_amount() for b in budgets)
    primary_goal = dash.campaign_goals.get_primary_campaign_goal(campaign)
    is_postclick_enabled = campaign_settings.enable_ga_tracking or campaign_settings.enable_adobe_tracking
    if not primary_goal:
        return analytics.constants.CampaignDeliveryStatus.NO_GOAL
    if campaign_settings.iab_category == dash.constants.IABCategory.IAB24:
        return analytics.constants.CampaignDeliveryStatus.IAB_UNDEFINED
    if active_amount <= 0:
        return analytics.constants.CampaignDeliveryStatus.NO_BUDGET
    if primary_goal.type in ENGAGEMENT_GOALS:
        if not is_postclick_enabled:
            return analytics.constants.CampaignDeliveryStatus.MISSING_POSTCLICK_SETUP
        if visits <= 0:
            return analytics.constants.CampaignDeliveryStatus.MISSING_POSTCLICK_STATS
    if check_pacing and projections["pacing"] is not None:
        if projections["pacing"] < LOW_PACING_THRESHOLD:
            return analytics.constants.CampaignDeliveryStatus.LOW_PACING
        if projections["pacing"] > HIGH_PACING_THRESHOLD:
            return analytics.constants.CampaignDeliveryStatus.HIGH_PACING
    active_ad_groups = core.models.ad_group.AdGroup.objects.filter(campaign=campaign).filter_running()
    if not active_ad_groups.count() and active_amount:
        return analytics.constants.CampaignDeliveryStatus.NO_ACTIVE_AD_GROUPS
    return analytics.constants.CampaignDeliveryStatus.OK


def check_ad_group_delivery(ad_group, ad_group_settings, ad_group_stats):
    media = ad_group_stats.get("media")
    data = ad_group_stats.get("data")
    content_ads = core.models.content_ad.ContentAd.objects.filter(ad_group=ad_group)
    active_sources = core.models.ad_group_source.AdGroupSource.objects.filter(ad_group=ad_group).filter_active()
    b1_active_sources = active_sources.filter(source__source_type__type=dash.constants.SourceType.B1)
    api_active_sources = active_sources.exclude(source__source_type__type=dash.constants.SourceType.B1)
    approved_ad_sources = core.models.content_ad_source.ContentAdSource.objects.filter(
        content_ad__ad_group_id=ad_group.pk, submission_status=dash.constants.ContentAdSubmissionStatus.APPROVED
    )
    api_active_sources_count = api_active_sources.count()
    b1_active_sources_count = b1_active_sources.count()
    rtb_as_1_mvp_enabled = ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE
    if not content_ads.count():
        return analytics.constants.AdGroupDeliveryStatus.MISSING_ADS
    if not approved_ad_sources.count():
        return analytics.constants.AdGroupDeliveryStatus.NO_ADS_APPROVED
    if not active_sources.count():
        return analytics.constants.AdGroupDeliveryStatus.NO_ACTIVE_SOURCES
    if ad_group_settings.b1_sources_group_enabled and rtb_as_1_mvp_enabled and not b1_active_sources_count:
        return analytics.constants.AdGroupDeliveryStatus.RTB_AS_1_NO_SOURCES
    if ad_group_settings.whitelist_publisher_groups:
        if ad_group_settings.interest_targeting:
            return analytics.constants.AdGroupDeliveryStatus.WHITELIST_AND_INTERESTS
        if ad_group_settings.bluekai_targeting:
            return analytics.constants.AdGroupDeliveryStatus.WHITELIST_AND_DATA
    if (
        not api_active_sources_count
        and ad_group_settings.interest_targeting
        and b1_active_sources_count <= MIN_B1_ACTIVE_SOURCES_FOR_INTEREST_TARGETING
    ):
        return analytics.constants.AdGroupDeliveryStatus.TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING
    if (
        _extract_unbillable_data_segments(ad_group_settings.bluekai_targeting)
        and b1_active_sources_count
        and media
        and not data
    ):
        return analytics.constants.AdGroupDeliveryStatus.MISSING_DATA_COST
    is_video_spending = _has_video_assets(content_ads) and media
    if is_video_spending and not data and ad_group.pk not in IGNORED_VIDEO_COST_AD_GROUPS:
        return analytics.constants.AdGroupDeliveryStatus.MISSING_VIDEO_COST
    return analytics.constants.AdGroupDeliveryStatus.OK


def _prepare_campaign_data(
    running_campaigns,
    campaign_settings_map,
    account_settings_map,
    campaign_stats,
    prev_campaign_stats,
    campaign_projections,
    skip_ok=True,
    check_pacing=True,
):
    campaign_data = []
    for campaign in running_campaigns:
        campaign_settings = campaign_settings_map[campaign.pk]
        delivery = check_campaign_delivery(
            campaign,
            campaign_settings,
            campaign_stats.get(campaign.pk, {}),
            prev_campaign_stats.get(campaign.pk, {}),
            campaign_projections.row(campaign.pk),
            check_pacing=check_pacing,
        )
        if skip_ok and delivery == "ok":
            continue
        cap = Decimal(dash.infobox_helpers.calculate_daily_campaign_cap(campaign))
        spend = campaign_stats.get(campaign.pk, {}).get("media", Decimal(0)) + campaign_stats.get(campaign.pk, {}).get(
            "data", Decimal(0)
        )
        campaign_data.append(
            (
                campaign.get_long_name(),
                campaign.pk,
                CAMPAIGN_URL.format(campaign.pk),
                account_settings_map[campaign.account_id].default_cs_representative,
                spend,
                cap,
                delivery,
            )
        )
    return campaign_data


def _prepare_ad_group_data(
    running_ad_groups, ad_group_settings_map, ad_group_stats, account_settings_map, skip_ok=True
):
    ad_group_data = []
    for ad_group in running_ad_groups:
        ad_group_settings = ad_group_settings_map[ad_group.pk]
        delivery = check_ad_group_delivery(ad_group, ad_group_settings, ad_group_stats.get(ad_group.pk, {}))
        if skip_ok and delivery == "ok":
            continue
        cap = Decimal(dash.infobox_helpers.calculate_daily_ad_group_cap(ad_group))
        spend = ad_group_stats.get(ad_group.pk, {}).get("media", Decimal(0)) + ad_group_stats.get(ad_group.pk, {}).get(
            "data", Decimal(0)
        )
        ad_group_data.append(
            (
                "{}, {}".format(ad_group.campaign.get_long_name(), ad_group.name),
                ad_group.pk,
                AD_GROUP_URL.format(ad_group.pk),
                account_settings_map[ad_group.campaign.account_id].default_cs_representative,
                ad_group_settings.end_date or "none",
                spend,
                cap,
                delivery,
            )
        )
    return ad_group_data


def _extract_unbillable_data_segments(targeting_exp):
    segments = set()
    if not targeting_exp:
        return segments
    for part in targeting_exp:
        if type(part) == list:
            filtered_part = _extract_unbillable_data_segments(part)
            if filtered_part:
                segments |= filtered_part
            continue
        if part.lower() in ("and", "or", "not"):
            continue
        if not any(
            unbillable_segment_type
            for unbillable_segment_type in UNBILLABLE_SEGMENT_PARTS
            if unbillable_segment_type in part
        ):
            segments.add(part)
            continue
    return segments


def _has_video_assets(content_ads):
    for ad in content_ads:
        if ad.video_asset:
            return True
    return False
