import backtosql

from redshiftapi.model_helpers import RSBreakdownMixin, AGGREGATES, BREAKDOWN


class K1PostclickStats(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column('date', BREAKDOWN)

    postclick_source = backtosql.Column('type', BREAKDOWN)

    ad_group_id = backtosql.Column('ad_group_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    source_slug = backtosql.Column('source', BREAKDOWN)
    publisher = backtosql.Column('publisher', BREAKDOWN)

    visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'visits'}, AGGREGATES)
    new_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, AGGREGATES)
    bounced_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'bounced_visits'}, AGGREGATES)
    pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, AGGREGATES)
    total_time_on_site = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'total_time_on_site'}, AGGREGATES)

    conversions = backtosql.TemplateColumn('part_json_dict_sum.sql', {'column_name': 'conversions'}, AGGREGATES)
    users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'users'}, AGGREGATES)

    def get_best_view(self, *args, **kwargs):
        return 'postclickstats'


class MVMaster(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column('date', BREAKDOWN)

    agency_id = backtosql.Column('agency_id', BREAKDOWN)
    account_id = backtosql.Column('account_id', BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', BREAKDOWN)
    ad_group_id = backtosql.Column('ad_group_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    source_id = backtosql.Column('source_id', BREAKDOWN)
    publisher = backtosql.Column('publisher', BREAKDOWN)
    external_id = backtosql.Column('external_id', BREAKDOWN)

    device_type = backtosql.Column('device_type', BREAKDOWN)
    country = backtosql.Column('country', BREAKDOWN)
    state = backtosql.Column('state', BREAKDOWN)
    dma = backtosql.Column('dma', BREAKDOWN)
    age = backtosql.Column('age', BREAKDOWN)
    gender = backtosql.Column('gender', BREAKDOWN)
    age_gender = backtosql.Column('age_gender', BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, AGGREGATES)
    impressions = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'impressions'}, AGGREGATES)
    cost_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'cost_nano'}, AGGREGATES)
    data_cost_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'data_cost_nano'}, AGGREGATES)

    visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'visits'}, AGGREGATES)
    new_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, AGGREGATES)
    bounced_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'bounced_visits'}, AGGREGATES)
    pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, AGGREGATES)
    total_time_on_site = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'total_time_on_site'}, AGGREGATES)

    effective_cost_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'effective_cost_nano'}, AGGREGATES)
    effective_data_cost_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'effective_data_cost_nano'},
                                                        AGGREGATES)
    license_fee_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'license_fee_nano'}, AGGREGATES)
    margin_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'margin_nano'}, AGGREGATES)

    users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'users'}, AGGREGATES)
    returning_users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'returning_users'}, AGGREGATES)

    def get_ordered_aggregates(self):
        """
        Returns aggregates in order as it is used in materialized view table definitions.
        """

        return self.select_columns(subset=[
            'impressions', 'clicks', 'cost_nano', 'data_cost_nano', 'visits', 'new_visits',
            'bounced_visits', 'pageviews', 'total_time_on_site', 'effective_cost_nano',
            'effective_data_cost_nano', 'license_fee_nano', 'margin_nano', 'users',
            'returning_users',
        ])
