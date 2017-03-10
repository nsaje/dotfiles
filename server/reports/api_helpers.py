DIMENSIONS = set(['content_ad', 'article', 'ad_group', 'date', 'source', 'account', 'campaign'])
TRAFFIC_FIELDS = [
    'clicks', 'impressions', 'data_cost',
    'cpc', 'ctr', 'title', 'url',
    'media_cost', 'e_media_cost', 'e_data_cost',
    'license_fee', 'billing_cost',
    'margin', 'agency_total', 'cpm',
]
POSTCLICK_ACQUISITION_FIELDS = ['click_discrepancy', ]
POSTCLICK_ENGAGEMENT_FIELDS = [
    'percent_new_users', 'pv_per_visit', 'avg_tos', 'bounce_rate', 'goals', 'new_visits',
    'returning_users', 'unique_users', 'bounced_visits', 'total_seconds', 'non_bounced_visits',
    'new_users', 'pageviews', 'visits',
]
CONVERSION_GOAL_FIELDS = ['conversions']

GOAL_FIELDS = [
    'avg_cost_per_minute', 'avg_cost_per_non_bounced_visit', 'avg_cost_per_pageview',
    'avg_cost_for_new_visitor', 'avg_cost_per_visit',
]


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

    'performance':      ('zemauth.campaign_goal_performance',),
    'styles':           ('zemauth.campaign_goal_performance',),
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
        for field in GOAL_FIELDS:
            if field in row:
                filtered_row[field] = row[field]

        filtered_row = {
            field: value for field, value in filtered_row.iteritems()
            if field not in FIELD_PERMISSION_MAPPING or user.has_perms(FIELD_PERMISSION_MAPPING[field])
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

    fields_to_keep.extend(GOAL_FIELDS)

    for field, permissions in FIELD_PERMISSION_MAPPING.iteritems():
        if not permissions or user.has_perms(permissions):
            fields_to_keep.append(field)

    return fields_to_keep


def remove_fields(rows, fields_to_keep):
    for row in rows:
        for row_field in row.keys():
            if row_field not in fields_to_keep:
                row.pop(row_field, None)


def custom_cleanup(user, rows):
    """
    Put here custom logics for cleaning fields that doesn't fit 'remove_fields'.
    """

    remove_content_ad_source_status = not user.has_perm('zemauth.can_see_media_source_status_on_submission_popover')

    if remove_content_ad_source_status:
        for row in rows:
            if row.get('status_per_source'):
                for source_status in row['status_per_source'].values():
                    source_status.pop('source_status', None)
