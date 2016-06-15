import backtosql
from collections import defaultdict
import json
import logging

import dash.models
import dash.constants

from redshiftapi import db
from utils import converters

from etl import models
from etl import helpers
from etl import materialize_helpers


logger = logging.getLogger(__name__)


class MVHelpersSource(materialize_helpers.TempTableMixin, materialize_helpers.MaterializeViaCSV):
    """
    Helper view that puts source id and slug into redshift. Its than used to construct the mv_master view.
    """

    def table_name(self):
        return 'mvh_source'

    def generate_rows(self, cursor, date_from, date_to, **kwargs):
        sources = dash.models.Source.objects.all()

        for source in sources:
            yield (
                source.id,
                helpers.extract_source_slug(source.bidder_slug),
                source.bidder_slug,
            )

    def create_table_template_name(self):
        return 'etl_create_table_mvh_source.sql'


class MVHelpersCampaignFactors(materialize_helpers.TempTableMixin, materialize_helpers.MaterializeViaCSV):
    """
    Helper view that puts campaign factors into redshift. Its than used to construct the mv_master view.
    """

    def table_name(self):
        return 'mvh_campaign_factors'

    def generate_rows(self, cursor, date_from, date_to, campaign_factors, **kwargs):
        for date, campaign_dict in campaign_factors.iteritems():
            for campaign, factors in campaign_dict.iteritems():
                yield (
                    date,
                    campaign.id,

                    factors[0],
                    factors[1],
                )

    def create_table_template_name(self):
        return 'etl_create_table_mvh_campaign_factors.sql'


class MVHelpersAdGroupStructure(materialize_helpers.TempTableMixin, materialize_helpers.MaterializeViaCSV):
    """
    Helper view that puts ad group structure (campaign id, account id, agency id) into redshift. Its than
    used to construct the mv_master view.
    """

    def table_name(self):
        return 'mvh_adgroup_structure'

    def generate_rows(self, cursor, date_from, date_to, **kwargs):
        ad_groups = dash.models.AdGroup.objects.select_related('campaign', 'campaign__account').all()

        for ad_group in ad_groups:
            yield (
                ad_group.campaign.account.agency_id,
                ad_group.campaign.account_id,
                ad_group.campaign_id,
                ad_group.id,
            )

    def create_table_template_name(self):
        return 'etl_create_table_mvh_adgroup_structure.sql'


class MVHelpersNormalizedStats(materialize_helpers.TempTableMixin, materialize_helpers.Materialize):
    """
    Writes a temporary table that has data from stats transformed into the correct format for mv_master construction.
    It does conversion from age, gender etc. strings to constatnts, calculates nano, calculates effective cost and license
    fee based on mvh_campaign_factors.
    """

    def table_name(self):
        return 'mvh_clean_stats'

    def prepare_insert_query(self, date_from, date_to, **kwargs):
        params = helpers.get_local_multiday_date_context(date_from, date_to)

        sql = backtosql.generate_sql('etl_insert_mvh_clean_stats.sql', {
            'date_ranges': params.pop('date_ranges'),
        })

        return sql, params

    def create_table_template_name(self):
        return 'etl_create_table_mvh_clean_stats.sql'


