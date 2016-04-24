import backtosql

from redshiftapi import constants
from redshiftapi import models_helpers

class RSContentAdStats(backtosql.Model, models_helpers.RSBreakdownMixin):
    # this model defines the basic materialized view that has
    # all the fields available

    # TODO: until K1 data is not available use the existing
    # 'contentadstats' table. The model definition is based
    # on that table for now.

    dt = backtosql.TemplateColumn('part_trunc_date.sql', {'column_name': 'dt'},
                                  constants.ColumnGroup.BREAKDOWN)

    account_id = backtosql.Column('account_id', constants.ColumnGroup.BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', constants.ColumnGroup.BREAKDOWN)
    ad_group_id = backtosql.Column('adgroup_id', constants.ColumnGroup.BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', constants.ColumnGroup.BREAKDOWN)
    source_id = backtosql.Column('source_id', constants.ColumnGroup.BREAKDOWN)

    clicks = models_helpers.SumColumn('clicks')
    impressions = models_helpers.SumColumn('impressions')
    cost = models_helpers.SumCCColumn('cost_cc')
    data_cost = models_helpers.SumCCColumn('data_cost_cc')

    # BCM
    media_cost = models_helpers.SumCCColumn('cost_cc')
    e_media_cost = models_helpers.SumNanoColumn('effective_cost_nano')
    e_data_cost = models_helpers.SumNanoColumn('effective_data_cost_nano')
    license_fee = models_helpers.SumNanoColumn('license_fee_nano')
    billing_cost = models_helpers.AggregateColumn(column_name=None, template_name='part_billing_cost.sql')
    total_cost = models_helpers.AggregateColumn(column_name=None, template_name='part_total_cost.sql')

    # Derivates
    ctr = models_helpers.SumDivPercColumn('clicks', 'impressions')
    cpc = models_helpers.SumDivCCColumn('cost_cc', 'clicks')

    # Postclick acquisition fields
    visits = models_helpers.SumColumn('visits')
    click_discrepancy = models_helpers.AggregateColumn(column_name=None, template_name='part_click_discrepancy.sql')
    pageviews = models_helpers.SumColumn('pageviews')

    # Postclick engagement fields
    new_visits = models_helpers.SumColumn('new_visits')
    percent_new_users = models_helpers.SumDivPercColumn('new_visits', 'visits')
    bounce_rate = models_helpers.SumDivPercColumn('bounced_visits', 'visits')
    pv_per_visit = models_helpers.SumDivColumn('pageviews', 'visits')
    avg_tos = models_helpers.SumDivColumn('total_time_on_site', 'visits')

    @classmethod
    def get_best_view(cls, breakdown, constraints):
        return 'contentadstats'

    @classmethod
    def get_best_query_template(cls, breakdown, constraints):
        if len(breakdown) == 2:
            return 'q_2_breakdowns.sql'
        return 'q_simple_breakdown.sql'