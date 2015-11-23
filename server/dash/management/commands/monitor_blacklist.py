import datetime
import logging

from django.core.management.base import BaseCommand

import reports.api_publishers
import dash.constants
import dash.models

from utils import statsd_helper

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    @statsd_helper.statsd_timer('dash.commands', 'monitor_blacklist')
    def handle(self, *args, **options):
        logger.info('Monitor publisher blacklisting.')

        impressions, clicks = 0, 0
        cost, cpc, ctr = 0, 0, 0

        BATCH_SIZE = 50
        batch = []

        blacklisted_before = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        no_stats_after = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        processed = 0

        for blacklist_entry in dash.models.PublisherBlacklist.objects.filter(
            created_dt__lte=blacklisted_before,
            status=dash.constants.PublisherStatus.BLACKLISTED):
            if blacklist_entry.ad_group is None:
                continue
            # fetch blacklisted status from db
            batch.append({
                'domain': blacklist_entry.name,
                'adgroup_id': blacklist_entry.ad_group.id,
                'exchange': blacklist_entry.source.tracking_slug.replace('b1_', ''),
            })

            if len(batch) >= BATCH_SIZE:
                totals_data = reports.api_publishers.query_blacklisted_publishers(
                    no_stats_after.date(),
                    datetime.datetime.utcnow().date(),
                    blacklist=batch,
                )
                clicks += totals_data.get('clicks', 0) or 0
                impressions += totals_data.get('impressions', 0) or 0
                cost += totals_data.get('cost', 0) or 0
                ctr += totals_data.get('ctr', 0) or 0
                cpc += totals_data.get('cpc', 0) or 0
                processed += BATCH_SIZE
                print "Processed blacklist entries", processed
                logger.info("Processed %d blacklist entries", processed)
                batch = []

        if len(batch) > 0:
            totals_data = reports.api_publishers.query_blacklisted_publishers(
                no_stats_after.date(),
                datetime.datetime.utcnow().date(),
                blacklist=batch
            )
            clicks += totals_data.get('clicks', 0) or 0
            impressions += totals_data.get('impressions', 0) or 0
            cost += totals_data.get('cost', 0) or 0
            ctr += totals_data.get('ctr', 0) or 0
            cpc += totals_data.get('cpc', 0) or 0

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

        # monitor PENDING publisherblacklist entries
        count_pending = dash.models.PublisherBlacklist.objects.filter(
            status=dash.constants.PublisherStatus.PENDING
        ).count()
        statsd_helper.statsd_gauge('dash.blacklisted_publisher.pending', count_pending)
        count_blacklisted = dash.models.PublisherBlacklist.objects.filter(
            status=dash.constants.PublisherStatus.BLACKLISTED
        ).count()
        statsd_helper.statsd_gauge('dash.blacklisted_publisher.blacklisted', count_blacklisted)
