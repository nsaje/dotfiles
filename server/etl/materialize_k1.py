import logging
import json
from collections import defaultdict
from decimal import Decimal
from functools import partial

import dash.models
from utils import converters
from redshiftapi.db import get_write_stats_cursor, get_write_stats_transaction

from etl import helpers
from etl import materialize_views

logger = logging.getLogger(__name__)

POST_CLICK_PRIORITY = {'gaapi': 1, 'ga_mail': 2, 'omniture': 3}


"""
NOTE: This module will be deprecated when contentadstats and related tables are deprecated - when redshiftapi
replaces reports module.
"""


class ContentAdStats(materialize_views.Materialize):
    """
    date, content_ad_id, adgroup_id, source_id
    campaign_id, account_id
    impressions, clicks
    cost_cc, data_cost_cc
    visits, new_visits, bounced_visits, pageviews, total_time_on_site, conversions
    effective_cost_nano, effective_data_cost_nano, license_fee_nano, users
    """

    TABLE_NAME = 'contentadstats'

    def generate(self, campaign_factors):
        for date, daily_campaign_factors in campaign_factors.iteritems():
            with get_write_stats_transaction():
                with get_write_stats_cursor() as c:

                    logger.info('Deleting data from table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = materialize_views.prepare_daily_delete_query(self.TABLE_NAME, date)
                    c.execute(sql, params)

                    s3_path = materialize_views.upload_csv(
                        self.TABLE_NAME,
                        date,
                        self.job_id,
                        partial(self.generate_rows, c, date, daily_campaign_factors)
                    )

                    logger.info('Copying CSV to table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = materialize_views.prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

    def _stats_breakdown(self, date):
        return Breakdown(
            date,
            'stats',
            ['ad_group_id', 'content_ad_id', 'media_source_type', 'media_source'],
            [('impressions', 'sum'), ('clicks', 'sum'), ('spend', 'sum'), ('data_spend', 'sum')],
        )

    def _postclick_stats_breakdown(self, date):
        return Breakdown(
            date,
            'postclickstats',
            ['content_ad_id', 'type', 'source'],
            [('visits', 'sum'), ('new_visits', 'sum'), ('bounced_visits', 'sum'),
             ('pageviews', 'sum'), ('total_time_on_site', 'sum'), ('conversions', 'listagg'),
             ('users', 'sum'), ('returning_users', 'sum')],
        )

    def _get_post_click_data(self, content_ad_postclick, ad_group, content_ad_id, media_source):
        post_click_list = content_ad_postclick.pop((content_ad_id, media_source), None)
        if not post_click_list:
            return {}

        if len(post_click_list) > 1:
            logger.info("Multiple post click statistics for ad group: %s", ad_group.id)
            post_click_list = sorted(post_click_list, key=lambda x: POST_CLICK_PRIORITY.get(x[1], 100))

        post_click = post_click_list[0]

        if len(post_click) < 9:
            raise Exception("Invalid post click row")

        return {
            "visits": post_click[3],
            "new_visits": post_click[4],
            "bounced_visits": post_click[5],
            "pageviews": post_click[6],
            "time_on_site": post_click[7],
            "conversions": json.dumps(_sum_conversion(post_click[1], post_click[8])),
            "users": post_click[9],
        }

    def generate_rows(self, cursor, date, campaign_factors):
        content_ad_postclick = defaultdict(list)
        for row in self._postclick_stats_breakdown(date).rows():
            content_ad_id = row[0]
            media_source = helpers.extract_source_slug(row[2])
            content_ad_postclick[(content_ad_id, media_source)].append(row)

        ad_groups_map = {a.id: a for a in dash.models.AdGroup.objects.all()}
        media_sources_map = {
            s.bidder_slug: s for s in dash.models.Source.objects.all()
        }

        for row in self._stats_breakdown(date).rows():
            content_ad_id = row[1]
            media_source_slug = row[3]

            ad_group = ad_groups_map.get(row[0])
            if ad_group is None:
                logger.error("Got spend for invalid adgroup: %s", row[0])
                continue
            media_source = media_sources_map.get(media_source_slug)
            if media_source is None:
                logger.error("Got spend for invalid media_source: %s", media_source_slug)
                continue

            cost = row[6] or 0
            data_cost = row[7] or 0

            effective_cost, effective_data_cost, license_fee, margin = helpers.calculate_effective_cost(
                cost, data_cost, campaign_factors[ad_group.campaign])

            # merge postclicks
            post_click = self._get_post_click_data(
                content_ad_postclick,
                ad_group,
                content_ad_id,
                helpers.extract_source_slug(media_source_slug)
            )

            yield (
                date,
                content_ad_id,
                ad_group.id,
                media_source.id,

                ad_group.campaign_id,
                ad_group.campaign.account_id,
                row[4],  # impressions
                row[5],  # clicks

                converters.micro_to_cc(cost),
                converters.micro_to_cc(data_cost),

                post_click.get('visits'),
                post_click.get('new_visits'),
                post_click.get('bounced_visits'),
                post_click.get('pageviews'),
                post_click.get('time_on_site'),
                post_click.get('conversions'),

                converters.decimal_to_int(effective_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(effective_data_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(license_fee * converters.MICRO_TO_NANO),
                converters.decimal_to_int(margin * converters.MICRO_TO_NANO),

                post_click.get('users'),
                helpers.calculate_returning_users(post_click.get('users'), post_click.get('new_visits')),
            )

        content_ads_ad_group_map = {x.id: x.ad_group_id for x in dash.models.ContentAd.objects.all()}

        # make a new mapping as from now on we use media_source_slugs that are already extracted
        media_sources_map = {
            helpers.extract_source_slug(s.bidder_slug): s for s in dash.models.Source.objects.all()
        }

        # insert the remaining postclicks
        for content_ad_id, media_source_slug in content_ad_postclick.keys():
            ad_group_id = content_ads_ad_group_map.get(content_ad_id)
            ad_group = ad_groups_map.get(ad_group_id)
            if ad_group is None:
                logger.error("Got postclick data for unknown ad group")
                continue

            media_source = media_sources_map.get(media_source_slug)
            if media_source is None:
                logger.error("Got postclick data for invalid media_source: %s", media_source_slug)
                continue

            post_click = self._get_post_click_data(
                content_ad_postclick,
                ad_group,
                content_ad_id,
                media_source_slug
            )

            yield (
                date,
                content_ad_id,
                ad_group.id,
                media_source.id,

                ad_group.campaign_id,
                ad_group.campaign.account_id,

                0,
                0,
                0,
                0,

                post_click.get('visits'),
                post_click.get('new_visits'),
                post_click.get('bounced_visits'),
                post_click.get('pageviews'),
                post_click.get('time_on_site'),
                post_click.get('conversions'),

                0,
                0,
                0,
                0,

                post_click.get('users'),
                helpers.calculate_returning_users(post_click.get('users'), post_click.get('new_visits')),
            )

        if content_ad_postclick:
            logger.info(
                'Contentadstats: Couldn\'t join the following post click stats: %s', content_ad_postclick.keys())


class Publishers(materialize_views.Materialize):
    """
    date, adgroup_id, exchange,
    domain, external_id,
    clicks, impressions,
    cost_nano, data_cost_nano,
    effective_cost_nano, effective_data_cost_nano, license_fee_nano
    visits, new_visits, bounced_visits, pageviews, total_time_on_site, conversions,
    users
    """

    TABLE_NAME = 'publishers_1'

    def generate(self, campaign_factors):
        for date, daily_campaign_factors in campaign_factors.iteritems():
            with get_write_stats_transaction():
                with get_write_stats_cursor() as c:

                    logger.info('Deleting data from table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = materialize_views.prepare_daily_delete_query(self.TABLE_NAME, date)
                    c.execute(sql, params)

                    s3_path = materialize_views.upload_csv(
                        self.TABLE_NAME,
                        date,
                        self.job_id,
                        partial(self.generate_rows, c, date, daily_campaign_factors)
                    )

                    logger.info('Copying CSV to table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = materialize_views.prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

    def _stats_breakdown(self, date):
        return Breakdown(
            date,
            'stats',
            ['ad_group_id', 'media_source_type', 'media_source', 'publisher'],
            [('impressions', 'sum'), ('clicks', 'sum'), ('spend', 'sum'), ('data_spend', 'sum')],
        )

    def _stats_outbrain_publishers(self, date):
        fields = ['ad_group_id', 'publisher_id', 'publisher_name', 'clicks']
        query = "select {fields} from {table} where date = '{date}'".format(
            fields=', '.join(fields),
            table='outbrainpublisherstats',
            date=date.isoformat()
        )
        return _query_rows(query)

    def _postclick_stats_breakdown(self, date):
        return Breakdown(
            date,
            'postclickstats',
            ['ad_group_id', 'type', 'source', 'lower(publisher)'],
            [('visits', 'sum'), ('new_visits', 'sum'), ('bounced_visits', 'sum'),
             ('pageviews', 'sum'), ('total_time_on_site', 'sum'), ('conversions', 'listagg'),
             ('users', 'sum'), ('returning_users', 'sum')],
        )

    def _outbrain_cpc(self, date):
        query = """
            select ad_group_id, sum(spend), sum(clicks)
            from stats
            where media_source='outbrain' and date='{date}'
            group by ad_group_id
        """.format(
            date=date.isoformat()
        )
        cpcs = {}
        for line in _query_rows(query):
            if line[1] != 0 and line[2] != 0:
                cpcs[line[0]] = Decimal(line[1]) / line[2]

        return cpcs

    def _get_post_click_data(self, content_ad_postclick, ad_group_id, media_source, publisher):
        post_click_list = content_ad_postclick.pop((ad_group_id, media_source, publisher.lower()), None)
        if not post_click_list:
            return {}

        if len(post_click_list) > 1:
            logger.info("Multiple post click statistics for ad group: %s", ad_group_id)
            post_click_list = sorted(post_click_list, key=lambda x: POST_CLICK_PRIORITY.get(x[1], 100))

        post_click = post_click_list[0]
        if len(post_click) < 10:
            raise Exception("Invalid post click row")

        return {
            "visits": post_click[4],
            "new_visits": post_click[5],
            "bounced_visits": post_click[6],
            "pageviews": post_click[7],
            "time_on_site": post_click[8],
            "conversions": json.dumps(_sum_conversion(post_click[1], post_click[9])),
            "users": post_click[10],
        }

    def generate_rows(self, cursor, date, campaign_factors):
        content_ad_postclick = defaultdict(list)
        for row in self._postclick_stats_breakdown(date).rows():
            ad_group_id = row[0]
            media_source = row[2]
            publisher = row[3]
            media_source = helpers.extract_source_slug(media_source)
            content_ad_postclick[(ad_group_id, media_source, publisher)].append(row)

        ad_groups_map = {a.id: a for a in dash.models.AdGroup.objects.all()}

        for row in self._stats_breakdown(date).rows():
            ad_group_id = row[0]
            media_source = row[2]
            publisher = row[3]

            if media_source == 'outbrain':
                # skip outbrain as we import it from another table
                continue

            if not publisher:
                continue

            ad_group = ad_groups_map.get(ad_group_id)
            if ad_group is None:
                logger.error("Got spend for invalid adgroup: %s", ad_group_id)
                continue

            cost = row[6] or 0
            data_cost = row[7] or 0

            effective_cost, effective_data_cost, license_fee, margin = helpers.calculate_effective_cost(
                cost, data_cost, campaign_factors[ad_group.campaign])

            post_click = self._get_post_click_data(content_ad_postclick, ad_group_id, media_source, publisher)

            yield (
                date,
                ad_group_id,
                media_source,
                publisher,
                '',

                row[5],  # clicks
                row[4],  # impressions

                cost * converters.MICRO_TO_NANO,
                data_cost * converters.MICRO_TO_NANO,

                converters.decimal_to_int(effective_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(effective_data_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(license_fee * converters.MICRO_TO_NANO),

                post_click.get('visits'),
                post_click.get('new_visits'),
                post_click.get('bounced_visits'),
                post_click.get('pageviews'),
                post_click.get('time_on_site'),
                post_click.get('conversions'),

                converters.decimal_to_int(margin * converters.MICRO_TO_NANO),

                post_click.get('users'),
                helpers.calculate_returning_users(post_click.get('users'), post_click.get('new_visits')),
            )

        source = dash.models.Source.objects.get(source_type__type=dash.constants.SourceType.OUTBRAIN)
        outbrain_cpcs = self._outbrain_cpc(date)

        for row in self._stats_outbrain_publishers(date):
            ad_group_id = row[0]
            ad_group = ad_groups_map.get(ad_group_id)
            if ad_group is None:
                logger.error("Got spend for invalid adgroup: %s", ad_group_id)
                continue

            clicks = row[3]
            cost = converters.decimal_to_int(outbrain_cpcs.get(ad_group_id, 0) * clicks)
            data_cost = 0

            effective_cost, effective_data_cost, license_fee, margin = helpers.calculate_effective_cost(
                cost, data_cost, campaign_factors[ad_group.campaign])

            media_source = source.tracking_slug
            publisher = row[2]
            post_click = self._get_post_click_data(content_ad_postclick, ad_group_id, media_source, row[1])

            yield (
                date,
                ad_group_id,
                media_source,
                publisher,
                row[1],

                clicks,
                0,

                cost * converters.MICRO_TO_NANO,
                data_cost * converters.MICRO_TO_NANO,

                converters.decimal_to_int(effective_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(effective_data_cost * converters.MICRO_TO_NANO),
                converters.decimal_to_int(license_fee * converters.MICRO_TO_NANO),

                post_click.get('visits'),
                post_click.get('new_visits'),
                post_click.get('bounced_visits'),
                post_click.get('pageviews'),
                post_click.get('time_on_site'),
                post_click.get('conversions'),

                converters.decimal_to_int(margin * converters.MICRO_TO_NANO),

                post_click.get('users'),
                helpers.calculate_returning_users(post_click.get('users'), post_click.get('new_visits')),
            )

        # make a new mapping as from now on we use media_source_slugs that are already extracted
        media_sources_map = {
            helpers.extract_source_slug(s.bidder_slug): s for s in dash.models.Source.objects.all()
        }

        # import the remaining postclickstats
        for ad_group_id, media_source_slug, publisher in content_ad_postclick.keys():
            ad_group = ad_groups_map.get(ad_group_id)
            if ad_group is None:
                logger.error("Got postclick data for unknown ad group")
                continue

            media_source = media_sources_map.get(media_source_slug)
            if media_source is None:
                logger.error("Got postclick data for invalid media_source: %s", media_source_slug)
                continue

            if not publisher:
                continue

            post_click = self._get_post_click_data(
                content_ad_postclick,
                ad_group_id,
                media_source_slug,
                publisher
            )

            yield (
                date,
                ad_group.id,
                media_source.bidder_slug,
                publisher,
                '',  # domain

                0,
                0,

                0,
                0,

                0,
                0,
                0,

                post_click.get('visits'),
                post_click.get('new_visits'),
                post_click.get('bounced_visits'),
                post_click.get('pageviews'),
                post_click.get('time_on_site'),
                post_click.get('conversions'),

                0,

                post_click.get('users'),
                helpers.calculate_returning_users(post_click.get('users'), post_click.get('new_visits')),
            )

        if content_ad_postclick:
            logger.info('Publishers_1: Couldn\'t join the following post click stats: %s', content_ad_postclick.keys())


class TouchpointConversions(materialize_views.Materialize):
    """
    zuid, slug, date, conversion_id, conversion_timestamp, account_id,
    campaign_id, ad_group_id, content_ad_id, source_id,
    touchpoint_id, touchpoint_timestamp, conversion_lag, publisher
    """

    TABLE_NAME = 'touchpointconversions'

    def generate(self, campaign_factors):
        for date, daily_campaign_factors in campaign_factors.iteritems():
            with get_write_stats_transaction():
                with get_write_stats_cursor() as c:
                    s3_path = materialize_views.upload_csv(
                        self.TABLE_NAME,
                        date,
                        self.job_id,
                        partial(self.generate_rows, c, date)
                    )

                    sql, params = materialize_views.prepare_daily_delete_query(self.TABLE_NAME, date)
                    c.execute(sql, params)

                    sql, params = materialize_views.prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

    def generate_rows(self, cursor, date):
        query = """
            select
                zuid, slug, date, conversion_id, conversion_timestamp, account_id,
                campaign_id, ad_group_id, content_ad_id, source_id,
                touchpoint_id, touchpoint_timestamp, conversion_lag, publisher
            from conversions
            where date=%s
        """

        cursor.execute(query, [date])
        for row in cursor:
            yield row


class Breakdown(object):

    def __init__(self, date, table, breakdowns, values):
        self.date = date
        self.table = table
        self.breakdowns = breakdowns
        self.values = values

    def rows(self):
        query = self._get_materialize_query()
        return _query_rows(query)

    def _get_materialize_query(self):
        aggr_values = []
        for field, aggr in self.values:
            if aggr == 'listagg':
                aggr_values.append('{aggr}({field}, \'\n\')'.format(aggr=aggr, field=field))
            else:
                aggr_values.append('{aggr}({field})'.format(aggr=aggr, field=field))

        return """
            select {groups}, {values}
            from {table}
            where {date_query}
            group by {groups}
        """.format(
            groups=', '.join(self.breakdowns),
            values=', '.join(aggr_values),
            table=self.table,
            date_query=self._get_date_query(),
        )

    def _get_date_query(self):
        if self.table == 'stats':
            return helpers.get_local_date_query(self.date)
        return "date = '{date}'".format(date=self.date.isoformat())


def _query_rows(query):
    with get_write_stats_cursor() as c:
        c.execute(query)
        for row in c:
            yield row


def _sum_conversion(postclick_source, conversion_str):
    conv = defaultdict(int)

    for line in conversion_str.split('\n'):
        line = line.strip()
        if not line:
            continue
        c = json.loads(line)
        for k, v in c.iteritems():
            conv[helpers.get_conversion_prefix(postclick_source, k)] += v

    return dict(conv)
