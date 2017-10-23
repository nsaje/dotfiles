from django.forms import ValidationError
from django.db import models

import core.bcm

import dash
import dash.models
import dash.constants
from utils import lc_helper


class CpcValidationError(ValidationError):
    pass


def validate_cpc(cpc, bcm_modifiers=None, **levels):
    rules = dash.models.CpcConstraint.objects.all().filter_applied(cpc, bcm_modifiers, **levels)
    if not rules:
        return
    raise ValidationError(
        'Bid CPC is violating some constraints: ' + ', '.join(map(str, rules))
    )


def adjust_cpc(cpc, bcm_modifiers=None, **levels):
    rules = dash.models.CpcConstraint.objects.all().filter_applied(cpc, bcm_modifiers, **levels)
    for rule in rules:
        cpc = max(rule.bcm_min_cpc or cpc, cpc)
        cpc = min(rule.bcm_max_cpc or cpc, cpc)
    return cpc


def create(constraint_type=dash.constants.CpcConstraintType.MANUAL,
           min_cpc=None, max_cpc=None, enforce_cpc_settings=False,
           **levels):
    assert levels
    if dash.models.CpcConstraint.objects.filter(
            constraint_type=constraint_type,
            min_cpc=min_cpc,
            max_cpc=max_cpc,
            **levels).exists():
        return
    if enforce_cpc_settings:
        enforce_rule(min_cpc, max_cpc, **levels)
    else:
        validate_source_settings(min_cpc, max_cpc, **levels)
    dash.models.CpcConstraint.objects.create(
        constraint_type=constraint_type,
        min_cpc=min_cpc,
        max_cpc=max_cpc,
        **levels
    )


def clear(constraint_type, **levels):
    assert levels
    dash.models.CpcConstraint.objects.filter(
        constraint_type=constraint_type,
        **levels
    ).delete()


def enforce_rule(min_cpc=None, max_cpc=None, **levels):
    ag_sources_settings = _get_ad_group_sources_settings(**levels)
    bcm_modifiers_map = _get_bcm_modifiers_map(ag_sources_settings)
    for agss in ag_sources_settings:
        ad_group_source = agss.ad_group_source
        bcm_modifiers = bcm_modifiers_map.get(ad_group_source.ad_group.campaign_id)
        bcm_min_cpc = core.bcm.calculations.calculate_min_cpc(min_cpc, bcm_modifiers)
        bcm_max_cpc = core.bcm.calculations.calculate_max_cpc(max_cpc, bcm_modifiers)
        current_cpc = agss.cpc_cc
        _enforce_ags_cpc(ad_group_source, current_cpc, bcm_min_cpc, bcm_max_cpc)


def _enforce_ags_cpc(ad_group_source, current_cpc, min_cpc, max_cpc):
    adjusted_cpc = max(min_cpc or current_cpc, current_cpc)
    adjusted_cpc = min(max_cpc or adjusted_cpc, adjusted_cpc)
    if current_cpc != adjusted_cpc:
        ad_group_source.update(
            cpc_cc=adjusted_cpc,
            skip_validation=False
        )


def validate_source_settings(min_cpc=None, max_cpc=None, **levels):
    """
    When creating a CPC constraint, check all active ad group source settings
    if any existing bid CPCs violate the introduced limitations.
    """
    ag_sources_settings = _get_invalid_ad_group_sources_settings(min_cpc, max_cpc, **levels)
    if ag_sources_settings.exists():
        source = levels.get('source') or levels.get('source_id') and dash.models.Source.objects.get(
            pk=levels.get('source_id')
        )
        msg = source and 'Source {} '.format(source.name) or ''
        msg += 'Bid CPC has to be '
        if min_cpc and max_cpc:
            msg += 'between {} and {} '.format(
                lc_helper.default_currency(min_cpc),
                lc_helper.default_currency(max_cpc),
            )
        elif min_cpc:
            msg += 'above {} '.format(
                lc_helper.default_currency(min_cpc),
            )
        elif max_cpc:
            msg += 'under {} '.format(
                lc_helper.default_currency(max_cpc),
            )
        raise CpcValidationError(msg + 'on all ad groups. Please contact Customer Success Team.')


def _get_invalid_ad_group_sources_settings(min_cpc=None, max_cpc=None, **levels):
    cpc_rules = models.Q()
    if min_cpc:
        cpc_rules |= models.Q(cpc_cc__lte=min_cpc)
    if max_cpc:
        cpc_rules |= models.Q(cpc_cc__gte=max_cpc)
    ag_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(
        pk__in=dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group_id__in=(
                dash.models.AdGroup.objects.all().exclude_archived().values_list('id', flat=True)
            ),
            **_get_ags_level_constraints(levels)
        ).group_current_settings().values_list('id', flat=True),
        state=dash.constants.AdGroupSettingsState.ACTIVE
    ).filter(cpc_rules)
    return ag_sources_settings


def _get_ad_group_sources_settings(**levels):
    return dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group_id__in=(
            dash.models.AdGroup.objects.all().exclude_archived().values_list('id', flat=True)
        ),
        **_get_ags_level_constraints(levels)
    ).select_related('ad_group_source__ad_group').group_current_settings()


def _get_bcm_modifiers_map(ag_sources_settings):
    campaigns = dash.models.Campaign.objects.filter(
        adgroup__adgroupsource__id__in=ag_sources_settings.values_list('ad_group_source_id')
    )
    return {
        campaign.id: campaign.get_bcm_modifiers() for campaign in campaigns
    }


def _get_ags_level_constraints(levels):
    constraints = {}
    for level, value in levels.iteritems():
        search_key = ''
        if 'ad_group' in level:
            search_key = 'ad_group'
        if 'campaign' in level:
            search_key = 'ad_group__campaign'
        if 'account' in level:
            search_key = 'ad_group__campaign__account'
        if 'agency' in level:
            search_key = 'ad_group__campaign__account__agency'
        if 'source' in level:
            search_key = 'source'
        constraints['ad_group_source__' + search_key + '_id'] = value if '_id' in level else value.pk
    return constraints
