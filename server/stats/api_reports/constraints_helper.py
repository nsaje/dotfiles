import core.features.publisher_groups
import dash.constants
import dash.models
import stats.constants
import stats.constraints_helper
from zemauth.features.entity_permission import Permission


def _intersection(base_collection, qs_ids):
    if not base_collection:
        return set(qs_ids)

    return set(base_collection) & set(qs_ids)


def _distinct_key(base_qs, key):
    return base_qs.order_by(key).distinct(key).values_list(key, flat=True)


# at this point permissions are checked
def prepare_constraints(
    user,
    breakdown,
    start_date,
    end_date,
    filtered_sources,
    show_archived,
    account_ids=None,
    campaign_ids=None,
    ad_group_ids=None,
    content_ad_ids=None,
    filtered_agencies=None,
    filtered_account_types=None,
    filtered_businesses=None,
    only_used_sources=False,
    show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
):
    # determine the basic structure that is allowed
    allowed_accounts = (
        dash.models.Account.objects.all()
        .filter_by_agencies(filtered_agencies)
        .filter_by_account_types(filtered_account_types)
        .filter_by_business(filtered_businesses)
    )

    allowed_campaigns = dash.models.Campaign.objects.all()
    allowed_ad_groups = dash.models.AdGroup.objects.all()
    allowed_content_ads = dash.models.ContentAd.objects.all()

    constrain_content_ads = stats.constants.CONTENT_AD in breakdown
    constrain_ad_group = constrain_content_ads or stats.constants.AD_GROUP in breakdown
    constrain_campaigns = constrain_ad_group or stats.constants.CAMPAIGN in breakdown
    constrain_accounts = constrain_campaigns or stats.constants.ACCOUNT in breakdown

    ad_group = None

    # filter by user and sources only on level that is restricted
    if content_ad_ids:
        allowed_content_ads = allowed_content_ads.filter_by_entity_permission(user, Permission.READ)
    elif ad_group_ids:
        allowed_ad_groups = allowed_ad_groups.filter_by_entity_permission(user, Permission.READ)
    elif campaign_ids:
        allowed_campaigns = allowed_campaigns.filter_by_entity_permission(user, Permission.READ).filter_by_sources(
            filtered_sources
        )
    else:
        allowed_accounts = allowed_accounts.filter_by_entity_permission(user, Permission.READ).filter_by_sources(
            filtered_sources
        )

        # limit by ids
    ad_group_sources = None
    if content_ad_ids:
        allowed_content_ads = allowed_content_ads.filter(pk__in=content_ad_ids)
        ad_group_ids = _intersection(ad_group_ids, _distinct_key(allowed_content_ads, "ad_group_id"))

        constrain_content_ads = True
        constrain_ad_group = True
        constrain_campaigns = True
        constrain_accounts = True

    if ad_group_ids:
        allowed_ad_groups = allowed_ad_groups.filter(pk__in=ad_group_ids)
        if not content_ad_ids:
            allowed_content_ads = allowed_content_ads.filter(ad_group__in=allowed_ad_groups)
        campaign_ids = _intersection(campaign_ids, _distinct_key(allowed_ad_groups, "campaign_id"))
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__in=allowed_ad_groups)

        if len(ad_group_ids) == 1:
            ad_group = allowed_ad_groups.first()

        constrain_ad_group = True
        constrain_campaigns = True
        constrain_accounts = True

    if campaign_ids:
        allowed_campaigns = allowed_campaigns.filter(pk__in=campaign_ids)
        if not ad_group_ids:
            allowed_ad_groups = allowed_ad_groups.filter(campaign__in=allowed_campaigns)
            if not content_ad_ids:
                allowed_content_ads = allowed_content_ads.filter(ad_group__in=allowed_ad_groups)
        account_ids = _intersection(account_ids, _distinct_key(allowed_campaigns, "account_id"))
        if ad_group_sources is None:
            ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__campaign__in=allowed_campaigns)

        constrain_campaigns = True
        constrain_accounts = True

    if account_ids:
        allowed_accounts = allowed_accounts.filter(pk__in=account_ids)
        constrain_accounts = True

    if not campaign_ids:
        allowed_campaigns = allowed_campaigns.filter(account__in=allowed_accounts)
        if not ad_group_ids:
            allowed_ad_groups = allowed_ad_groups.filter(campaign__in=allowed_campaigns)
            if not content_ad_ids:
                allowed_content_ads = allowed_content_ads.filter(ad_group__in=allowed_ad_groups)

    if ad_group_sources is None:
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group__campaign__account__in=allowed_accounts)

    if only_used_sources:
        filtered_sources = stats.constraints_helper.narrow_filtered_sources(filtered_sources, ad_group_sources)

    # apply show_archived (at the end because higher up we need all users's ad groups in the queryset)
    allowed_content_ads = allowed_content_ads.exclude_archived(show_archived)
    allowed_ad_groups = allowed_ad_groups.exclude_archived(show_archived)
    allowed_campaigns = allowed_campaigns.exclude_archived(show_archived)
    allowed_accounts = allowed_accounts.exclude_archived(show_archived)

    include_publisher_groups = stats.constants.contains_dimension(
        breakdown, [stats.constants.PUBLISHER, stats.constants.PLACEMENT]
    )
    blacklisted_entries, whitelisted_entries, pg_targeting = (
        _prepare_publisher_groups_constraints(
            allowed_accounts,
            allowed_campaigns,
            allowed_ad_groups,
            constrain_accounts,
            constrain_campaigns,
            constrain_ad_group,
            filtered_sources,
        )
        if include_publisher_groups
        else (None, None, None)
    )

    constraints = {
        "show_archived": show_archived,
        "ad_group": ad_group,
        "allowed_content_ads": allowed_content_ads if constrain_content_ads else None,
        "allowed_ad_groups": allowed_ad_groups if constrain_ad_group else None,
        "allowed_campaigns": allowed_campaigns if constrain_campaigns else None,
        "allowed_accounts": allowed_accounts,
        "publisher_blacklist": blacklisted_entries if include_publisher_groups else None,
        "publisher_whitelist": whitelisted_entries if include_publisher_groups else None,
        "publisher_group_targeting": pg_targeting if include_publisher_groups else None,
        "publisher_blacklist_filter": show_blacklisted_publishers if include_publisher_groups else None,
        "filtered_sources": filtered_sources,
        "date__gte": start_date,
        "date__lte": end_date,
    }
    return constraints


