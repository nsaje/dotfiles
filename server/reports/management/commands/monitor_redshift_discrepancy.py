import re

from django.db.models import Sum

import reports.models
from reports import redshift

from utils.command_helpers import ExceptionCommand
from utils.statsd_helper import statsd_gauge


class Command(ExceptionCommand):

    def _post_metrics(self, prefix, stats, redshift_sums):
        for stats_key, stats_val in stats.iteritems():
            redshift_stats_val = redshift_sums[stats_key]
            if stats_key.endswith('_nano'):
                stats_key = re.sub(r'_nano$', '', stats_key)
                stats_val = float(stats_val) / 10**9
                redshift_stats_val = float(redshift_stats_val) / 10**9

            cads_total_name = '{prefix}.{stat_name}_total'.format(
                prefix=prefix,
                stat_name=stats_key
            )

            statsd_gauge(cads_total_name, stats_val)

            redshift_stats_name = '{prefix}.{stat_name}_total_aggr'.format(
                prefix=prefix,
                stat_name=stats_key
            )
            statsd_gauge(redshift_stats_name, redshift_stats_val)

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

        ds_stats = reports.models.BudgetDailyStatement.objects.aggregate(
            effective_cost_nano=Sum('media_spend_nano'),
            effective_data_cost_nano=Sum('data_spend_nano'),
            license_fee_nano=Sum('license_fee_nano')
        )

        rs_sums = redshift.sum_of_stats()
        rs_sums_with_diffs = redshift.sum_of_stats(with_diffs=True)

        self._post_metrics('reports.contentadstats', cad_stats, rs_sums)
        self._post_metrics('reports.contentadstats', cad_post_stats, rs_sums)
        self._post_metrics('reports.daily_statements', ds_stats, rs_sums_with_diffs)
