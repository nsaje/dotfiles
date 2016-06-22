from django.core.management.base import BaseCommand
from django.db.models import Sum

import reports.models

from utils.command_helpers import ExceptionCommand
from utils.statsd_helper import statsd_gauge


class Command(ExceptionCommand):

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