def _prepare_publisher_groups_constraints(
    allowed_accounts,
    allowed_campaigns,
    allowed_ad_groups,
    constrain_accounts,
    constrain_campaigns,
    constrain_ad_group,
    filtered_sources,
):
    (
        blacklists,
        whitelists,
        pg_targeting,
    ) = core.features.publisher_groups.get_publisher_group_targeting_multiple_entities(
        allowed_accounts if constrain_accounts else None,
        allowed_campaigns if constrain_campaigns else None,
        allowed_ad_groups if constrain_ad_group else None,
    )

    blacklisted_entries = dash.models.PublisherGroupEntry.objects.filter(
        publisher_group_id__in=blacklists
    ).filter_by_sources(filtered_sources, include_wo_source=True)
    whitelisted_entries = dash.models.PublisherGroupEntry.objects.filter(
        publisher_group_id__in=whitelists
    ).filter_by_sources(filtered_sources, include_wo_source=True)

    return blacklisted_entries, whitelisted_entries, pg_targeting


class Goals(object):
    def __init__(
        self, campaign_goals=None, conversion_goals=None, campaign_goal_values=None, pixels=None, primary_goals=None
    ):
        self.campaign_goals = campaign_goals or []
        self.conversion_goals = conversion_goals or []
        self.campaign_goal_values = campaign_goal_values or []
        self.pixels = pixels or []
        self.primary_goals = primary_goals or []


def get_goals(constraints, breakdown):
    campaign_goals, conversion_goals, campaign_goal_values, pixels = [], [], [], []
    primary_goals = []

    if constraints["allowed_campaigns"] is not None and constraints["allowed_campaigns"].count() == 1:
        campaign = constraints["allowed_campaigns"][0]
        conversion_goals = campaign.conversiongoal_set.all().select_related("pixel")
        campaign_goals = (
            campaign.campaigngoal_set.all()
            .order_by("-primary", "created_dt")
            .select_related("conversion_goal", "conversion_goal__pixel", "campaign", "campaign__account")
        )
        primary_goals = [campaign_goals.first()]
        campaign_goal_values = dash.campaign_goals.get_campaign_goal_values(campaign)
        pixels = campaign.account.conversionpixel_set.filter(archived=False)

    elif constraints["allowed_accounts"].count() == 1:
        # only take for campaigns when constraints for 1 account, otherwise its too much
        account = constraints["allowed_accounts"][0]
        pixels = account.conversionpixel_set.filter(archived=False)

        if stats.constants.CAMPAIGN in breakdown:
            allowed_campaigns = constraints["allowed_campaigns"]
            conversion_goals = dash.models.ConversionGoal.objects.filter(campaign__in=allowed_campaigns).select_related(
                "pixel"
            )

            campaign_goals = (
                dash.models.CampaignGoal.objects.filter(campaign__in=allowed_campaigns)
                .order_by("-primary", "created_dt")
                .select_related("conversion_goal", "conversion_goal__pixel", "campaign", "campaign__account")
            )

            primary_goals_by_campaign = {}
            for cg in campaign_goals:
                if cg.campaign_id not in primary_goals_by_campaign:
                    primary_goals_by_campaign[cg.campaign_id] = cg
            primary_goals = list(primary_goals_by_campaign.values())

            for campaign in allowed_campaigns:
                campaign_goal_values.extend(dash.campaign_goals.get_campaign_goal_values(campaign))

    return Goals(campaign_goals, conversion_goals, campaign_goal_values, pixels, primary_goals)
