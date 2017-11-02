import dash.campaign_goals
import dash.models
from dash.constants import Level, CampaignGoalKPI

from utils import exc

from stats import constants
from stats import fields
from stats.constraints_helper import get_uses_bcm_v2
from stats.constants import StructureDimension, DeliveryDimension


NOT_PUBLIC_ANYMORE = [
    'zemauth.can_view_platform_cost_breakdown_derived',
    'zemauth.can_view_platform_cost_breakdown',
    'zemauth.can_view_agency_margin',
    'zemauth.can_view_flat_fees',
]


def has_perm_bcm_v2(user, permission, uses_bcm_v2=False):
    return has_perms_bcm_v2(user, [permission], uses_bcm_v2)


def has_perms_bcm_v2(user, permissions, uses_bcm_v2=False):
    if not uses_bcm_v2 and any(x in NOT_PUBLIC_ANYMORE for x in permissions):
        permissions = [x for x in permissions if x not in NOT_PUBLIC_ANYMORE]

        if not permissions:
            # if after that no permissions are left it is allowed
            return True

    return user.has_perms(permissions)


BCM2_DEPRECATED_FIELDS = {
    'agency_cost', 'billing_cost', 'total_cost',
    'cpc', 'cpm', 'video_cpv', 'video_cpcv',
    'avg_cost_per_minute', 'avg_cost_per_non_bounced_visit', 'avg_cost_per_pageview',
    'avg_cost_for_new_visitor', 'avg_cost_per_visit',
    'yesterday_cost', 'e_yesterday_cost'
}

FIELD_PERMISSION_MAPPING = {
    'media_cost':          ('zemauth.can_view_actual_costs',),
    'e_media_cost':        ('zemauth.can_view_platform_cost_breakdown',),

    'data_cost':           ('zemauth.can_view_actual_costs',),
    'e_data_cost':         ('zemauth.can_view_platform_cost_breakdown',),

    'at_cost':             ('zemauth.can_view_actual_costs',),
    'et_cost':             ('zemauth.can_view_platform_cost_breakdown_derived',),
    'etf_cost':            ('zemauth.can_view_agency_cost_breakdown',),
    'etfm_cost':           ('zemauth.can_view_end_user_cost_breakdown',),

    'license_fee':         ('zemauth.can_view_platform_cost_breakdown',),
    'margin':              ('zemauth.can_view_agency_margin',),

    'yesterday_at_cost':   ('zemauth.can_view_actual_costs',),
    'yesterday_et_cost':   ('zemauth.can_view_platform_cost_breakdown_derived',),
    'yesterday_etfm_cost': ('zemauth.can_view_end_user_cost_breakdown',),

    'et_cpc':              ('zemauth.can_view_platform_cost_breakdown_derived',),
    'et_cpm':              ('zemauth.can_view_platform_cost_breakdown_derived',),
    'video_et_cpv':        ('zemauth.can_view_platform_cost_breakdown_derived',),
    'video_et_cpcv':       ('zemauth.can_view_platform_cost_breakdown_derived',),

    'etfm_cpc':            ('zemauth.can_view_end_user_cost_breakdown',),
    'etfm_cpm':            ('zemauth.can_view_end_user_cost_breakdown',),
    'video_etfm_cpv':      ('zemauth.can_view_end_user_cost_breakdown',),
    'video_etfm_cpcv':     ('zemauth.can_view_end_user_cost_breakdown',),

    # legacy
    'agency_cost':         ('zemauth.can_view_agency_margin',),
    'yesterday_cost':      ('zemauth.can_view_actual_costs',),
    'e_yesterday_cost':    ('zemauth.can_view_platform_cost_breakdown',),

    'avg_et_cost_per_minute':              ('zemauth.can_view_platform_cost_breakdown',),
    'avg_et_cost_per_non_bounced_visit':   ('zemauth.can_view_platform_cost_breakdown',),
    'avg_et_cost_per_pageview':            ('zemauth.can_view_platform_cost_breakdown',),
    'avg_et_cost_for_new_visitor':         ('zemauth.can_view_platform_cost_breakdown',),
    'avg_et_cost_per_visit':               ('zemauth.can_view_platform_cost_breakdown',),

    'avg_etfm_cost_per_minute':            ('zemauth.can_view_end_user_cost_breakdown',),
    'avg_etfm_cost_per_non_bounced_visit': ('zemauth.can_view_end_user_cost_breakdown',),
    'avg_etfm_cost_per_pageview':          ('zemauth.can_view_end_user_cost_breakdown',),
    'avg_etfm_cost_for_new_visitor':       ('zemauth.can_view_end_user_cost_breakdown',),
    'avg_etfm_cost_per_visit':             ('zemauth.can_view_end_user_cost_breakdown',),

    # projections
    'pacing':                 ('zemauth.can_view_platform_cost_breakdown',),
    'allocated_budgets':      ('zemauth.can_see_projections',),
    'spend_projection':       ('zemauth.can_view_platform_cost_breakdown',),
    'license_fee_projection': ('zemauth.can_view_platform_cost_breakdown',),
    'total_fee':              ('zemauth.can_view_flat_fees',),
    'flat_fee':               ('zemauth.can_view_flat_fees',),

    'total_fee_projection':   ('zemauth.can_view_flat_fees',),

    'default_account_manager':      ('zemauth.can_see_managers_in_accounts_table',),
    'default_sales_representative': ('zemauth.can_see_managers_in_accounts_table',),
    'default_cs_representative':    ('zemauth.can_see_managers_in_accounts_table',),

    'campaign_manager':      ('zemauth.can_see_managers_in_campaigns_table',),
    'account_type':          ('zemauth.can_see_account_type',),
    'salesforce_url':        ('zemauth.can_see_salesforce_url',),
    'agency':                ('zemauth.can_view_account_agency_information',),
    'agency_id':             ('zemauth.can_view_account_agency_information',),

    'performance':           ('zemauth.campaign_goal_performance',),
    'etfm_performance':      ('zemauth.campaign_goal_performance', 'zemauth.can_view_end_user_cost_breakdown'),
    'styles':                ('zemauth.campaign_goal_performance',),
}


