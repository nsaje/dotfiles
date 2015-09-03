from django.core.management.base import BaseCommand
from django.db.models import Sum

import reports.models
from reports import redshift

from utils.statsd_helper import statsd_gauge


class Command(BaseCommand):

    def handle(self, *args, **options):
        n_imps = reports.models.ArticleStats.objects\
            .aggregate(impressions=Sum('impressions')).get('impressions') or 0
        n_imps_aggregate = reports.models.AdGroupStats.objects\
            .aggregate(impressions=Sum('impressions')).get('impressions') or 0

        n_visits = reports.models.ArticleStats.objects\
            .aggregate(visits=Sum('visits')).get('visits') or 0
        n_visits_aggregate = reports.models.AdGroupStats.objects\
            .aggregate(visits=Sum('visits')).get('visits') or 0

        n_conversions = reports.models.GoalConversionStats.objects\
            .aggregate(conversions=Sum('conversions')).get('conversions') or 0
        n_conversions_aggregate = reports.models.AdGroupGoalConversionStats.objects\
            .aggregate(conversions=Sum('conversions')).get('conversions') or 0

        n_impressions_contentads = reports.models.ContentAdStats.objects\
            .aggregate(impressions=Sum('impressions')).get('impressions') or 0
        n_visits_contentads = reports.models.ContentAdPostclickStats.objects\
            .aggregate(impressions=Sum('visits')).get('visits') or 0

        contentads_aggregates = redshift.sum_contentadstats()
        n_impressions_contentads_aggregate = contentads_aggregates['impressions']
        n_visits_contentads_aggregate = contentads_aggregates['visits']

        statsd_gauge('reports.impressions_total', n_imps)
        statsd_gauge('reports.impressions_total_aggr', n_imps_aggregate)
        statsd_gauge('reports.visits_total', n_visits)
        statsd_gauge('reports.visits_total_aggr', n_visits_aggregate)
        statsd_gauge('reports.conversions_total', n_conversions)
        statsd_gauge('reports.conversions_total_aggr', n_conversions_aggregate)

        # content ads
        # TODO temp fix
        #statsd_gauge('reports.impressions_contentads_total', n_impressions_contentads)
        #statsd_gauge('reports.impressions_contentads_total_aggr', n_impressions_contentads_aggregate)
        #statsd_gauge('reports.visits_contentads_total', n_visits_contentads)
        #statsd_gauge('reports.visits_contentads_total_aggr', n_visits_contentads_aggregate)
