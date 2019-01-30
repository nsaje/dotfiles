from django.db.models import Q

import core.models
import dash.features.custom_flags
import dash.models
import dash.retargeting_helper


def get_extra_data(user, ad_group):
    retargetable_adgroups = get_retargetable_adgroups(
        user, ad_group, ad_group.settings.retargeting_ad_groups + ad_group.settings.exclusion_retargeting_ad_groups
    )

    audiences = get_audiences(
        user, ad_group, ad_group.settings.audience_targeting + ad_group.settings.exclusion_audience_targeting
    )

    warnings = get_warnings(ad_group)

    extra = {
        "action_is_waiting": False,
        "can_archive": ad_group.can_archive(),
        "can_restore": ad_group.can_restore(),
        "retargetable_adgroups": retargetable_adgroups,
        "audiences": audiences,
        "warnings": warnings,
    }

    if user.has_perm("zemauth.can_see_backend_hacks"):
        extra["hacks"] = get_hacks(ad_group)

    return extra


def get_retargetable_adgroups(user, ad_group, existing_targetings):
    if not user.has_perm("zemauth.can_view_retargeting_settings"):
        return []

    account = ad_group.campaign.account
    if account.id == 305:  # OEN
        return []

    ad_groups = (
        core.models.AdGroup.objects.filter(campaign__account=account)
        .select_related("campaign", "settings")
        .order_by("id")
    )

    if user.has_perm("zemauth.can_target_custom_audiences"):
        result = [
            {"id": adg.id, "name": adg.name, "archived": adg.settings.archived, "campaign_name": adg.campaign.name}
            for adg in ad_groups
            if not adg.settings.archived or adg.id in existing_targetings
        ]
    else:
        result = [
            {"id": adg.id, "name": adg.name, "archived": adg.settings.archived, "campaign_name": adg.campaign.name}
            for adg in ad_groups
        ]

    return result


def get_audiences(user, ad_group, existing_targetings):
    if not user.has_perm("zemauth.can_target_custom_audiences"):
        return []

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


def get_hacks(ad_group):
    return dash.models.CustomHack.objects.all().filter_applied(ad_group=ad_group).filter_active(
        True
    ).to_dict_list() + dash.features.custom_flags.helpers.get_all_custom_flags_on_ad_group(ad_group)
