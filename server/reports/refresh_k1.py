import logging

from django.db import connections
from django.conf import settings

import dash.models
from reports import daily_statements_k1

logger = logging.getLogger(__name__)


CC_TO_MICRO = 100
MICRO_TO_NANO = 1000


def _calculate_effective_cost(cost, data_cost, factors):
    pct_actual_spend, pct_license_fee = factors

    effective_cost = cost * pct_actual_spend
    effective_data_cost = data_cost * pct_actual_spend
    license_fee = (effective_cost + effective_data_cost) * pct_license_fee

    return effective_cost, effective_data_cost, license_fee


def _content_ads_tab_generator(date, rows, campaign_factors):
    """
    date, content_ad_id, adgroup_id, source_id
    campaign_id, account_id
    impressions, clicks
    cost_cc, data_cost_cc
    visits, new_visits, bounced_visits, pageviews, total_time_on_site, conversions
    effective_cost_nano, effective_data_cost_nano, license_fee_nano
    """

    ad_groups_map = {a.id: a for a in dash.models.AdGroup.objects.all()}

    for row in rows:
        ad_group = ad_groups_map[row[0]]

        cost = row[6] or 0
        data_cost = row[7] or 0

        effective_cost, effective_data_cost, license_fee = _calculate_effective_cost(
                cost, data_cost, campaign_factors[ad_group.campaign])

        yield (
            date,
            row[1],  # content_ad_id
            ad_group.id,  # ad_group_id
            row[3],  # source TODO mapping

            ad_group.campaign.id,  # campaign id
            ad_group.campaign.account.id,  # account id
            row[4],  # impressions
            row[5],  # clicks

            cost / CC_TO_MICRO,  # cost
            data_cost / CC_TO_MICRO,  # data cost

            0,  # visits TODO postclick
            0,  # new visits TODO postclick
            0,  # bounced visits TODO postclick
            0,  # pageviews TODO postclick
            0,  # time on site TODO postclick
            0,  # conversions TODO postclick

            effective_cost * MICRO_TO_NANO,  # effective_cost_nano TODO round
            effective_data_cost * MICRO_TO_NANO,  # effective_data_cost_nano TODO round
            license_fee * MICRO_TO_NANO,  # license_fee_nano TODO round
        )


TABLE_BREAKDOWNS = {
    'contentadstats': {
        'groups': ['ad_group_id', 'content_ad_id', 'media_source_type', 'media_source'],
        'values': ['impressions', 'clicks', 'spend', 'data_spend'],
        'generator': _content_ads_tab_generator,
    }
}


def refresh_k1_reports(update_since):
    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date())
    generate_views(effective_spend_factors)


def generate_views(effective_spend_factors):
    for date, campaigns in effective_spend_factors.iteritems():
        for table, props in TABLE_BREAKDOWNS.iteritems():
            _generate_table(date, table, props, effective_spend_factors[date])


def _generate_table(date, table, props, campaign_factors):
    print date, table

    cursor = connections[settings.STATS_DB_NAME].cursor()

    query = """
        select {groups}, {values}
        from stats
        where {date_query}
        group by {groups}
    """.format(
        groups=', '.join(props['groups']),
        values=', '.join(['sum(%s)' % v for v in props['values']]),
        date_query=daily_statements_k1._get_redshift_date_query(date),
    )

    logger.info("Running redshift query: %s", query)
    cursor.execute(query)

    for line in props['generator'](date, cursor, campaign_factors):
        print line
