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


class MVAccount(materialize_helpers.Materialize):

    def table_name(self):
        return 'mv_account'

    def prepare_insert_query(self, date_from, date_to):
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

    def prepare_insert_query(self, date_from, date_to):
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


class MasterView(materialize_helpers.TransformAndMaterialize):
    """
    Represents breakdown by all dimensions available. It containts traffic, postclick, conversions
    and tochpoint conversions data.

    NOTE: It excludes outbrain publishers as those are currently not linked to content ads and so
    breakdown by publisher and content ad is not possible for them.
    """

    def table_name(self):
        return 'mv_master'

    def generate_rows(self, date, campaign_factors):
        self._prefetch()

        with db.get_stats_cursor() as c:
            breakdown_keys_with_traffic_stats = set()

            for breakdown_key, row in self._get_stats(c, date, campaign_factors):
                breakdown_keys_with_traffic_stats.add(breakdown_key)
                yield row

            skipped_postclick_stats = set()
            # only return those rows for which we have
            for breakdown_key, row in self._get_postclickstats(c, date):
                if breakdown_key in breakdown_keys_with_traffic_stats:
                    yield row
                else:
                    skipped_postclick_stats.add(breakdown_key)

            skipped_tpconversions = set()
            for breakdown_key, row in self._get_touchpoint_conversions(c, date):
                if breakdown_key in breakdown_keys_with_traffic_stats:
                    yield row
                else:
                    skipped_tpconversions.add(breakdown_key)

            if skipped_postclick_stats:
                logger.info('MasterView: Couldn\'t join the following postclick stats: %s', skipped_postclick_stats)

            if skipped_tpconversions:
                logger.info(
                    'MasterView: Couldn\'t join the following touchpoint conversions stats: %s', skipped_tpconversions)

    def _prefetch(self):
        self.ad_groups_map = {x.id: x for x in dash.models.AdGroup.objects.all()}
        self.campaigns_map = {x.id: x for x in dash.models.Campaign.objects.all()}
        self.accounts_map = {x.id: x for x in dash.models.Account.objects.all()}
        self.sources_slug_map = {
            helpers.extract_source_slug(x.bidder_slug): x for x in dash.models.Source.objects.all()}
        self.sources_map = {x.id: x for x in dash.models.Source.objects.all()}

    def _get_stats(self, cursor, date, campaign_factors):

        for row in self._get_stats_query_results(cursor, date):

            if row.ad_group_id not in self.ad_groups_map:
                logger.warning("Got spend for unknown ad group: %s", row.ad_group_id)
                continue

            source_slug = helpers.extract_source_slug(row.source_slug)
            if source_slug not in self.sources_slug_map:
                logger.warning("Got spend for unknown media source: %s", row.source_slug)
                continue

            ad_group = self.ad_groups_map[row.ad_group_id]
            campaign = self.campaigns_map[ad_group.campaign_id]
            account = self.accounts_map[campaign.account_id]
            source = self.sources_slug_map[source_slug]

            if campaign not in campaign_factors:
                logger.warning("Missing cost factors for campaign %s", campaign.id)
                continue

            effective_cost, effective_data_cost, license_fee = helpers.calculate_effective_cost(
                    row.cost_micro or 0, row.data_cost_micro or 0, campaign_factors[campaign])

            age = helpers.extract_age(row.age)
            gender = helpers.extract_gender(row.gender)

            yield helpers.get_breakdown_key_for_postclickstats(source.id, row.content_ad_id), (
                date,
                source.id,

                account.agency_id,
                account.id,
                campaign.id,
                ad_group.id,
                row.content_ad_id,
                row.publisher,

                helpers.extract_device_type(row.device_type),
                helpers.extract_country(row.country),
                helpers.extract_state(row.state),
                helpers.extract_dma(row.dma),
                age,
                gender,
                helpers.extract_age_gender(age, gender),

                row.impressions,
                row.clicks,
                converters.micro_to_cc(row.cost_micro),
                converters.micro_to_cc(row.data_cost_micro),

                0,
                0,
                0,
                0,
                0,

                converters.decimal_to_int(effective_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(effective_data_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(license_fee * converters.MICRO_TO_NANO),

                None,
                None,
            )

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
    def _get_stats_query_results(cls, cursor, date):
        sql, params = cls._prepare_stats_query(date)

        cursor.execute(sql, params)
        return db.xnamedtuplefetchall(cursor)

    @classmethod
    def _get_postclickstats_query_results(cls, c, date):
        sql, params = cls._prepare_postclickstats_query(date)

        c.execute(sql, params)
        return db.xnamedtuplefetchall(c)

    @classmethod
    def _get_touchpoint_conversions_query_results(cls, c, date):
        sql, params = cls._prepare_touchpoint_conversions_query(date)

        c.execute(sql, params)
        return db.xnamedtuplefetchall(c)

    @classmethod
    def _prepare_stats_query(cls, date):
        sql = backtosql.generate_sql('etl_breakdown_stats_one_day.sql', {
            'breakdown': models.K1Stats.get_breakdown([
                'source_slug', 'ad_group_id', 'content_ad_id', 'publisher',
                'device_type', 'country', 'state', 'dma', 'age', 'gender'
            ]),
            'aggregates': models.K1Stats.get_aggregates(),
        })

        params = helpers.get_local_date_context(date)

        return sql, params

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
