
from django.db.models import Sum, Max
from django.db import transaction

import reports.models
import dash.models


def refresh_adgroup_stats():
    rs = reports.models.ArticleStats.objects.values(
        'datetime', 'ad_group', 'source'
    ).annotate(
        impressions=Sum('impressions'),
        clicks=Sum('clicks'),
        cost_cc=Sum('cost_cc'),
        visits=Sum('visits'),
        new_visits=Sum('new_visits'),
        bounced_visits=Sum('bounced_visits'),
        pageviews=Sum('pageviews'),
        duration=Sum('duration'),
        has_traffic_metrics=Max('has_traffic_metrics'),
        has_postclick_metrics=Max('has_postclick_metrics'),
        has_conversion_metrics=Max('has_conversion_metrics'),
    )
    ad_group_lookup = {}
    source_lookup = {}
    with transaction.atomic():
        for row in rs:
            if row['ad_group'] not in ad_group_lookup:
                ad_group_lookup[row['ad_group']] = \
                    dash.models.AdGroup.objects.get(pk=row['ad_group'])
            if row['source'] not in source_lookup:
                source_lookup[row['source']] = \
                    dash.models.Source.objects.get(pk=row['source'])
            dimensions = {
                'datetime': row['datetime'],
                'ad_group': ad_group_lookup[row['ad_group']],
                'source': source_lookup[row['source']]
            }
            row['ad_group'] = ad_group_lookup[row['ad_group']]
            row['source'] = source_lookup[row['source']]
            try:
                adgroup_stats = reports.models.AdGroupStats.objects.get(**dimensions)
                for metric, value in row.items():
                    if metric not in ('datetime', 'ad_group', 'source'):
                        adgroup_stats.__setattr__(metric, value)
            except reports.models.AdGroupStats.DoesNotExist:
                adgroup_stats = reports.models.AdGroupStats(**row)

            adgroup_stats.save()




def refresh_adgroup_conversion_stats():
    pass