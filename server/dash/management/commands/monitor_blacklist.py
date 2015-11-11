import datetime
import logging

from django.core.management.base import BaseCommand

import reports.api_publishers
import dash.constants
import dash.models

from utils import statsd_helper

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Monitor publisher blacklisting.')

        impressions, clicks = 0, 0
        cost, cpc, ctr = 0, 0, 0

        BATCH_SIZE = 50
        batch = []

        before_yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=2)

        today = datetime.date.today()

        for blacklist_entry in dash.models.PublisherBlacklist.objects.filter(
            created_dt__lte=before_yesterday,
            status=dash.constants.PublisherStatus.BLACKLISTED):
            # fetch blacklisted status from db
            batch.append({
                'domain': blacklist_entry.name,
                'adgroup_id': blacklist_entry.ad_group.id,
                'exchange': blacklist_entry.source.tracking_slug.replace('b1_', ''),
            })

            if len(batch) > BATCH_SIZE:
                for entry in batch:
                    totals_data = reports.api_publishers.query_blacklisted_publishers(
                        datetime.datetime.combine(today, datetime.time.min),
                        datetime.datetime.combine(today, datetime.time.max),
                        blacklist=batch
                    )
                    clicks += totals_data['clicks']
                    impressions += totals_data['impressions']
                    cost += totals_data['cost']
                    ctr += totals_data['ctr']
                    cpc += totals_data['cpc']
                batch = []

        if len(batch) > 0:
            for entry in batch:
                totals_data = reports.api_publishers.query_blacklisted_publishers(
                    datetime.datetime.combine(today, datetime.time.min),
                    datetime.datetime.combine(today, datetime.time.max),
                    blacklist=batch
                )
                clicks += totals_data['clicks']
                impressions += totals_data['impressions']
                cost += totals_data['cost']
                ctr += totals_data['ctr']
                cpc += totals_data['cpc']

        logger.info('Blacklisting summary at {dt}: {blob}'.format(
            dt=datetime.datetime.utcnow().isoformat(),
            blob={
                'clicks': clicks,
                'impressions': impressions,
                'cost': cost,
                'cpc': cpc,
                'ctr': ctr,
            }
        ))

        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.clicks', clicks)
        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.impressions', impressions)
        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.cost', cost)
        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.ctr', ctr)
        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.cpc', cpc)