class MasterView(materialize_helpers.MaterializeViaCSVDaily):
    """
    Represents breakdown by all dimensions available. It containts traffic, postclick, conversions
    and tochpoint conversions data.

    NOTE: It excludes outbrain publishers as those are currently not linked to content ads and so
    breakdown by publisher and content ad is not possible for them.
    """

    def table_name(self):
        return 'mv_master'

    def insert_data(self, cursor, date_from, date_to, campaign_factors, **kwargs):
        self._prefetch()

        self._execute_insert_stats_into_mv_master(cursor)

        breakdown_keys_with_traffic = self._get_breakdowns_with_traffic_results(cursor, date_from, date_to)

        super(MasterView, self).insert_data(
            cursor, date_from, date_to, campaign_factors,
            breakdown_keys_with_traffic=breakdown_keys_with_traffic,
            **kwargs)

    def _prefetch(self):
        self.ad_groups_map = {x.id: x for x in dash.models.AdGroup.objects.all()}
        self.campaigns_map = {x.id: x for x in dash.models.Campaign.objects.all()}
        self.accounts_map = {x.id: x for x in dash.models.Account.objects.all()}
        self.sources_slug_map = {
            helpers.extract_source_slug(x.bidder_slug): x for x in dash.models.Source.objects.all()}
        self.sources_map = {x.id: x for x in dash.models.Source.objects.all()}

    def generate_rows(self, cursor, date, breakdown_keys_with_traffic, **kwargs):
        skipped_postclick_stats = set()

        breakdown_keys_with_traffic = breakdown_keys_with_traffic.get(date, {})

        for breakdown_key, row in self._get_postclickstats(cursor, date):
            # only return those rows for which we have traffic - click
            if breakdown_key in breakdown_keys_with_traffic:
                yield row
            else:
                skipped_postclick_stats.add(breakdown_key)

        skipped_tpconversions = set()

        for breakdown_key, row in self._get_touchpoint_conversions(cursor, date):
            # only return those rows for which we have traffic - click
            if breakdown_key in breakdown_keys_with_traffic:
                yield row
            else:
                skipped_tpconversions.add(breakdown_key)

        if skipped_postclick_stats:
            logger.info('MasterView: Couldn\'t join the following postclick stats: %s', skipped_postclick_stats)

        if skipped_tpconversions:
            logger.info(
                'MasterView: Couldn\'t join the following touchpoint conversions stats: %s', skipped_tpconversions)

    def _get_postclickstats(self, cursor, date):

        # group postclick rows by ad group and postclick source
        rows_by_ad_group = defaultdict(lambda: defaultdict(list))
        for row in self._get_postclickstats_query_results(cursor, date):
            postclick_source = helpers.extract_postclick_source(row.postclick_source)
            rows_by_ad_group[row.ad_group_id][postclick_source].append(row)

        for ad_group_id, rows_by_postclick_source in rows_by_ad_group.iteritems():

            if len(rows_by_postclick_source.keys()) > 1:
                logger.warning("Postclick stats for a single ad group (%s) from different sources %s, date %s",
                               ad_group_id, rows_by_postclick_source.keys(), date)

            rows = helpers.get_highest_priority_postclick_source(rows_by_postclick_source)

            for row in rows:
                source_slug = helpers.extract_source_slug(row.source_slug)
                if source_slug not in self.sources_slug_map:
                    logger.warning("Got postclick stats for unknown source: %s", row.source_slug)
                    continue

                if row.ad_group_id not in self.ad_groups_map:
                    logger.warning("Got postclick stats for unknown ad group: %s", row.ad_group_id)
                    continue

                source = self.sources_slug_map[source_slug]
                ad_group = self.ad_groups_map[row.ad_group_id]
                campaign = self.campaigns_map[ad_group.campaign_id]
                account = self.accounts_map[campaign.account_id]

                yield helpers.get_breakdown_key_for_postclickstats(source.id, row.content_ad_id), (
                    date,
                    source.id,

                    account.agency_id,
                    account.id,
                    campaign.id,
                    ad_group.id,
                    row.content_ad_id,
                    row.publisher,

                    dash.constants.DeviceType.UNDEFINED,
                    None,
                    None,
                    None,
                    dash.constants.AgeGroup.UNDEFINED,
                    dash.constants.Gender.UNDEFINED,
                    dash.constants.AgeGenderGroup.UNDEFINED,

                    0,
                    0,
                    0,
                    0,

                    row.visits,
                    row.new_visits,
                    row.bounced_visits,
                    row.pageviews,
                    row.total_time_on_site,

                    0,
                    0,
                    0,

                    row.conversions,
                    None,
                )

    def _get_touchpoint_conversions(self, cursor, date):

        conversions_breakdown = helpers.construct_touchpoint_conversions_dict(
            self._get_touchpoint_conversions_query_results(cursor, date))

        for breakdown_key, conversions in conversions_breakdown.iteritems():
            ad_group_id, content_ad_id, source_id, publisher = breakdown_key

            if source_id not in self.sources_map:
                logger.warning("Got conversion for unknown media source: %s", source_id)
                continue

            if ad_group_id not in self.ad_groups_map:
                logger.warning("Got conversion for unknown ad group: %s", ad_group_id)
                continue

            ad_group = self.ad_groups_map[ad_group_id]
            campaign = self.campaigns_map[ad_group.campaign_id]
            account = self.accounts_map[campaign.account_id]

            yield helpers.get_breakdown_key_for_postclickstats(source_id, content_ad_id), (
                date,
                source_id,

                account.agency_id,
                account.id,
                campaign.id,
                ad_group.id,
                content_ad_id,
                publisher,

                dash.constants.DeviceType.UNDEFINED,
                None,
                None,
                None,
                dash.constants.AgeGroup.UNDEFINED,
                dash.constants.Gender.UNDEFINED,
                dash.constants.AgeGenderGroup.UNDEFINED,

                0,
                0,
                0,
                0,

                0,
                0,
                0,
                0,
                0,

                0,
                0,
                0,

                None,
                json.dumps(conversions),
            )

    @classmethod
    def _execute_insert_stats_into_mv_master(cls, c):
        sql, params = cls._prepare_insert_stats_query()
        c.execute(sql, params)

    @classmethod
    def _prepare_insert_stats_query(cls):
        # NOTE: mvh_clean_stats includes only data from the selected date range
        # so no constraints are necessary
        return backtosql.generate_sql('etl_insert_mv_master_stats.sql', {}), {}

    @classmethod
    def _get_breakdowns_with_traffic_results(cls, c, date_from, date_to):
        sql, params = cls._prepare_get_breakdowns_with_traffic(date_from, date_to)
        c.execute(sql, params)

        breakdown_keys = defaultdict(set)
        for row in db.xnamedtuplefetchall(c):
            breakdown_keys[row.date].add(helpers.get_breakdown_key_for_postclickstats(row.source_id, row.content_ad_id))

        return breakdown_keys

    @classmethod
    def _prepare_get_breakdowns_with_traffic(cls, date_from, date_to):
        return backtosql.generate_sql('etl_select_breakdown_keys_with_traffic.sql', {}), {
            'date_from': date_from,
            'date_to': date_to,
        }

    @classmethod
    def _get_postclickstats_query_results(cls, c, date):
        sql, params = cls._prepare_postclickstats_query(date)

        c.execute(sql, params)
        return db.xnamedtuplefetchall(c)

    @classmethod
    def _prepare_postclickstats_query(cls, date):
        sql = backtosql.generate_sql('etl_breakdown_simple_one_day.sql', {
            'breakdown': models.K1PostclickStats.get_breakdown([
                'ad_group_id', 'postclick_source', 'content_ad_id', 'source_slug', 'publisher',
            ]),
            'aggregates': models.K1PostclickStats.get_aggregates(),
            'table': 'postclickstats'
        })

        params = {'date': date}

        return sql, params

    @classmethod
    def _get_touchpoint_conversions_query_results(cls, c, date):
        sql, params = cls._prepare_touchpoint_conversions_query(date)

        c.execute(sql, params)
        return db.xnamedtuplefetchall(c)

    @classmethod
    def _prepare_touchpoint_conversions_query(cls, date):
        sql = backtosql.generate_sql('etl_breakdown_simple_one_day.sql', {
            'breakdown': models.K1Conversions.get_breakdown([
                'ad_group_id', 'content_ad_id', 'source_id', 'publisher', 'slug', 'conversion_window'
            ]),
            'aggregates': models.K1Conversions.select_columns(subset=['count']),
            'table': 'conversions',
        })

        params = {'date': date}

        return sql, params


class MVAccount(materialize_helpers.Materialize):

    def table_name(self):
        return 'mv_account'

    def prepare_insert_query(self, date_from, date_to, **kwargs):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster.get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id',
            ]),
            'aggregates': models.MVMaster.get_ordered_aggregates(),
            'destination_table': self.table_name(),
            'source_table': 'mv_master',
        })

        return sql, {
            'date_from': date_from,
            'date_to': date_to,
        }


class MVAccountDelivery(materialize_helpers.Materialize):

    def table_name(self):
        return 'mv_account_delivery'

    def prepare_insert_query(self, date_from, date_to, **kwargs):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster.get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id',
                'device_type', 'country', 'state', 'dma', 'age', 'gender', 'age_gender',
            ]),
            'aggregates': models.MVMaster.get_ordered_aggregates(),
            'destination_table': self.table_name(),
            'source_table': 'mv_master',
        })

        return sql, {
            'date_from': date_from,
            'date_to': date_to,
        }
