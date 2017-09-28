import collections
import datetime
import logging

import dateutil.parser
import influx

import backtosql
from utils.command_helpers import ExceptionCommand
from dash import constants
from dash import models
from dash import publisher_helpers
from core.publisher_groups import publisher_group_helpers
import redshiftapi.db
from utils import list_helper
from utils import slack

logger = logging.getLogger(__name__)

OEN = 305


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
        parser.add_argument('--no-influx', action='store_true', help='Do not log to influx')
        parser.add_argument('--no-slack', action='store_true', help='Do not log to slack')
        parser.add_argument('--include-oen', action='store_true', help='Include OEN')

    def handle(self, *args, **options):
        logger.info('Monitor publisher whitelisting and blacklisting.')

        date_from = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        if options.get('date_from') is not None:
            date_from = dateutil.parser.parse(options['date_from']).date()

        date_to = datetime.datetime.utcnow().date()
        if options.get('date_to') is not None:
            date_to = dateutil.parser.parse(options['date_to']).date()

        ad_groups = models.AdGroup.objects.all().exclude_archived().filter_running()
        if not options['include_oen']:
            ad_groups = ad_groups.exclude(
                campaign__account__id=OEN,
            )
        if options.get('ad_group_ids') is not None:
            ad_group_ids = [int(x.strip()) for x in options['ad_group_ids'].split(',')]
            ad_groups = models.AdGroup.objects.filter(pk__in=ad_group_ids)

        publishers_map = self.get_publishers_map(date_from)
        stats_map = self.get_stats(date_from, date_to, ad_groups)

        self.check_ad_groups(
            ad_groups=ad_groups,
            publishers_map=publishers_map,
            stats_map=stats_map,
            date_from=date_from,
            log_influx=not options['no_influx'],
            log_slack=not options['no_slack'],
        )

    def check_ad_groups(self, ad_groups, publishers_map, stats_map, date_from, log_influx=True, log_slack=True):
        # load necessary objects
        ad_groups = ad_groups.select_related('campaign', 'campaign__account')
        campaigns = models.Campaign.objects.filter(pk__in=ad_groups.values_list('campaign_id', flat=True))
        accounts = models.Account.objects.filter(pk__in=campaigns.values_list('account_id', flat=True))
        ad_group_settings_map = {x.ad_group_id: x for x in models.AdGroupSettings.objects.filter(
            ad_group__in=ad_groups).group_current_settings()}
        campaign_settings_map = {x.campaign_id: x for x in models.CampaignSettings.objects.filter(
            campaign__in=campaigns).group_current_settings()}
        account_settings_map = {x.account_id: x for x in models.AccountSettings.objects.filter(
            account__in=accounts).group_current_settings()}

        outbrain = models.Source.objects.get(source_type__type=constants.SourceType.OUTBRAIN)

        overall_blacklisted_entry_ids = set()
        overall_whitelisted_entry_ids = set()
        overall_vialotors_stats = {'clicks': 0, 'impressions': 0}

        for ad_group in ad_groups:
            blacklist, whitelist = publisher_group_helpers.concat_publisher_group_targeting(
                ad_group, ad_group_settings_map[ad_group.id],
                ad_group.campaign, campaign_settings_map[ad_group.campaign_id],
                ad_group.campaign.account, account_settings_map[ad_group.campaign.account_id],
                include_global=True)

            blacklisted_publishers = set(list_helper.flatten(publishers_map[x] for x in blacklist))
            whitelisted_publishers = set(list_helper.flatten(publishers_map[x] for x in whitelist))

            # filter out recently blacklisted, because we can still have some data for blacklisted
            overall_blacklisted_entry_ids |= set(models.PublisherGroupEntry.objects
                                                 .filter(publisher_group_id__in=blacklist)
                                                 .filter(modified_dt__lt=date_from)
                                                 .values_list('id', flat=True))
            # do not filter out recent, because we can already have some data for whitelisted
            overall_whitelisted_entry_ids |= set(models.PublisherGroupEntry.objects
                                                 .filter(publisher_group_id__in=whitelist)
                                                 .values_list('id', flat=True))

            ad_group_stats = stats_map.get(ad_group.id, {})
            ad_group_violators = set()

            # remove triplelift NA as it gets in there sometimes
            traffic_publisher_ids = set(ad_group_stats.keys()) - {'na__34'}
            traffic_publisher_ids_wo_outbrain = set(
                x for x in traffic_publisher_ids if publisher_helpers.dissect_publisher_id(x)[1] != outbrain.id)
            traffic_publisher_ids_outbrain = set(
                x for x in traffic_publisher_ids if publisher_helpers.dissect_publisher_id(x)[1] == outbrain.id)

            if whitelisted_publishers:
                # all publishers with traffic should be within whitelisted publisher ids
                # whitelisted publishers are those that are on whitelist but not on blacklist

                violator_publisher_ids = self.get_whitelist_violators(
                    traffic_publisher_ids_wo_outbrain, whitelisted_publishers, blacklisted_publishers)
                if violator_publisher_ids:
                    message = 'Found publisher statistics in ad group {ad_group_id} for non-whitelisted publishers: {publisher_ids}'.format(
                        ad_group_id=ad_group.id,
                        publisher_ids=', '.join(violator_publisher_ids),
                    )
                    logger.info(message)
                    if log_slack:
                        slack.publish(
                            message,
                            channel='z1-monitor-blacklist',
                        )

                    ad_group_violators |= violator_publisher_ids

                # outbrain doesn't support whitelisting so just don't check

            if blacklisted_publishers:
                # there should be no traffic from blacklisted publishers

                violator_publisher_ids = self.get_blacklist_violators(
                    traffic_publisher_ids_wo_outbrain, blacklisted_publishers)
                if violator_publisher_ids:
                    message = 'Found publisher statistics in ad group {ad_group_id} for blacklisted publishers: {publisher_ids}'.format(
                        ad_group_id=ad_group.id,
                        publisher_ids=', '.join(violator_publisher_ids),
                    )
                    logger.info(message)
                    if log_slack:
                        slack.publish(
                            message,
                            channel='z1-monitor-blacklist',
                        )

                    ad_group_violators |= violator_publisher_ids

                if len(set(x for x in blacklisted_publishers if x.source_id == outbrain.id)) < 30:
                    # outbrain - skip check when more than 30 blacklisted outbrain publishers as we are probably waiting for
                    # a manual action

                    outbrain_blacklist = [x for x in blacklisted_publishers if x.source_id == outbrain.id]
                    violator_publisher_ids = self.get_blacklist_violators(
                        traffic_publisher_ids_outbrain, outbrain_blacklist)
                    if violator_publisher_ids:
                        message = 'Found Outbrain publisher statistics in ad group {ad_group_id} for blacklisted publishers: {publisher_ids}'.format(
                            ad_group_id=ad_group.id,
                            publisher_ids=', '.join(violator_publisher_ids),
                        )
                        logger.info(message)
                        if log_slack:
                            slack.publish(
                                message,
                                channel='z1-monitor-blacklist',
                            )

                        ad_group_violators |= violator_publisher_ids

            overall_vialotors_stats['clicks'] += sum(ad_group_stats[x]['clicks'] for x in ad_group_violators)
            overall_vialotors_stats['impressions'] += sum(ad_group_stats[x]['impressions'] for x in ad_group_violators)

        logger.info('Blacklisted publisher group entries count %s', len(overall_blacklisted_entry_ids))
        logger.info('Whitelisted publisher group entries count %s', len(overall_whitelisted_entry_ids))
        if log_influx:
            influx.gauge('dash.blacklisted_publisher.status', len(overall_blacklisted_entry_ids), status='blacklisted')
            influx.gauge('dash.blacklisted_publisher.status', len(overall_whitelisted_entry_ids), status='whitelisted')

        logger.info('Overall clicks for violator publishers: %s', overall_vialotors_stats['clicks'])
        logger.info('Overall impressions for violator publishers: %s', overall_vialotors_stats['impressions'])
        if log_influx:
            influx.gauge('dash.blacklisted_publisher.stats', overall_vialotors_stats['clicks'], type='clicks')
            influx.gauge('dash.blacklisted_publisher.stats', overall_vialotors_stats['impressions'], type='impressions')

    def get_whitelist_violators(self, publisher_ids, whitelisted_publishers, blacklisted_publishers):
        whitelist = (whitelisted_publishers - blacklisted_publishers)
        lookup = publisher_helpers.PublisherIdLookupMap(whitelist)
        return set([publisher_id for publisher_id in publisher_ids if publisher_id not in lookup and publisher_id != 'all publishers__4'])

    def get_blacklist_violators(self, publisher_ids, blacklisted_publishers):
        lookup = publisher_helpers.PublisherIdLookupMap(blacklisted_publishers)
        return set([publisher_id for publisher_id in publisher_ids if publisher_id in lookup and publisher_id != 'all publishers__4'])

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

        m = collections.defaultdict(dict)
        for row in results:
            if row['publisher_id'] not in m[row['ad_group_id']]:
                m[row['ad_group_id']][row['publisher_id']] = {
                    'clicks': 0,
                    'impressions': 0,
                }

            m[row['ad_group_id']][row['publisher_id']]['clicks'] += row['clicks']
            m[row['ad_group_id']][row['publisher_id']]['impressions'] += row['impressions']

        return m

    def get_publishers_map(self, listed_before):
        """
        Get publisher ids for each publisher group
        """

        publishers_map = {}

        for publisher_group in models.PublisherGroup.objects.all():
            publishers_map[publisher_group.id] = publisher_group.entries.all().filter(created_dt__lte=listed_before)

        return publishers_map
