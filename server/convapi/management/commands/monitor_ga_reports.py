import datetime

from django.core.management.base import BaseCommand
from django.db.models import Sum

import reports.api
import convapi.models

from utils.statsd_helper import statsd_gauge


class Command(BaseCommand):

    def handle(self, *args, **options):
        today = datetime.datetime.utcnow().date()
        n_aggregated_visits = reports.api.query(today, today).get('visits') or 0
        n_reported_visits = convapi.models.RawPostclickStats.objects.filter(
            datetime=today
        ).aggregate(visits_sum=Sum('visits')).get('visits_sum') or 0
        statsd_gauge('convapi.reported_visits', n_reported_visits)
        statsd_gauge('convapi.aggregated_visits', n_aggregated_visits)
