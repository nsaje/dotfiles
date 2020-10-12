from django.conf import settings
from django.db.models import Q

import core.models
import dash.campaign_goals
import dash.features.custom_flags
import dash.models
import dash.retargeting_helper
import restapi.common.helpers
from core.features import bid_modifiers


def get_extra_data(user, ad_group):
    primary_campaign_goal = dash.campaign_goals.get_primary_campaign_goal(ad_group.campaign)

    default_settings = get_default_settings(ad_group)

    retargetable_ad_groups = get_retargetable_ad_groups(
        user, ad_group, ad_group.settings.retargeting_ad_groups + ad_group.settings.exclusion_retargeting_ad_groups
    )

    audiences = get_audiences(
        user, ad_group, ad_group.settings.audience_targeting + ad_group.settings.exclusion_audience_targeting
    )

    warnings = get_warnings(ad_group)

    extra = {
        "action_is_waiting": False,
        "can_restore": ad_group.can_restore(),
        "is_campaign_autopilot_enabled": ad_group.campaign.settings.autopilot,
        "account_id": ad_group.campaign.account_id,
        "agency_id": ad_group.campaign.account.agency_id,
        "currency": ad_group.campaign.account.currency,
        "optimization_objective": primary_campaign_goal.type if primary_campaign_goal else None,
        "default_settings": default_settings,
        "retargetable_ad_groups": retargetable_ad_groups,
        "audiences": audiences,
        "warnings": warnings,
        "current_bids": {"cpc": ad_group.settings.local_cpc, "cpm": ad_group.settings.local_cpm},
        "agency_uses_realtime_autopilot": (
            ad_group.campaign.account.agency.uses_realtime_autopilot if ad_group.campaign.account.agency else False
        ),
    }

    if user.has_perm("zemauth.can_see_backend_hacks"):
        extra["hacks"] = get_hacks(ad_group)

    if user.has_perm("zemauth.can_see_deals_in_ui"):
        extra["deals"] = get_deals(ad_group)

    overview = get_bid_modifier_type_summaries(ad_group)
    if overview is not None:
        extra["bid_modifier_type_summaries"] = overview

    return extra


def get_default_settings(ad_group):
    settings = ad_group.campaign.settings

    result = {
        "target_regions": settings.target_regions,
        "exclusion_target_regions": settings.exclusion_target_regions,
        "target_devices": settings.target_devices,
        "target_os": settings.target_os,
        "target_environments": settings.target_environments,
    }

    return result


def get_retargetable_ad_groups(user, ad_group, existing_targetings):
    account = ad_group.campaign.account
    if account.id == settings.HARDCODED_ACCOUNT_ID_OEN:
        return []

    ad_groups = (
        core.models.AdGroup.objects.filter(campaign__account=account)
        .select_related("campaign", "settings")
        .order_by("id")
    )

    result = [
        {"id": adg.id, "name": adg.name, "archived": adg.settings.archived, "campaign_name": adg.campaign.name}
        for adg in ad_groups
        if not adg.settings.archived or adg.id in existing_targetings
    ]

    return result


def get_audiences(user, ad_group, existing_targetings):
    audiences = (
        dash.models.Audience.objects.filter(pixel__account_id=ad_group.campaign.account.pk)
        .filter(Q(archived=False) | Q(pk__in=existing_targetings))
        .order_by("name")
    )

    return [
        {"id": audience.pk, "name": audience.name, "archived": audience.archived or False} for audience in audiences
    ]


def get_warnings(ad_group):
    warnings = {}

    ad_group_sources = ad_group.adgroupsource_set.all().select_related("source", "settings")
    supports_retargeting, unsupported_sources = dash.retargeting_helper.supports_retargeting(ad_group_sources)
    if not supports_retargeting:
        retargeting_warning = {"sources": [s.name for s in unsupported_sources]}
        warnings["retargeting"] = retargeting_warning

    return warnings


def get_deals(ad_group):
    if ad_group.id is None:
        return []
    return restapi.common.helpers.get_applied_deals_dict(ad_group.get_all_configured_deals())


def get_hacks(ad_group):
    if ad_group.id is None:
        return []
    return dash.models.CustomHack.objects.all().filter_applied(ad_group=ad_group).filter_active(
        True
    ).to_dict_list() + dash.features.custom_flags.helpers.get_all_custom_flags_on_ad_group(ad_group)


def get_bid_modifier_type_summaries(ad_group):
    if ad_group.id is None:
        return None
    return bid_modifiers.get_type_summaries(ad_group.id)