def filter_columns_by_permission(user, rows, goals, constraints):
    fields_to_keep = _get_fields_to_keep(user, goals, get_uses_bcm_v2(user, constraints))
    _remove_fields(rows, fields_to_keep)
    _custom_cleanup(user, rows)


def _get_fields_to_keep(user, goals, uses_bcm_v2):
    fields_to_keep = set(fields.DIMENSION_FIELDS)
    fields_to_keep |= fields.SOURCE_FIELDS
    fields_to_keep |= fields.HELPER_FIELDS
    fields_to_keep |= fields.PUBLISHER_FIELDS
    fields_to_keep |= fields.DEFAULT_STATS

    if ((user.has_perm('zemauth.content_ads_postclick_acquisition') or
         user.has_perm('zemauth.aggregate_postclick_acquisition'))):
        fields_to_keep |= fields.POSTCLICK_ACQUISITION_FIELDS

    if user.has_perm('zemauth.aggregate_postclick_engagement'):
        fields_to_keep |= fields.POSTCLICK_ENGAGEMENT_FIELDS

    for field, permissions in FIELD_PERMISSION_MAPPING.iteritems():
        if not permissions or has_perms_bcm_v2(user, permissions, uses_bcm_v2=uses_bcm_v2):
            fields_to_keep.add(field)
        if permissions and not has_perms_bcm_v2(user, permissions, uses_bcm_v2=uses_bcm_v2) and field in fields_to_keep:
            fields_to_keep.remove(field)

    # add allowed dynamically generated goals fields
    fields_to_keep |= _get_allowed_campaign_goals_fields(
        user, goals.campaign_goals, goals.campaign_goal_values, goals.conversion_goals, uses_bcm_v2)
    fields_to_keep |= _get_allowed_conversion_goals_fields(user, goals.conversion_goals)
    fields_to_keep |= _get_allowed_pixels_fields(user, goals.pixels, uses_bcm_v2)

    if uses_bcm_v2:
        fields_to_keep -= BCM2_DEPRECATED_FIELDS

    return fields_to_keep


def _remove_fields(rows, fields_to_keep):
    for row in rows:
        for row_field in row.keys():
            if row_field not in fields_to_keep:
                row.pop(row_field, None)


def _custom_cleanup(user, rows):
    """
    Put here custom logics for cleaning fields that doesn't fit '_remove_fields'.
    """

    remove_content_ad_source_status = not user.has_perm('zemauth.can_see_media_source_status_on_submission_popover')

    if remove_content_ad_source_status:
        for row in rows:
            if row.get('status_per_source'):
                for source_status in row['status_per_source'].values():
                    source_status.pop('source_status', None)


def _get_allowed_campaign_goals_fields(user, campaign_goals, campaign_goal_values, conversion_goals, uses_bcm_v2):
    """
    Returns campaign goal field names that should be kept if user has
    proper permissions.
    """

    allowed_fields = set()
    included_campaign_goals = []

    can_add_et_fields = has_perm_bcm_v2(user, 'zemauth.can_view_platform_cost_breakdown', uses_bcm_v2)
    can_add_etfm_fields = has_perm_bcm_v2(user, 'zemauth.can_view_end_user_cost_breakdown', uses_bcm_v2)

    if user.has_perm('zemauth.campaign_goal_optimization'):
        included_campaign_goals = [x.campaign_goal.type for x in campaign_goal_values]

    for goal in included_campaign_goals:
        relevant_fields = dash.campaign_goals.get_relevant_goal_fields_map(uses_bcm_v2).get(goal, [])
        allowed_fields |= set(relevant_fields)

    if CampaignGoalKPI.CPA in included_campaign_goals:

        if not uses_bcm_v2:
            allowed_fields |= set(
                'avg_cost_per_{}'.format(cg.get_view_key(conversion_goals)) for cg in conversion_goals)

        if can_add_et_fields:
            allowed_fields |= set(
                'avg_et_cost_per_{}'.format(cg.get_view_key(conversion_goals)) for cg in conversion_goals)

        if can_add_etfm_fields:
            allowed_fields |= set(
                'avg_etfm_cost_per_{}'.format(cg.get_view_key(conversion_goals)) for cg in conversion_goals)

    if user.has_perm('zemauth.campaign_goal_performance'):
        allowed_fields |= set('performance_' + x.get_view_key() for x in campaign_goals)

        if can_add_etfm_fields:
            allowed_fields |= set('etfm_performance_' + x.get_view_key() for x in campaign_goals)

    return allowed_fields


