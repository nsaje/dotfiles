import logging
import json
from collections import defaultdict
from decimal import Decimal

from django.db import connections
from django.conf import settings

import dash.models
from reports import daily_statements_k1

logger = logging.getLogger(__name__)

CC_TO_MICRO = 100
MICRO_TO_NANO = 1000


class ContentAdStats(object):
    """
    date, content_ad_id, adgroup_id, source_id
    campaign_id, account_id
    impressions, clicks
    cost_cc, data_cost_cc
    visits, new_visits, bounced_visits, pageviews, total_time_on_site, conversions
    effective_cost_nano, effective_data_cost_nano, license_fee_nano
    """

    def table_name(self):
        return 'contentadstats'

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
             ('pageviews', 'sum'), ('total_time_on_site', 'avg'), ('conversions', 'listagg')],
        )

    def _sum_conversion(self, conversion_str):
        conv = defaultdict(int)

        for line in conversion_str.split('\n'):
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            for k, v in c.iteritems():
                conv[k] += v

        return dict(conv)

    def _get_post_click_data(self, ad_group, post_click_list):
        if not post_click_list:
            return {}

        if len(post_click_list) > 1:
            logger.warn("Multiple post click statistics for ad group: %s", ad_group.id)

        post_click = post_click_list[0]
        if len(post_click) < 9:
            raise Exception("Invalid post click row")

        return {
            "visits": post_click[3],
            "new_visits": post_click[4],
            "bounced_visits": post_click[5],
            "pageviews": post_click[6],
            "time_on_site": post_click[7],
            "conversions": json.dumps(self._sum_conversion(post_click[8])),
        }

    def generate_rows(self, date, campaign_factors):
        content_ad_postclick = defaultdict(list)
        for row in self._postclick_stats_breakdown(date).rows():
            content_ad_id = row[0]
            media_source = row[2]
            content_ad_postclick[(content_ad_id, media_source)].append(row)

        ad_groups_map = {a.id: a for a in dash.models.AdGroup.objects.all()}
        media_sources_map = {s.bidder_slug: s for s in dash.models.Source.objects.all()}

        for row in self._stats_breakdown(date).rows():
            ad_group = ad_groups_map.get(row[0])
            if ad_group is None:
                logger.error("Got spend for invalid adgroup: %s", row[0])
                continue
            media_source = media_sources_map.get(row[3])
            if media_source is None:
                logger.error("Got spend for invalid media_source: %s", row[3])
                continue

            cost = row[6] or 0
            data_cost = row[7] or 0

            effective_cost, effective_data_cost, license_fee = _calculate_effective_cost(
                    cost, data_cost, campaign_factors[ad_group.campaign])

            post_click = self._get_post_click_data(ad_group, content_ad_postclick.get((row[1], row[3])))

            yield (
                date,
                row[1],  # content_ad_id
                ad_group.id,
                media_source.id,

                ad_group.campaign.id,
                ad_group.campaign.account.id,
                row[4],  # impressions
                row[5],  # clicks

                _micro_to_cc(cost),
                _micro_to_cc(data_cost),

                post_click.get('visits'),
                post_click.get('new_visits'),
                post_click.get('bounced_visits'),
                post_click.get('pageviews'),
                post_click.get('time_on_site'),
                post_click.get('conversions'),

                _decimal_to_int(effective_cost * MICRO_TO_NANO),
                _decimal_to_int(effective_data_cost * MICRO_TO_NANO),
                _decimal_to_int(license_fee * MICRO_TO_NANO),
            )


class Breakdown(object):

    def __init__(self, date, table, breakdowns, values):
        self.date = date
        self.table = table
        self.breakdowns = breakdowns
        self.values = values

    def rows(self):
        query = self._get_materialize_query()
        logger.info("Breakdown query: %s", query)
        with connections[settings.K1_DB_NAME].cursor() as c:
            c.execute(query)
            for row in c:
                yield row

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
            return daily_statements_k1._get_redshift_date_query(self.date)
        return "date = '{date}'".format(date=self.date.isoformat())


def _calculate_effective_cost(cost, data_cost, factors):
    pct_actual_spend, pct_license_fee = factors

    effective_cost = cost * pct_actual_spend
    effective_data_cost = data_cost * pct_actual_spend
    license_fee = (effective_cost + effective_data_cost) * pct_license_fee

    return effective_cost, effective_data_cost, license_fee


def _decimal_to_int(d):
    return int(round(d))


def _micro_to_cc(d):
    return _decimal_to_int(Decimal(d) / CC_TO_MICRO)
