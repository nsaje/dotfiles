from collections import defaultdict

from django.db import models
from django.forms import ValidationError

import core.features.bcm
import dash
import dash.constants
import dash.models


class CpcValidationError(ValidationError):
    pass


def validate_cpc(cpc, bcm_modifiers=None, rules=None, **levels):
    if rules is None:
        rules = get_rules(cpc, bcm_modifiers, **levels)
    for rule in rules:
        if (rule.bcm_min_cpc is not None and rule.bcm_min_cpc > cpc) or (
            rule.bcm_max_cpc is not None and rule.bcm_max_cpc < cpc
        ):
            raise ValidationError("Bid CPC is violating some constraints: " + ", ".join(map(str, rules)))


def get_rules(cpc, bcm_modifiers=None, select_related=False, **levels):
    rules = dash.models.CpcConstraint.objects.all().filter_applied(cpc, bcm_modifiers, **levels)
    if select_related:
        rules = rules.select_related("source")
    return rules


def get_rules_per_source(ad_group, bcm_modifiers=None):
    rules = get_rules(None, bcm_modifiers, select_related=True, ad_group=ad_group)
    rules_for_all_sources = [rule for rule in rules if rule.source is None]
    rules_per_source = defaultdict(lambda: list(rules_for_all_sources))
    for rule in rules:
        if rule.source is None:
            continue
        rules_per_source[rule.source].append(rule)
    return rules_per_source


def adjust_cpc(cpc, bcm_modifiers=None, rules=None, **levels):
    if rules is None:
        rules = get_rules(cpc, bcm_modifiers, **levels)
    for rule in rules:
        cpc = max(rule.bcm_min_cpc or cpc, cpc)
        cpc = min(rule.bcm_max_cpc or cpc, cpc)
    return cpc


def create(
    constraint_type=dash.constants.CpcConstraintType.MANUAL,
    min_cpc=None,
    max_cpc=None,
    enforce_cpc_settings=False,
    **levels
):
    assert levels
    if dash.models.CpcConstraint.objects.filter(
        constraint_type=constraint_type, min_cpc=min_cpc, max_cpc=max_cpc, **levels
    ).exists():
        return
    if enforce_cpc_settings:
        enforce_rule(min_cpc, max_cpc, **levels)
    else:
        validate_source_settings(min_cpc, max_cpc, **levels)
    dash.models.CpcConstraint.objects.create(
        constraint_type=constraint_type, min_cpc=min_cpc, max_cpc=max_cpc, **levels
    )


def clear(constraint_type, **levels):
    assert levels
    dash.models.CpcConstraint.objects.filter(constraint_type=constraint_type, **levels).delete()


def enforce_rule(min_cpc=None, max_cpc=None, **levels):
    ag_sources_settings = _get_ad_group_sources_settings(**levels)
    bcm_modifiers_map = _get_bcm_modifiers_map(ag_sources_settings)
    for agss in ag_sources_settings:
        bcm_min_cpc, bcm_max_cpc = _get_bcm_min_max_cpcs(
            min_cpc, max_cpc, bcm_modifiers_map.get(agss.ad_group_source.ad_group.campaign_id)
        )
        _enforce_ags_cpc(agss.ad_group_source, agss.cpc_cc, bcm_min_cpc, bcm_max_cpc)


def _enforce_ags_cpc(ad_group_source, current_cpc, min_cpc, max_cpc):
    adjusted_cpc = max(min_cpc or current_cpc, current_cpc)
    adjusted_cpc = min(max_cpc or adjusted_cpc, adjusted_cpc)
    if current_cpc != adjusted_cpc:
        ad_group_source.settings.update(cpc_cc=adjusted_cpc, skip_validation=False)


def validate_source_settings(min_cpc=None, max_cpc=None, **levels):
    """
    When creating a CPC constraint, check all active ad group source settings
    if any existing bid CPCs violate the introduced limitations.
    """
    if _any_source_settings_invalid(min_cpc, max_cpc, **levels):
        raise CpcValidationError("Invalid source settings on some ad groups. " "Please contact Customer Success Team.")


def _any_source_settings_invalid(min_cpc, max_cpc, **levels):
    ag_sources_settings = _get_ad_group_sources_settings(**levels)
    bcm_modifiers_map = _get_bcm_modifiers_map(ag_sources_settings)

    return any(
        _is_invalid(agss, min_cpc, max_cpc, bcm_modifiers_map.get(agss.ad_group_source.ad_group.campaign_id))
        for agss in ag_sources_settings
    )


def _is_invalid(ag_source_setting, min_cpc, max_cpc, bcm_modifiers):
    bcm_min_cpc, bcm_max_cpc = _get_bcm_min_max_cpcs(min_cpc, max_cpc, bcm_modifiers)
    return (bcm_min_cpc and ag_source_setting.cpc_cc < bcm_min_cpc) or (
        bcm_max_cpc and ag_source_setting.cpc_cc > bcm_max_cpc
    )


def _get_bcm_min_max_cpcs(min_cpc, max_cpc, bcm_modifiers):
    bcm_min_cpc = core.features.bcm.calculations.calculate_min_bid_value(min_cpc, bcm_modifiers)
    bcm_max_cpc = core.features.bcm.calculations.calculate_max_bid_value(max_cpc, bcm_modifiers)
    return bcm_min_cpc, bcm_max_cpc


def _get_invalid_ad_group_sources_settings(min_cpc=None, max_cpc=None, **levels):
    cpc_rules = models.Q()
    if min_cpc:
        cpc_rules |= models.Q(cpc_cc__lte=min_cpc)
    if max_cpc:
        cpc_rules |= models.Q(cpc_cc__gte=max_cpc)
    ag_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(
        pk__in=dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group_id__in=(
                dash.models.AdGroup.objects.all().exclude_archived().values_list("id", flat=True)
            ),
            **_get_ags_level_constraints(levels)
        )
        .group_current_settings()
        .values_list("id", flat=True),
        state=dash.constants.AdGroupSettingsState.ACTIVE,
    ).filter(cpc_rules)
    return ag_sources_settings


def _get_ad_group_sources_settings(**levels):
    return (
        dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group_id__in=(
                dash.models.AdGroup.objects.all().exclude_archived().values_list("id", flat=True)
            ),
            **_get_ags_level_constraints(levels)
        )
        .select_related("ad_group_source__ad_group")
        .group_current_settings()
    )


def _get_bcm_modifiers_map(ag_sources_settings):
    campaigns = dash.models.Campaign.objects.filter(
        adgroup__adgroupsource__id__in=ag_sources_settings.values_list("ad_group_source_id")
    )
    return {campaign.id: campaign.get_bcm_modifiers() for campaign in campaigns}


def _get_ags_level_constraints(levels):
    constraints = {}
    for level, value in levels.items():
        search_key = ""
        if "ad_group" in level:
            search_key = "ad_group"
        if "campaign" in level:
            search_key = "ad_group__campaign"
        if "account" in level:
            search_key = "ad_group__campaign__account"
        if "agency" in level:
            search_key = "ad_group__campaign__account__agency"
        if "source" in level:
            search_key = "source"
        constraints["ad_group_source__" + search_key + "_id"] = value if "_id" in level else value.pk
    return constraints
