from templatesql import RSModel, RSColumn, RSTemplateColumn


class ColumnGroup(object):
    BREAKDOWN = 1
    AGGREGATES = 2


class ContentAdsModel(RSModel):
    date = RSTemplateColumn('trunc_date.sql', 'dt', ColumnGroup.BREAKDOWN)

    account_id = RSColumn('account_id', ColumnGroup.BREAKDOWN)
    campaign_id = RSColumn('campaign_id', ColumnGroup.BREAKDOWN)
    ad_group_id = RSColumn('adgroup_id', ColumnGroup.BREAKDOWN)
    content_ad_id = RSColumn('content_ad', ColumnGroup.BREAKDOWN)
    source_id = RSColumn('source_id', ColumnGroup.BREAKDOWN)

    clicks = RSTemplateColumn('sum.sql', 'clicks', ColumnGroup.AGGREGATE)
    impressions = RSTemplateColumn('sum.sql', 'impressions',
                                   ColumnGroup.AGGREGATE)
    cost = RSTemplateColumn('sum.sql', 'cost_cc', ColumnGroup.AGGREGATE)
