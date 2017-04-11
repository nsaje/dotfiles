import datetime

from rest_framework import serializers

import dash.constants
import stats.constants
import utils.columns

import constants


def get_breakdown_from_fields(fields):
    if not fields:
        raise serializers.ValidationError("Must define fields!")

    def _dimension_identifier(field):
        return stats.constants.get_dimension_identifier(utils.columns.FieldNames.from_column_name(field, raise_exception=False))

    dimension_identifiers = [_dimension_identifier(field['field']) for field in fields]

    breakdown = []
    for di in dimension_identifiers:
        if di in constants.BREAKDOWN_FIELDS and di not in breakdown:
            breakdown.append(di)

    if utils.columns.FieldNames.publisher_id in breakdown and utils.columns.FieldNames.source_id in breakdown:
        breakdown.remove(utils.columns.FieldNames.source_id)

    return breakdown


def get_breakdown_names(query):
    breakdowns = limit_breakdown_to_level(
        get_breakdown_from_fields(query['fields']),
        get_level_from_constraints(get_filter_constraints(query['filters'])),
    )

    breakdowns = [breakdown[:-3] if breakdown.endswith('_id') else breakdown for breakdown in breakdowns]
    breakdowns = [utils.columns._FIELD_MAPPING[breakdown][0] for breakdown in breakdowns]

    return breakdowns


def _parse_date(string):
    try:
        return datetime.datetime.strptime(string, '%Y-%m-%d').date()
    except ValueError:
        raise serializers.ValidationError("Invalid date format")


def get_filter_constraints(filters):
    filter_constraints = {}
    for f in filters:
        field_name = utils.columns.FieldNames.from_column_name(f['field'])

        if field_name in constants.STRUCTURE_CONSTRAINTS_FIELDS:
            if f['operator'] == constants.EQUALS:
                filter_constraints[field_name] = int(f['value'])
            elif f['operator'] == constants.IN:
                filter_constraints[field_name + '_list'] = [int(v) for v in f['values']]
        if field_name == utils.columns.FieldNames.date and f['operator'] == constants.BETWEEN:
            filter_constraints['start_date'] = _parse_date(f['from'])
            filter_constraints['end_date'] = _parse_date(f['to'])
        if field_name == utils.columns.FieldNames.date and f['operator'] == constants.EQUALS:
            date = _parse_date(f['value'])
            filter_constraints['start_date'] = date
            filter_constraints['end_date'] = date
        if field_name == utils.columns.FieldNames.source and f['operator'] == constants.EQUALS:
            filter_constraints['sources'] = [f['value']]
        if field_name == utils.columns.FieldNames.source and f['operator'] == constants.IN:
            filter_constraints['sources'] = f['values']
        if field_name == utils.columns.FieldNames.agency and f['operator'] == constants.IN:
            filter_constraints['agencies'] = f['values']
        if field_name == utils.columns.FieldNames.account_type and f['operator'] == constants.IN:
            filter_constraints['account_types'] = f['values']
    return filter_constraints


def get_level_from_constraints(constraints):
    if stats.constants.AD_GROUP in constraints:
        return dash.constants.Level.AD_GROUPS
    elif 'content_ad_id_list' in constraints:
        return dash.constants.Level.AD_GROUPS
    elif stats.constants.CAMPAIGN in constraints:
        return dash.constants.Level.CAMPAIGNS
    elif 'ad_group_id_list' in constraints:
        return dash.constants.Level.CAMPAIGNS
    elif stats.constants.ACCOUNT in constraints:
        return dash.constants.Level.ACCOUNTS
    elif 'campaign_id_list' in constraints:
        return dash.constants.Level.ACCOUNTS
    else:
        return dash.constants.Level.ALL_ACCOUNTS


def limit_breakdown_to_level(breakdown, level):
    if level == dash.constants.Level.AD_GROUPS:
        constraint_dimension = stats.constants.AD_GROUP
    elif level == dash.constants.Level.CAMPAIGNS:
        constraint_dimension = stats.constants.CAMPAIGN
    elif level == dash.constants.Level.ACCOUNTS:
        constraint_dimension = stats.constants.ACCOUNT
    else:
        return breakdown
    return stats.constants.get_child_breakdown_of_dimension(breakdown, constraint_dimension)
