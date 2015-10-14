from django.core.management.base import BaseCommand
from django.db.models import Sum

import reports.models
from reports import redshift

from utils.statsd_helper import statsd_gauge


class Command(BaseCommand):

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

        redshift_sums = redshift.sum_of_stats()

        stats_field_keys = cad_stats.keys()
        for stats_field_key in stats_field_keys:
            prefix = 'reports.contentadstats'
            cads_total_name = '{prefix}.{stat_name}_total'.format(
                prefix=prefix,
                stat_name=stats_field_key
            )
            statsd_gauge(cads_total_name, cad_stats.get(stats_field_key, 0))

            cads_redshift_name = '{prefix}.{stat_name}_total_aggr'.format(
                prefix=prefix,
                stat_name=stats_field_key
            )
            statsd_gauge(cads_redshift_name, redshift_sums[stats_field_key])

        post_stats_field_keys = cad_post_stats.keys()
        for post_stats_field_key in post_stats_field_keys:
            prefix = 'reports.contentadstats'
            cads_total_name = '{prefix}.{stat_name}_total'.format(
                prefix=prefix,
                stat_name=post_stats_field_key
            )
            statsd_gauge(cads_total_name, cad_post_stats.get(post_stats_field_key, 0))

            cads_redshift_name = '{prefix}.{stat_name}_total_aggr'.format(
                prefix=prefix,
                stat_name=post_stats_field_key
            )
            statsd_gauge(cads_redshift_name, redshift_sums[post_stats_field_key])
