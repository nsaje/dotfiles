import dash.campaign_goals
import dash.models
from dash.constants import Level

from utils import exc

from stats import constants
from stats import fields
from stats.constants import StructureDimension

FIELD_PERMISSION_MAPPING = {
    'e_media_cost':     ('zemauth.can_view_platform_cost_breakdown',),
    'e_data_cost':      ('zemauth.can_view_platform_cost_breakdown',),
    'license_fee':      ('zemauth.can_view_platform_cost_breakdown',),

    'media_cost':       ('zemauth.can_view_actual_costs',),
    'data_cost':        ('zemauth.can_view_actual_costs',),

    'yesterday_cost':   ('zemauth.can_view_actual_costs',),
    'e_yesterday_cost': ('zemauth.can_view_platform_cost_breakdown',),

    'margin':           ('zemauth.can_view_agency_margin',),
    'agency_total':     ('zemauth.can_view_agency_margin',),

    'pacing':                 ('zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'),
    'allocated_budgets':      ('zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'),
    'spend_projection':       ('zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'),
    'license_fee_projection': ('zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown'),
    'total_fee':              ('zemauth.can_view_flat_fees', 'zemauth.can_view_platform_cost_breakdown'),
    'flat_fee':               ('zemauth.can_view_flat_fees', 'zemauth.can_view_platform_cost_breakdown'),

    'total_fee_projection':   ('zemauth.can_see_projections', 'zemauth.can_view_platform_cost_breakdown',
                               'zemauth.can_view_flat_fees'),

    'default_account_manager':      ('zemauth.can_see_managers_in_accounts_table',),
    'default_sales_representative': ('zemauth.can_see_managers_in_accounts_table',),
    'default_cs_representative': ('zemauth.can_see_managers_in_accounts_table',),

    'campaign_manager': ('zemauth.can_see_managers_in_campaigns_table',),
    'account_type':     ('zemauth.can_see_account_type',),
    'salesforce_url':   ('zemauth.can_see_salesforce_url',),
    'agency':           ('zemauth.can_view_account_agency_information',),
    'agency_id':        ('zemauth.can_view_account_agency_information',),

    'performance':      ('zemauth.campaign_goal_performance',),
    'styles':           ('zemauth.campaign_goal_performance',),
}

GOAL_FIELDS = [
    'avg_cost_per_minute', 'avg_cost_per_non_bounced_visit', 'avg_cost_per_pageview',
    'avg_cost_for_new_visitor', 'avg_cost_per_visit',
]


def filter_columns_by_permission(user, rows, goals):
    fields_to_keep = list(fields.DEFAULT_FIELDS)

    fields_to_keep.extend(_get_fields_to_keep(user))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_campaign_goals_fields(
        user, goals.campaign_goals, goals.campaign_goal_values, goals.conversion_goals
    ))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_conversion_goals_fields(
        user, goals.conversion_goals
    ))
    fields_to_keep.extend(dash.campaign_goals.get_allowed_pixels_fields(goals.pixels))

    _remove_fields(rows, fields_to_keep)
    _custom_cleanup(user, rows)


def validate_breakdown_by_permissions(level, user, breakdown):
    base_dimension = constants.get_base_dimension(breakdown)

    if level == Level.ALL_ACCOUNTS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.ACCOUNT):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.all_accounts_sources_view'):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.ACCOUNT and not user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

    elif level == Level.ACCOUNTS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.CAMPAIGN):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.SOURCE and not user.has_perm('zemauth.account_sources_view'):
            raise exc.MissingDataError()
        if base_dimension == StructureDimension.CAMPAIGN and not user.has_perm('zemauth.account_campaigns_view'):
            raise exc.MissingDataError()

    elif level == Level.CAMPAIGNS:
        if base_dimension not in (StructureDimension.SOURCE, StructureDimension.AD_GROUP):
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


def _get_fields_to_keep(user):
    fields_to_keep = []

    if ((user.has_perm('zemauth.content_ads_postclick_acquisition') or
         user.has_perm('zemauth.aggregate_postclick_acquisition'))):
        fields_to_keep.extend(fields.POSTCLICK_ACQUISITION_FIELDS)

    if user.has_perm('zemauth.aggregate_postclick_engagement'):
        fields_to_keep.extend(fields.POSTCLICK_ENGAGEMENT_FIELDS)

    fields_to_keep.extend(GOAL_FIELDS)

    for field, permissions in FIELD_PERMISSION_MAPPING.iteritems():
        if not permissions or user.has_perms(permissions):
            fields_to_keep.append(field)

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
