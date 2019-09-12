import datetime

from rest_framework import serializers

import dash.constants
import dash.views.helpers
import stats.constants
import utils.columns

from . import constants


def get_breakdown_from_fields(fields, level):
    if not fields:
        raise serializers.ValidationError("Must define fields!")

    def _dimension_identifier(column_name):
        return stats.constants.get_dimension_identifier(
            utils.columns.get_field_name(column_name, raise_exception=False)
        )

    dimension_identifiers = [_dimension_identifier(field["field"]) for field in fields]

    breakdown = []
    for di in dimension_identifiers:
        if di in constants.BREAKDOWN_FIELDS and di not in breakdown:
            breakdown.append(di)
            for additional in _get_required_hierarchical_dimensions(di, level):
                if additional not in breakdown:
                    breakdown.append(additional)

    if stats.constants.PUBLISHER in breakdown and stats.constants.SOURCE in breakdown:
        breakdown.remove(stats.constants.SOURCE)

    return breakdown


def _get_required_hierarchical_dimensions(dimension, level):
    if dimension not in constants.HIERARCHY_BREAKDOWN_FIELDS:
        return []

    dimension_index = constants.HIERARCHY_BREAKDOWN_FIELDS.index(dimension)
    parent_breakdowns = constants.HIERARCHY_BREAKDOWN_FIELDS[:dimension_index]
    return limit_breakdown_to_level(parent_breakdowns, level)


def extract_view_breakdown(job):
    breakdowns = get_breakdown_names(job.query)
    if len(breakdowns) < 1:
        return "", []
    return breakdowns[0], ["By " + breakdown for breakdown in breakdowns[1:]]


def get_breakdown_names(query):
    level = get_level_from_constraints(get_filter_constraints(query["filters"]))
    breakdowns = limit_breakdown_to_level(get_breakdown_from_fields(query["fields"], level), level)

    breakdowns = [breakdown[:-3] if breakdown.endswith("_id") else breakdown for breakdown in breakdowns]
    breakdowns = [utils.columns.get_column_name(field_name) for field_name in breakdowns]

    return breakdowns


def extract_entity_names(user, constraints):
    if stats.constants.AD_GROUP in constraints:
        ad_group = dash.views.helpers.get_ad_group(user, constraints[stats.constants.AD_GROUP])
        return ad_group.name, ad_group.campaign.name, ad_group.campaign.account.name
    elif stats.constants.CAMPAIGN in constraints:
        campaign = dash.views.helpers.get_campaign(user, constraints[stats.constants.CAMPAIGN])
        return None, campaign.name, campaign.account.name
    elif stats.constants.ACCOUNT in constraints:
        account = dash.views.helpers.get_account(user, constraints[stats.constants.ACCOUNT])
        return None, None, account.name
    else:
        return None, None, None


def _parse_date(string):
    try:
        return datetime.datetime.strptime(string, "%Y-%m-%d").date()
    except ValueError:
        raise serializers.ValidationError("Invalid date format")


def _parse_id(string):
    try:
        return int(string)
    except ValueError:
        raise serializers.ValidationError("Invalid ID")


def get_filter_constraints(filters):
    filter_constraints = {}
    for f in filters:
        field_name = utils.columns.get_field_name(f["field"])

        if field_name in constants.STRUCTURE_CONSTRAINTS_FIELDS:
            if f["operator"] == constants.EQUALS:
                filter_constraints[field_name] = _parse_id(f["value"])
            elif f["operator"] == constants.IN:
                filter_constraints[field_name + "_list"] = [_parse_id(v) for v in f["values"]]
        if field_name == utils.columns.FieldNames.date and f["operator"] == constants.BETWEEN:
            filter_constraints["start_date"] = _parse_date(f["from"])
            filter_constraints["end_date"] = _parse_date(f["to"])
        if field_name == utils.columns.FieldNames.date and f["operator"] == constants.EQUALS:
            date = _parse_date(f["value"])
            filter_constraints["start_date"] = date
            filter_constraints["end_date"] = date
        if field_name == utils.columns.FieldNames.source and f["operator"] == constants.EQUALS:
            filter_constraints["sources"] = [f["value"]]
        if field_name == utils.columns.FieldNames.source and f["operator"] == constants.IN:
            filter_constraints["sources"] = f["values"]
        if field_name == utils.columns.FieldNames.agency and f["operator"] == constants.IN:
            filter_constraints["agencies"] = f["values"]
        if field_name == utils.columns.FieldNames.account_type and f["operator"] == constants.IN:
            filter_constraints["account_types"] = f["values"]
        if field_name == utils.columns.FieldNames.business and f["operator"] == constants.IN:
            filter_constraints["businesses"] = f["values"]
    return filter_constraints


def get_level_from_constraints(constraints):
    if stats.constants.AD_GROUP in constraints:
        return dash.constants.Level.AD_GROUPS
    elif "content_ad_id_list" in constraints:
        return dash.constants.Level.AD_GROUPS
    elif stats.constants.CAMPAIGN in constraints:
        return dash.constants.Level.CAMPAIGNS
    elif "ad_group_id_list" in constraints:
        return dash.constants.Level.CAMPAIGNS
    elif stats.constants.ACCOUNT in constraints:
        return dash.constants.Level.ACCOUNTS
    elif "campaign_id_list" in constraints:
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


def fill_currency_column(rows, columns, currency, account_currency_map):
    if "currency" not in columns:
        return
    if account_currency_map:
        for row in rows:
            row["currency"] = account_currency_map.get(row["account_id"])
    else:
        for row in rows:
            row["currency"] = currency


def get_option(job, option, default=None):
    return job.query.get("options", {}).get(option, default)


def extract_column_names(fields_list):
    fieldnames = []

    # extract unique field names
    for field in fields_list:
        field = field["field"]
        if field not in fieldnames:
            fieldnames.append(field)

    return fieldnames
