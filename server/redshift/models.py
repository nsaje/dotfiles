from redshift.engine.models import RSModel, RSColumn, RSTemplateColumn, RSColumnType


class ContentAdsModel(RSModel):
    date = RSTemplateColumn('trunc_date.sql',
                            'dt',
                            expr='date',
                            column_type=RSColumnType.BREAKDOWN)

    account_id = RSColumn('account_id', column_type=RSColumnType.BREAKDOWN)
    campaign_id = RSColumn('campaign_id', column_type=RSColumnType.BREAKDOWN)
    ad_group_id = RSColumn('adgroup_id', column_type=RSColumnType.BREAKDOWN)
    content_ad_id = RSColumn('content_ad', column_type=RSColumnType.BREAKDOWN)

    # column type kinda doesn't belong into the engine
    # it is just a helper for api (engine doesn't know anything about)
    # breakdowns

    source_id = RSColumn('source_id', column_type=RSColumnType.BREAKDOWN)

    clicks = RSTemplateColumn('sum.sql',
                              'click_sum',
                              expr='clicks',
                              column_type=RSColumnType.AGGREGATE)
    impressions = RSTemplateColumn('sum.sql',
                                   'impression_sum',
                                   expr='impressions',
                                   column_type=RSColumnType.AGGREGATE)
    cost = RSTemplateColumn('sum.sql',
                            'cost_sum',
                            expr='cost_cc',
                            column_type=RSColumnType.AGGREGATE)
