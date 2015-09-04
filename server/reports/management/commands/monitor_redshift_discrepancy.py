from django.core.management.base import BaseCommand
from django.db.models import Sum

import reports.models
from reports import redshift

from utils.statsd_helper import statsd_gauge


class Command(BaseCommand):

    def handle(self, *args, **options):
        n_impressions_contentads = reports.models.ContentAdStats.objects\
            .aggregate(impressions=Sum('impressions')).get('impressions') or 0
        n_visits_contentads = reports.models.ContentAdPostclickStats.objects\
            .aggregate(impressions=Sum('visits')).get('visits') or 0

        contentads_redshift = redshift.sum_contentadstats()

        statsd_gauge('reports.impressions_contentads_total', n_impressions_contentads)
        statsd_gauge('reports.impressions_contentads_total_aggr', contentads_redshift['impressions'])

        statsd_gauge('reports.visits_contentads_total', n_visits_contentads)
        statsd_gauge('reports.visits_contentads_total_aggr', contentads_redshift['visits'])
