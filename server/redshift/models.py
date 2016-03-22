from functools import partial
from templatesql import Model, Column, TemplateColumn


class ColumnGroup(object):
    BREAKDOWN = 1
    AGGREGATES = 2
    SPECIAL = 3

# shortcuts
CGB = ColumnGroup.BREAKDOWN
CGA = ColumnGroup.AGGREGATES
CGS = ColumnGroup.SPECIAL


SumColumn = partial(TemplateColumn, 'part_sum.sql', group=CGA)
SumCCColumn = partial(TemplateColumn, 'part_sum_cc.sql', group=CGA)
SumNanoColumn = partial(TemplateColumn, 'part_sum_nano.sql', group=CGA)
class SumDivColumn(TemplateColumn):
    def __init__(self, expr, divisor, sub_template=None):
        super(SumDivColumn, self).__init__(sub_template or 'part_sumdiv.sql', '', CGA, {'expr': expr, 'divisor': divisor})
SumDivCCColumn = partial(SumDivColumn, sub_template='part_sumdiv_cc.sql')
SumDivPercColumn = partial(SumDivColumn, sub_template='part_sumdiv_perc.sql')


class RSContentAdsModel(Model):
    date = TemplateColumn('part_trunc_date.sql', 'dt', CGB)

    account_id = Column('account_id', CGB)
    campaign_id = Column('campaign_id', CGB)
    ad_group_id = Column('adgroup_id', CGB)
    content_ad_id = Column('content_ad', CGB)
    source_id = Column('source_id', CGB)

    clicks = SumColumn('clicks')
    impressions = SumColumn('impressions')
    cost = SumCCColumn('cost_cc')
    data_cost = SumCCColumn('data_cost_cc')

    # BCM
    media_cost = SumCCColumn('cost_cc')
    e_media_cost = SumNanoColumn('effective_cost_nano')
    e_data_cost = SumNanoColumn('effective_data_cost_nano')
    license_fee = SumNanoColumn('license_fee_nano')
    billing_cost = TemplateColumn('part_billing_cost.sql', '', CGA)
    total_cost = TemplateColumn('part_total_cost.sql', '', CGA)

    # Derivates
    ctr = SumDivPercColumn('clicks', 'impressions')
    cpc = SumDivCCColumn('cost_cc', 'clicks')

    # Postclick acquisition fields
    visits = SumColumn('visits')
    click_discrepancy = TemplateColumn('part_click_discrepancy.sql', '', CGA)
    pageviews = SumColumn('pageviews')

    # Postclick engagement fields
    new_visits = SumColumn('new_visits')
    percent_new_users = SumDivPercColumn('new_visits', 'visits')
    bounce_rate = SumDivPercColumn('bounced_visits', 'visits')
    pv_per_visit = SumDivColumn('pageviews', 'visits')
    avg_tos = SumDivColumn('total_time_on_site', 'visits')

    # Conversion goal fields (what SQL does it result into?)
    # _CONVERSION_GOAL_FIELDS = [
    #     dict(sql='conversions',           app='conversions',        out=rsh.decimal_to_int_exact, calc=rsh.sum_expr(rsh.extract_json_or_null('conversions')), num_json_params=2)
    # ]

    # Some other aggregations
    # TODO: duration probably has an error (no aggregate in api_contentads)
    has_postclick_metrics = TemplateColumn('part_has_postclick.sql', '', CGS)

    @classmethod
    def get_view(cls, brekdown=None):
        return 'contentadstats'

    @classmethod
    def get_query_template(cls, breakdown=None):
        return 'campaign_lvl1.sql'

    @classmethod
    def get_best_page_size(cls, page, breakdown=None):
        return page