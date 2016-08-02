DIMENSIONS = set(['content_ad', 'article', 'ad_group', 'date', 'source', 'account', 'campaign'])
TRAFFIC_FIELDS = [
    'clicks', 'impressions', 'data_cost',
    'cpc', 'ctr', 'title', 'url',
    'media_cost', 'e_media_cost', 'e_data_cost',
    'license_fee', 'billing_cost',
    'margin', 'agency_total', 'cpm',
]
POSTCLICK_ACQUISITION_FIELDS = ['visits', 'click_discrepancy', 'pageviews']
POSTCLICK_ENGAGEMENT_FIELDS = [
    'percent_new_users', 'pv_per_visit', 'avg_tos', 'bounce_rate', 'goals', 'new_visits',
    'returning_users', 'unique_users',
]
CONVERSION_GOAL_FIELDS = ['conversions']

CONTENTADSTATS_FIELD_MAPPING = {
    'date': 'date',
    'duration': 'total_time_on_site',
    'content_ad': 'content_ad_id',
    'source': 'source_id',
    'campaign': 'campaign_id',
    'account': 'account_id',
    'ad_group': 'adgroup_id'
}
CONTENTADSTATS_FIELD_REVERSE_MAPPING = {v: k for k, v in CONTENTADSTATS_FIELD_MAPPING.iteritems()}

CAMPAIGN_GOAL_FIELDS = [
    'total_seconds',
    'avg_cost_per_minute',
    'non_bounced_visits',
    'avg_cost_per_non_bounced_visit',
    'total_pageviews',
    'avg_cost_per_pageview',
    'avg_cost_for_new_visitor',
    'avg_cost_per_visit',
]

FIELD_PERMISSION_MAPPING = {
    'e_media_cost':     'zemauth.can_view_platform_cost_breakdown',
    'e_data_cost':      'zemauth.can_view_platform_cost_breakdown',
    'license_fee':      'zemauth.can_view_platform_cost_breakdown',

    'media_cost':       'zemauth.can_view_actual_costs',
    'data_cost':        'zemauth.can_view_actual_costs',

    'yesterday_cost':   'zemauth.can_view_actual_costs',
    'e_yesterday_cost': 'zemauth.can_view_platform_cost_breakdown',

    'margin':           'zemauth.can_view_agency_margin',
    'agency_total':     'zemauth.can_view_agency_margin',

    'total_fee': 'zemauth.can_view_flat_fees',
    'flat_fee': 'zemauth.can_view_flat_fees',
    'total_fee_projection': 'zemauth.can_view_flat_fees',

    'allocated_budget': 'zemauth.can_see_projections',
    'spend_projection': 'zemauth.can_see_projections',
    'pacing': 'zemauth.can_see_projections',
    'license_fee_projection': 'zemauth.can_see_projections',
    'total_fee_projection': 'zemauth.can_see_projections',

    'default_account_manager': 'zemauth.can_see_managers_in_accounts_table',
    'default_sales_representative': 'zemauth.can_see_managers_in_accounts_table',

    'campaign_manager': 'zemauth.can_see_managers_in_campaigns_table',
    'account_type': 'zemauth.can_see_account_type',

    'performance': 'zemauth.campaign_goal_performance',
    'styles': 'zemauth.campaign_goal_performance',

    'cpm':              'zemauth.can_view_new_columns',
    'unique_users':     'zemauth.can_view_new_columns',
    'returning_users':  'zemauth.can_view_new_columns',
}


def filter_by_permissions(result, user):
    '''
    filters reports such that the user will only get fields that he is allowed to see
    '''
    def filter_row(row):
        filtered_row = {}
        for field in DIMENSIONS:
            if field in row:
                filtered_row[field] = row[field]
        for field in TRAFFIC_FIELDS:
            if field in row:
                filtered_row[field] = row[field]
        if (user.has_perm('zemauth.content_ads_postclick_acquisition') or
                user.has_perm('zemauth.aggregate_postclick_acquisition')):
            for field in POSTCLICK_ACQUISITION_FIELDS:
                if field in row:
                    filtered_row[field] = row[field]
        if user.has_perm('zemauth.aggregate_postclick_engagement'):
            for field in POSTCLICK_ENGAGEMENT_FIELDS:
                if field in row:
                    filtered_row[field] = row[field]
        for field in CONVERSION_GOAL_FIELDS:
            if field in row:
                filtered_row[field] = row[field]
        if user.has_perm('zemauth.campaign_goal_optimization'):
            for field in CAMPAIGN_GOAL_FIELDS:
                if field in row:
                    filtered_row[field] = row[field]

        filtered_row = {
            field: value for field, value in filtered_row.iteritems()
            if field not in FIELD_PERMISSION_MAPPING or user.has_perm(FIELD_PERMISSION_MAPPING[field])
        }
        return filtered_row
    if isinstance(result, dict):
        return filter_row(result)
    else:
        return [filter_row(row) for row in result]


def get_fields_to_keep(user):
    fields_to_keep = []

    if ((user.has_perm('zemauth.content_ads_postclick_acquisition') or
         user.has_perm('zemauth.aggregate_postclick_acquisition'))):
        fields_to_keep.extend(POSTCLICK_ACQUISITION_FIELDS)

    if user.has_perm('zemauth.aggregate_postclick_engagement'):
        fields_to_keep.extend(POSTCLICK_ENGAGEMENT_FIELDS)

    for field, permission in FIELD_PERMISSION_MAPPING.iteritems():
        if user.has_perm(permission):
            fields_to_keep.append(field)

    return fields_to_keep


def remove_fields(rows, fields_to_keep):
    for row in rows:
        for field in row.keys():
            if field not in fields_to_keep:
                row.pop(field, None)
