from django.core.management.base import BaseCommand
from django.db.models import Sum, Max

import influx

import reports.api
import convapi.models
import dash.models

from utils.command_helpers import ExceptionCommand
from utils.statsd_helper import statsd_gauge
import influx


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        max_date = convapi.models.RawPostclickStats.objects.aggregate(max_date=Max('datetime'))['max_date']
        real_adgroups = dash.models.AdGroup.objects.exclude(pk__in=dash.models.AdGroup.demo_objects.all())
        n_aggregated_visits = reports.api.query(max_date, max_date, ad_group=real_adgroups).get('visits') or 0
        n_reported_visits = convapi.models.RawPostclickStats.objects.filter(
            datetime=max_date
        ).aggregate(visits_sum=Sum('visits')).get('visits_sum') or 0
        statsd_gauge('convapi.reported_visits', n_reported_visits)
        statsd_gauge('convapi.aggregated_visits', n_aggregated_visits)
        influx.gauge('convapi.visits', n_reported_visits, state='reported')
        influx.gauge('convapi.visits', n_aggregated_visits, state='aggregated')
