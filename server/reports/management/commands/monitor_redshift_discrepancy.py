from django.core.management.base import BaseCommand
from django.db.models import Sum

import reports.models
from reports import redshift

from utils.statsd_helper import statsd_gauge


class Command(BaseCommand):

    def handle(self, *args, **options):
        n_impressions = reports.models.ContentAdStats.objects\
            .aggregate(impressions=Sum('impressions')).get('impressions') or 0
        n_visits = reports.models.ContentAdPostclickStats.objects\
            .aggregate(impressions=Sum('visits')).get('visits') or 0

        redshift_sums = redshift.sum_contentadstats()

        statsd_gauge('reports.contentadstats.impressions_total', n_impressions)
        statsd_gauge('reports.contentadstats.impressions_total_aggr', redshift_sums['impressions'])

        statsd_gauge('reports.contentadstats.visits_total', n_visits)
        statsd_gauge('reports.contentadstats.visits_total_aggr', redshift_sums['visits'])
