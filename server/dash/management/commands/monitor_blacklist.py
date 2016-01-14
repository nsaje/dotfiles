import datetime
import logging
import dateutil.parser

from optparse import make_option
from django.core.management.base import BaseCommand

import reports.api_publishers
import dash.constants
import dash.models

from utils import statsd_helper
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Monitor blacklisted publishers by checking for publisher statistics in Redshift that should not exist."

    option_list = BaseCommand.option_list + (
        make_option(
            '--blacklisted_before',
            help='Iso formatted date. All pub. blacklist entries after this date will be ignored'
        ),
    )

    @statsd_helper.statsd_timer('dash.commands', 'monitor_blacklist')
    def handle(self, *args, **options):
        logger.info('Monitor publisher blacklisting.')

        if options.get('blacklisted_before') is None:
            blacklisted_before = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        else:
            blacklisted_before = dateutil.parser.parse(options['blacklisted_before']).date()

        self.monitor_adgroup_level(blacklisted_before)
        self.monitor_global_level(blacklisted_before)

        # monitor PENDING publisherblacklist entries
        count_pending = dash.models.PublisherBlacklist.objects.filter(
            status=dash.constants.PublisherStatus.PENDING
        ).count()
        statsd_helper.statsd_gauge('dash.blacklisted_publisher.pending', count_pending)
        count_blacklisted = dash.models.PublisherBlacklist.objects.filter(
            status=dash.constants.PublisherStatus.BLACKLISTED
        ).count()
        statsd_helper.statsd_gauge('dash.blacklisted_publisher.blacklisted', count_blacklisted)

    def monitor_adgroup_level(self, blacklisted_before):
        blacklisted_set = self.generate_adgroup_blacklist_hash(blacklisted_before)

        # since we usually only have statistics for yesterday
        # we need to take into account publisher statistics the day before
        # yesterday
        data = reports.api_publishers.query(
            datetime.datetime.utcnow().date() - datetime.timedelta(days=1),
            datetime.datetime.utcnow().date(),
            breakdown_fields=['domain', 'ad_group', 'exchange'],
        )
        # hashmap data
        redshift_stats = {}
        for row in data:
            redshift_stats[(
                row['domain'],
                row['ad_group'],
                row['exchange'].lower(),
            )] = (row['impressions'], row['clicks'])
        # do set intersection
        redshift_stats_keys = set(redshift_stats.keys())

        aggregated_clicks = 0
        aggregated_impressions = 0
        for key in blacklisted_set.intersection(redshift_stats_keys):
            logger.warning(
                'monitor_blacklist: Found publisher statistics for blacklisted publisher %s - stats: %s',
                key,
                redshift_stats[key]
            )
            aggregated_impressions += redshift_stats[key][0]
            aggregated_clicks += redshift_stats[key][1]

        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.impressions', aggregated_impressions)
        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.clicks', aggregated_clicks)

    def monitor_global_level(self, blacklisted_before):
        blacklisted_set = self.generate_global_blacklist_hash(blacklisted_before)

        data = reports.api_publishers.query(
            datetime.datetime.utcnow().date() - datetime.timedelta(days=1),
            datetime.datetime.utcnow().date(),
            breakdown_fields=['domain', 'exchange'],
        )

        # hashmap data
        redshift_stats = {}
        for row in data:
            if row['exchange'].lower() == 'outbrain':
                continue
            existing_impressions, existing_clicks = redshift_stats.get(
                row['domain'],
                (0, 0)
            )
            redshift_stats[(
                row['domain']
            )] = (
                existing_impressions + row['impressions'],
                existing_clicks + row['clicks']
            )

        # do set intersection
        aggregated_clicks = 0
        aggregated_impressions = 0
        redshift_stats_keys = set(redshift_stats.keys())
        for key in blacklisted_set.intersection(redshift_stats_keys):
            logger.warning(
                'monitor_blacklist: Found publisher statistics for globally blacklisted publisher. %s - stats %s',
                key,
                redshift_stats[key]
            )
            aggregated_impressions += redshift_stats[key][0]
            aggregated_clicks += redshift_stats[key][1]
        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.global_impressions', aggregated_impressions)
        statsd_helper.statsd_gauge('dash.blacklisted_publisher_stats.global_clicks', aggregated_clicks)

    def generate_adgroup_blacklist_hash(self, blacklisted_before):
        adgroup_blacklist = set(
            [(pub[0], pub[1], pub[2].replace('b1_', ''),)
             for pub in dash.models.PublisherBlacklist.objects.filter(
                 ad_group__isnull=False,
                 status=dash.constants.PublisherStatus.BLACKLISTED,
                 created_dt__lte=blacklisted_before,
             ).values_list('name', 'ad_group__id', 'source__tracking_slug')]
        )

        campaign_account_blacklist = []
        for pub in dash.models.PublisherBlacklist.objects.filter(
             campaign__isnull=False,
             status=dash.constants.PublisherStatus.BLACKLISTED,
             created_dt__lte=blacklisted_before,
        ).iterator():
            adgroup_ids = dash.models.AdGroup.objects.filter(
                campaign=pub.campaign
            ).values_list('id', flat=True)
            for adgroup_id in adgroup_ids:
                campaign_account_blacklist.append(
                    (
                        pub.name,
                        adgroup_id,
                        pub.source.tracking_slug.replace('b1_', ''),
                    )
                )

        for pub in dash.models.PublisherBlacklist.objects.filter(
             account__isnull=False,
             status=dash.constants.PublisherStatus.BLACKLISTED,
             created_dt__lte=blacklisted_before,
        ).iterator():
            adgroup_ids = dash.models.AdGroup.objects.filter(
                campaign__account=pub.account
            ).values_list('id', flat=True)
            for adgroup_id in adgroup_ids:
                campaign_account_blacklist.append((
                        pub.name,
                        adgroup_id,
                        pub.source.tracking_slug.replace('b1_', ''),
                    ))
        return adgroup_blacklist.union(set(campaign_account_blacklist))

    def generate_global_blacklist_hash(self, blacklisted_before):
        return set(
            [pub.name
             for pub in dash.models.PublisherBlacklist.objects.filter(
                 everywhere=True,
                 status=dash.constants.PublisherStatus.BLACKLISTED,
                 created_dt__lte=blacklisted_before,
             ).iterator()]
        )