def _get_allowed_conversion_goals_fields(user, conversion_goals):
    """
    Returns conversion goal column names that should be kept if user has
    proper permissions.
    """

    if user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
        return set(cg.get_view_key(conversion_goals) for cg in conversion_goals)

    return set()


def _get_allowed_pixels_fields(user, pixels, uses_bcm_v2):
    """
    Returns pixel column names and average costs column names that should be kept for all users.
    """

    can_add_et_fields = has_perm_bcm_v2(user, 'zemauth.can_view_platform_cost_breakdown', uses_bcm_v2)
    can_add_etfm_fields = has_perm_bcm_v2(user, 'zemauth.can_view_end_user_cost_breakdown', uses_bcm_v2)

    allowed = set()
    for pixel in pixels:
        for conversion_window in dash.constants.ConversionWindows.get_all():
            view_key = pixel.get_view_key(conversion_window)
            allowed.add(view_key)

            if not uses_bcm_v2:
                allowed.add('avg_cost_per_' + view_key)
                allowed.add('roas_' + view_key)

            if can_add_et_fields:
                allowed.add('avg_et_cost_per_' + view_key)
                allowed.add('et_roas_' + view_key)

            if can_add_etfm_fields:
                allowed.add('avg_etfm_cost_per_' + view_key)
                allowed.add('etfm_roas_' + view_key)

    return allowed


def validate_breakdown_by_permissions(level, user, breakdown):
    base_dimension = constants.get_base_dimension(breakdown)

    if level == Level.ALL_ACCOUNTS:
        if base_dimension not in (
                StructureDimension.SOURCE, StructureDimension.ACCOUNT, StructureDimension.PUBLISHER):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.all_accounts_sources_view'):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.ACCOUNT and not user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

    elif level == Level.ACCOUNTS:
        if base_dimension not in (
                StructureDimension.SOURCE, StructureDimension.CAMPAIGN, StructureDimension.PUBLISHER):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.account_sources_view'):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.CAMPAIGN and not user.has_perm('zemauth.account_campaigns_view'):
            raise exc.MissingDataError()

    elif level == Level.CAMPAIGNS:
        if base_dimension not in (
                StructureDimension.SOURCE, StructureDimension.AD_GROUP, StructureDimension.PUBLISHER):
            raise exc.MissingDataError()

    elif level == Level.AD_GROUPS:
        if base_dimension not in (
                StructureDimension.SOURCE, StructureDimension.CONTENT_AD, StructureDimension.PUBLISHER):
            raise exc.MissingDataError()

    if StructureDimension.PUBLISHER in breakdown and not user.has_perm('zemauth.can_see_publishers'):
        raise exc.MissingDataError()

    delivery_dimension = constants.get_delivery_dimension(breakdown)
    if delivery_dimension is not None and not user.has_perm('zemauth.can_view_breakdown_by_delivery'):
        raise exc.MissingDataError()

    if delivery_dimension in DeliveryDimension._EXTENDED and not user.has_perm('zemauth.can_view_breakdown_by_delivery_extended'):
        raise exc.MissingDataError()


def validate_breakdown_by_structure(breakdown):
    base = constants.get_base_dimension(breakdown)
    if not base:
        return

    clean_breakdown = [base]
    structure = constants.get_structure_dimension(breakdown)
    if structure:
        clean_breakdown.append(structure)

    delivery = constants.get_delivery_dimension(breakdown)
    if delivery:
        clean_breakdown.append(delivery)

    time = constants.get_time_dimension(breakdown)
    if time:
        clean_breakdown.append(time)

    if 'publisher_id' in breakdown and 'source_id' in breakdown:
        raise exc.InvalidBreakdownError("Unsupported breakdown - publishers are broken down by source by default")

    unsupperted_breakdowns = set(breakdown) - set(clean_breakdown)
    if unsupperted_breakdowns:
        raise exc.InvalidBreakdownError("Unsupported breakdowns: {}".format(', '.join(unsupperted_breakdowns)))

    if breakdown != clean_breakdown:
        raise exc.InvalidBreakdownError("Wrong breakdown order")
