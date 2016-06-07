import backtosql

import dash.constants

from redshiftapi.model_helpers import RSBreakdownMixin, AGGREGATES, BREAKDOWN


class K1Stats(backtosql.Model, RSBreakdownMixin):
    hour = backtosql.Column('hour', BREAKDOWN)
    date = backtosql.Column('date', BREAKDOWN)

    source_type = backtosql.Column('media_source_type', BREAKDOWN)
    source_slug = backtosql.Column('media_source', BREAKDOWN)

    ad_group_id = backtosql.Column('ad_group_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    publisher = backtosql.Column('publisher', BREAKDOWN)

    device_type = backtosql.Column('device_type', BREAKDOWN)
    country = backtosql.Column('country', BREAKDOWN)
    state = backtosql.Column('state', BREAKDOWN)
    dma = backtosql.Column('dma', BREAKDOWN)
    age = backtosql.Column('age', BREAKDOWN)
    gender = backtosql.Column('gender', BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, AGGREGATES)
    impressions = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'impressions'}, AGGREGATES)
    cost_micro = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'spend'}, AGGREGATES)
    data_cost_micro = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'data_spend'}, AGGREGATES)

    def get_best_view(self, *args, **kwargs):
        return 'stats'


class K1Conversions(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column('date', BREAKDOWN)

    account_id = backtosql.Column('account_id', BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', BREAKDOWN)
    ad_group_id = backtosql.Column('ad_group_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    source_id = backtosql.Column('source_id', BREAKDOWN)
    publisher = backtosql.Column('publisher', BREAKDOWN)

    slug = backtosql.Column('slug', BREAKDOWN)
    conversion_window = backtosql.TemplateColumn('part_conversion_window.sql', {
        'column_name': 'conversion_lag',
        'conversion_windows': dash.constants.ConversionWindows.get_all()
    }, BREAKDOWN)

    count = backtosql.TemplateColumn('part_count.sql', None, AGGREGATES)

    def get_best_view(self, *args, **kwargs):
        return 'conversions'


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

    def get_best_view(self, *args, **kwargs):
        return 'postclickstats'


class K1OutbrainPublisherStats(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column('date', BREAKDOWN)

    ad_group_id = backtosql.Column('ad_group_id', BREAKDOWN)
    publisher = backtosql.Column('publisher_name', BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, AGGREGATES)

    def get_best_view(self, *args, **kwargs):
        return 'outbrainpublisherstats'


class MVMaster(backtosql.Model, RSBreakdownMixin):
    date = backtosql.TemplateColumn('part_trunc_date.sql', {'column_name': 'date'}, BREAKDOWN)

    agency_id = backtosql.Column('agency_id', BREAKDOWN)
    account_id = backtosql.Column('account_id', BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', BREAKDOWN)
    ad_group_id = backtosql.Column('adgroup_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    source_id = backtosql.Column('source_id', BREAKDOWN)
    publisher = backtosql.Column('publisher', BREAKDOWN)

    device_type = backtosql.Column('device_type', BREAKDOWN)
    country = backtosql.Column('country', BREAKDOWN)
    state = backtosql.Column('state', BREAKDOWN)
    dma = backtosql.Column('dma', BREAKDOWN)
    age = backtosql.Column('age', BREAKDOWN)
    gender = backtosql.Column('gender', BREAKDOWN)
    age_gender = backtosql.Column('age_gender', BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, AGGREGATES)
    impressions = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'impressions'}, AGGREGATES)
    cost = backtosql.TemplateColumn('part_sum_cc.sql', {'column_name': 'cost_cc'}, AGGREGATES)
    data_cost = backtosql.TemplateColumn('part_sum_cc.sql', {'column_name': 'data_cost_cc'}, AGGREGATES)

    visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'visits'}, AGGREGATES)
    new_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, AGGREGATES)
    bounced_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'bounced_visits'}, AGGREGATES)
    pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, AGGREGATES)
    total_time_on_site = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'total_time_on_site'}, AGGREGATES)

    effective_cost_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'effective_cost_nano'}, AGGREGATES)
    effective_data_cost_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'effective_data_cost_nano'}, AGGREGATES)
    license_fee_nano = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'license_fee_nano'}, AGGREGATES)

    conversions = backtosql.TemplateColumn('part_json_dict_sum.sql', {'column_name': 'conversions'}, AGGREGATES)
    tp_conversions = backtosql.TemplateColumn('part_json_dict_sum.sql', {'column_name': 'tp_conversions'}, AGGREGATES)

    @classmethod
    def get_aggregates(cls):
        """
        Returns aggregates in default order as it is used in materialized view table definitions.
        """

        # TODO test count == nr aggregates
        return cls.select_columns(subset=[
            'impressions', 'clicks', 'cost', 'data_cost', 'visits', 'new_visits',
            'bounced_visits', 'pageviews', 'total_time_on_site', 'effective_cost_nano',
            'effective_data_cost_nano', 'license_fee_nano', 'conversions', 'tp_conversions',
        ])
