import backtosql
import collections
import datetime
import dateutil.parser
import logging

from utils.command_helpers import ExceptionCommand

from dash import constants
from dash import models
from dash import publisher_helpers
from dash import publisher_group_helpers

import redshiftapi.db

from utils import list_helper

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Monitor whitelisted and blacklisted publishers by checking for publisher statistics in Redshift that should not exist."

    def add_arguments(self, parser):
        parser.add_argument(
            '--date_from',
            help='Iso formatted date. All publisher group entries after this date will be ignored')
        parser.add_argument(
            '--date_to',
            help='Iso formatted date. Date to which stats should be checked')
        parser.add_argument(
            '--ad_group_ids',
            help='Comma separated ad group ids')

    def handle(self, *args, **options):
        logger.info('Monitor publisher whitelisting and blacklisting.')

        date_from = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        if options.get('date_from') is not None:
            date_from = dateutil.parser.parse(options['date_from']).date()

        date_to = datetime.datetime.utcnow().date()
        if options.get('date_to') is not None:
            date_to = dateutil.parser.parse(options['date_to']).date()

        ad_groups = models.AdGroup.objects.all().exclude_archived().filter_running()
        if options.get('ad_group_ids') is not None:
            ad_group_ids = [int(x.strip()) for x in options['ad_group_ids'].split(',')]
            ad_groups = models.AdGroup.objects.filter(pk__in=ad_group_ids)

        publishers_map = self.get_publishers_map(date_from)
        stats_map = self.get_stats(date_from, date_to, ad_groups)

        self.check_ad_groups(ad_groups, publishers_map, stats_map)

    def check_ad_groups(self, ad_groups, publishers_map, stats_map):
        # load necessary objects
        ad_groups = ad_groups.select_related('campaign', 'campaign__account')
        campaigns = models.Campaign.objects.filter(pk__in=ad_groups.values_list('campaign_id', flat=True))
        accounts = models.Account.objects.filter(pk__in=campaigns.values_list('account_id', flat=True))
        ad_group_settings_map = {x.ad_group_id: x for x in models.AdGroupSettings.objects.filter(ad_group__in=ad_groups).group_current_settings()}
        campaign_settings_map = {x.campaign_id: x for x in models.CampaignSettings.objects.filter(campaign__in=campaigns).group_current_settings()}
        account_settings_map = {x.account_id: x for x in models.AccountSettings.objects.filter(account__in=accounts).group_current_settings()}

        outbrain = models.Source.objects.get(source_type__type=constants.SourceType.OUTBRAIN)

        for ad_group in ad_groups:
            blacklist, whitelist = publisher_group_helpers.concat_publisher_group_targeting(
                ad_group, ad_group_settings_map[ad_group.id],
                ad_group.campaign, campaign_settings_map[ad_group.campaign_id],
                ad_group.campaign.account, account_settings_map[ad_group.campaign.account_id],
                include_global=True)

            blacklisted_publisher_ids = set(list_helper.flatten(publishers_map[x] for x in blacklist))
            whitelisted_publisher_ids = set(list_helper.flatten(publishers_map[x] for x in whitelist))

            traffic_publisher_ids = stats_map.get(ad_group.id, set())
            traffic_publisher_ids_wo_outbrain = set(
                x for x in traffic_publisher_ids if publisher_helpers.dissect_publisher_id(x)[1] != outbrain.id)
            traffic_publisher_ids_outbrain = set(
                x for x in traffic_publisher_ids if publisher_helpers.dissect_publisher_id(x)[1] == outbrain.id)

            if whitelisted_publisher_ids:
                # all publishers with traffic should be within whitelisted publisher ids
                # whitelisted publishers are those that are on whitelist but not on blacklist

                violator_publisher_ids = self.get_whitelist_violators(
                    traffic_publisher_ids_wo_outbrain, whitelisted_publisher_ids, blacklisted_publisher_ids)
                if violator_publisher_ids:
                    logger.warning(
                        'publisher_group_monitor: Found publisher statistics for whitelisted publishers in ad group %s',
                        ad_group.id, extra={'publisher_ids': violator_publisher_ids})

                # outbrain doesn't support whitelisting so just don't check

            if blacklisted_publisher_ids:
                # there should be no traffic from blacklisted publishers

                violator_publisher_ids = self.get_blacklist_violators(
                    traffic_publisher_ids_wo_outbrain, blacklisted_publisher_ids)
                if violator_publisher_ids:
                    logger.warning(
                        'publisher_group_monitor: Found publisher statistics for blacklisted publishers in ad group %s',
                        ad_group.id, extra={'publisher_ids': violator_publisher_ids})

                if len(set(x for x in blacklisted_publisher_ids if publisher_helpers.dissect_publisher_id(x)[1] == outbrain.id)) < 30:
                    # outbrain - skip check when more than 30 blacklisted outbrain publishers as we are probably waiting for
                    # a manual action

                    violator_publisher_ids = self.get_blacklist_violators(
                        traffic_publisher_ids_outbrain, blacklisted_publisher_ids)
                    if violator_publisher_ids:
                        logger.warning(
                            'publisher_group_monitor: Found Outbrain publisher statistics for blacklisted publishers in ad group %s',
                            ad_group.id, extra={'publisher_ids': violator_publisher_ids})

    def get_whitelist_violators(self, publisher_ids, whitelisted_publisher_ids, blacklisted_publisher_ids):
        return publisher_ids - (whitelisted_publisher_ids - blacklisted_publisher_ids)

    def get_blacklist_violators(self, publisher_ids, blacklisted_publisher_ids):
        return publisher_ids.intersection(blacklisted_publisher_ids)

    def get_stats(self, date_from, date_to, ad_groups):
        params = {
            'date_from': date_from,
            'date_to': date_to,
            'ad_group_id': list(ad_groups.values_list('pk', flat=True)),
        }

        sql = backtosql.generate_sql('etl_get_publishers_with_traffic.sql', None)

        with redshiftapi.db.get_stats_cursor() as cursor:
            cursor.execute(sql, params)
            results = redshiftapi.db.dictfetchall(cursor)

        m = collections.defaultdict(set)
        for row in results:
            m[row['ad_group_id']].add(row['publisher_id'])

        return m

    def get_publishers_map(self, listed_before):
        """
        Get publisher ids for each publisher group
        """

        source_ids = models.Source.objects.all().values_list('pk', flat=True)

        publishers_map = {}
        for publisher_group in models.PublisherGroup.objects.all():
            publisher_ids = publisher_group.entries.all()\
                                                   .filter(created_dt__lte=listed_before)\
                                                   .annotate_publisher_id()\
                                                   .values_list('publisher_id', flat=True)

            # when source is not defined create publisher id for each source so that its easier to compare
            # with recorded data that always has a source id.
            publisher_ids = list_helper.flatten(
                publisher_helpers.inflate_publisher_id_source(x, source_ids) for x in publisher_ids)
            publisher_ids = set(publisher_ids)

            publishers_map[publisher_group.id] = publisher_ids

        return publishers_map
