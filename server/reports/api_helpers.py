DIMENSIONS = set(['content_ad', 'article', 'ad_group', 'date', 'source', 'account', 'campaign', 'domain', 'exchange'])
TRAFFIC_FIELDS = ['clicks', 'impressions', 'cost', 'cpc', 'ctr', 'title', 'url']
POSTCLICK_ACQUISITION_FIELDS = ['visits', 'click_discrepancy', 'pageviews']
POSTCLICK_ENGAGEMENT_FIELDS = [
    'percent_new_users', 'pv_per_visit', 'avg_tos', 'bounce_rate', 'goals'
]


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
        if (user.has_perm('zemauth.content_ads_postclick_engagement') or
                user.has_perm('zemauth.aggregate_postclick_engagement')):
            for field in POSTCLICK_ENGAGEMENT_FIELDS:
                if field in row:
                    filtered_row[field] = row[field]
        return filtered_row
    if isinstance(result, dict):
        return filter_row(result)
    else:
        return [filter_row(row) for row in result]
