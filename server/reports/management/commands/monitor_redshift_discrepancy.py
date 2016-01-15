from django.db.models import Sum

import reports.models
from reports import redshift

from utils.command_helpers import ExceptionCommand
from utils.statsd_helper import statsd_gauge


class Command(ExceptionCommand):

    def _post_metrics(self, prefix, stats, redshift_sums):
        for stats_key, stats_val in stats.keys():
            cads_total_name = '{prefix}.{stat_name}_total'.format(
                prefix=prefix,
                stat_name=stats_key
            )
            statsd_gauge(cads_total_name, stats_val)

            redshift_stat_name = '{prefix}.{stat_name}_total_aggr'.format(
                prefix=prefix,
                stat_name=stats_key
            )
            statsd_gauge(redshift_stat_name, redshift_sums[stats_key])

    def handle(self, *args, **options):

        cad_stats = reports.models.ContentAdStats.objects.aggregate(
            impressions=Sum('impressions'),
            clicks=Sum('clicks'),
            cost_cc=Sum('cost_cc'),
            data_cost_cc=Sum('data_cost_cc')
        )

        cad_post_stats = reports.models.ContentAdPostclickStats.objects.aggregate(
            visits=Sum('visits'),
            new_visits=Sum('new_visits'),
            bounced_visits=Sum('bounced_visits'),
            pageviews=Sum('pageviews'),
            total_time_on_site=Sum('total_time_on_site'),
        )

        ds_stats = reports.models.BudgetDailyStatement.objects.aggregaet(
            effective_cost_nano=Sum('media_spend_nano'),
            effective_data_cost_nano=Sum('data_spend_nano'),
            license_fee_nano=Sum('license_fee_nano')
        )

        redshift_sums = redshift.sum_of_stats()

        self._post_metrics('reports.contentadstats', cad_stats, redshift_sums)
        self._post_metrics('reports.contentadstats', cad_post_stats, redshift_sums)
        self._post_metrics('reports.daily_statements', ds_stats, redshift_sums)
