from django.core.management.base import BaseCommand
from django.db.models import Sum

import reports.models

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

        statsd_gauge('reports.articlestats.impressions_total', n_imps)
        statsd_gauge('reports.articlestats.impressions_total_aggr', n_imps_aggregate)
        statsd_gauge('reports.articlestats.visits_total', n_visits)
        statsd_gauge('reports.articlestats.visits_total_aggr', n_visits_aggregate)
        statsd_gauge('reports.articlestats.conversions_total', n_conversions)
        statsd_gauge('reports.articlestats.conversions_total_aggr', n_conversions_aggregate)
