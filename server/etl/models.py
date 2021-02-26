from django.db import models

import backtosql

BREAKDOWN = 1
AGGREGATES = 2


class MaterializationRun(models.Model):
    id = models.AutoField(primary_key=True)
    finished_dt = models.DateTimeField(auto_now_add=True, verbose_name="Finished at")


class EtlBooksClosed(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    modified_dt = models.DateTimeField(auto_now_add=True)
    etl_books_closed = models.BooleanField(default=False)


class RSBreakdownMixin(object):
    """
    Mixin that defines breakdowns specific model features.
    """

    @classmethod
    def get_best_view(cls, breakdown):
        """ Returns the SQL view that best fits the breakdown """
        raise NotImplementedError()

    def get_breakdown(self, breakdown):
        """ Selects breakdown subset of columns """
        return self.select_columns(subset=breakdown)

    def get_aggregates(self):
        """ Returns all the aggregate columns """
        return self.select_columns(group=AGGREGATES)


class K1PostclickStats(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column("date", BREAKDOWN)

    postclick_source = backtosql.Column("type", BREAKDOWN)

    ad_group_id = backtosql.Column("ad_group_id", BREAKDOWN)
    content_ad_id = backtosql.Column("content_ad_id", BREAKDOWN)
    source_slug = backtosql.Column("source", BREAKDOWN)
    publisher = backtosql.Column("publisher", BREAKDOWN)

    visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "visits"}, AGGREGATES)
    new_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "new_visits"}, AGGREGATES)
    bounced_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "bounced_visits"}, AGGREGATES)
    pageviews = backtosql.TemplateColumn("part_sum.sql", {"column_name": "pageviews"}, AGGREGATES)
    total_time_on_site = backtosql.TemplateColumn("part_sum.sql", {"column_name": "total_time_on_site"}, AGGREGATES)

    conversions = backtosql.TemplateColumn("part_json_dict_sum.sql", {"column_name": "conversions"}, AGGREGATES)
    users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "users"}, AGGREGATES)

    def get_best_view(self, *args, **kwargs):
        return "postclickstats"


class MVMaster(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column("date", BREAKDOWN)
    source_id = backtosql.Column("source_id", BREAKDOWN)
    original_source_id = backtosql.Column("original_source_id", BREAKDOWN)

    account_id = backtosql.Column("account_id", BREAKDOWN)
    campaign_id = backtosql.Column("campaign_id", BREAKDOWN)
    ad_group_id = backtosql.Column("ad_group_id", BREAKDOWN)
    content_ad_id = backtosql.Column("content_ad_id", BREAKDOWN)
    publisher = backtosql.Column("publisher", BREAKDOWN)
    publisher_source_id = backtosql.Column("publisher_source_id", BREAKDOWN)

    device_type = backtosql.Column("device_type", BREAKDOWN)
    device_os = backtosql.Column("device_os", BREAKDOWN)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN)
    environment = backtosql.Column("environment", BREAKDOWN)
    browser = backtosql.Column("browser", BREAKDOWN)
    connection_type = backtosql.Column("connection_type", BREAKDOWN)

    zem_placement_type = backtosql.Column("zem_placement_type", BREAKDOWN)
    video_playback_method = backtosql.Column("video_playback_method", BREAKDOWN)

    country = backtosql.Column("country", BREAKDOWN)
    state = backtosql.Column("state", BREAKDOWN)
    dma = backtosql.Column("dma", BREAKDOWN)
    city_id = backtosql.Column("city_id", BREAKDOWN)

    age = backtosql.Column("age", BREAKDOWN)
    gender = backtosql.Column("gender", BREAKDOWN)
    age_gender = backtosql.Column("age_gender", BREAKDOWN)

    impressions = backtosql.TemplateColumn("part_sum.sql", {"column_name": "impressions"}, AGGREGATES)
    clicks = backtosql.TemplateColumn("part_sum.sql", {"column_name": "clicks"}, AGGREGATES)

    cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "cost_nano"}, AGGREGATES)
    data_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "data_cost_nano"}, AGGREGATES)
    base_effective_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "base_effective_cost_nano"}, AGGREGATES
    )
    base_effective_data_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "base_effective_data_cost_nano"}, AGGREGATES
    )
    effective_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "effective_cost_nano"}, AGGREGATES)
    effective_data_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "effective_data_cost_nano"}, AGGREGATES
    )
    service_fee_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "service_fee_nano"}, AGGREGATES)
    license_fee_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "license_fee_nano"}, AGGREGATES)
    margin_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "margin_nano"}, AGGREGATES)
    ssp_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "ssp_cost_nano"}, AGGREGATES)

    local_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "local_cost_nano"}, AGGREGATES)
    local_data_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "local_data_cost_nano"}, AGGREGATES)
    local_base_effective_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_base_effective_cost_nano"}, AGGREGATES
    )
    local_base_effective_data_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_base_effective_data_cost_nano"}, AGGREGATES
    )
    local_effective_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_effective_cost_nano"}, AGGREGATES
    )
    local_effective_data_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_effective_data_cost_nano"}, AGGREGATES
    )
    local_service_fee_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_service_fee_nano"}, AGGREGATES
    )
    local_license_fee_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_license_fee_nano"}, AGGREGATES
    )
    local_margin_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "local_margin_nano"}, AGGREGATES)
    local_ssp_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "local_ssp_cost_nano"}, AGGREGATES)

    users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "users"}, AGGREGATES)
    returning_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "returning_users"}, AGGREGATES)

    visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "visits"}, AGGREGATES)
    new_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "new_visits"}, AGGREGATES)
    bounced_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "bounced_visits"}, AGGREGATES)
    pageviews = backtosql.TemplateColumn("part_sum.sql", {"column_name": "pageviews"}, AGGREGATES)
    total_time_on_site = backtosql.TemplateColumn("part_sum.sql", {"column_name": "total_time_on_site"}, AGGREGATES)

    video_start = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_start"}, AGGREGATES)
    video_first_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_first_quartile"}, AGGREGATES)
    video_midpoint = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_midpoint"}, AGGREGATES)
    video_third_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_third_quartile"}, AGGREGATES)
    video_complete = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_complete"}, AGGREGATES)
    video_progress_3s = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_progress_3s"}, AGGREGATES)

    mrc50_measurable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc50_measurable"}, AGGREGATES)
    mrc50_viewable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc50_viewable"}, AGGREGATES)
    mrc100_measurable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc100_measurable"}, AGGREGATES)
    mrc100_viewable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc100_viewable"}, AGGREGATES)
    vast4_measurable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "vast4_measurable"}, AGGREGATES)
    vast4_viewable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "vast4_viewable"}, AGGREGATES)

    def get_ordered_aggregates(self):
        """
        Returns aggregates in order as it is used in materialized view table definitions.
        """

        return self.select_columns(
            subset=[
                "impressions",
                "clicks",
                "cost_nano",
                "data_cost_nano",
                "visits",
                "new_visits",
                "bounced_visits",
                "pageviews",
                "total_time_on_site",
                "effective_cost_nano",
                "effective_data_cost_nano",
                "license_fee_nano",
                "margin_nano",
                "users",
                "returning_users",
                "video_start",
                "video_first_quartile",
                "video_midpoint",
                "video_third_quartile",
                "video_complete",
                "video_progress_3s",
                "local_cost_nano",
                "local_data_cost_nano",
                "local_effective_cost_nano",
                "local_effective_data_cost_nano",
                "local_license_fee_nano",
                "local_margin_nano",
                "mrc50_measurable",
                "mrc50_viewable",
                "mrc100_measurable",
                "mrc100_viewable",
                "vast4_measurable",
                "vast4_viewable",
                "ssp_cost_nano",
                "local_ssp_cost_nano",
                "base_effective_cost_nano",
                "base_effective_data_cost_nano",
                "service_fee_nano",
                "local_base_effective_cost_nano",
                "local_base_effective_data_cost_nano",
                "local_service_fee_nano",
            ]
        )


class MVAdGroupPlacement(MVMaster):
    placement = backtosql.Column("placement", BREAKDOWN)
    placement_type = backtosql.Column("placement_type", BREAKDOWN)


class MVConversions(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column("date", BREAKDOWN)
    source_id = backtosql.Column("source_id", BREAKDOWN)

    account_id = backtosql.Column("account_id", BREAKDOWN)
    campaign_id = backtosql.Column("campaign_id", BREAKDOWN)
    ad_group_id = backtosql.Column("ad_group_id", BREAKDOWN)
    content_ad_id = backtosql.Column("content_ad_id", BREAKDOWN)
    publisher = backtosql.Column("publisher", BREAKDOWN)
    publisher_source_id = backtosql.Column("publisher_source_id", BREAKDOWN)

    slug = backtosql.Column("slug", BREAKDOWN)

    conversion_count = backtosql.TemplateColumn("part_sum.sql", {"column_name": "conversion_count"}, AGGREGATES)

    def get_ordered_aggregates(self):
        """
        Returns aggregates in order as it is used in materialized view table definitions.
        """

        return self.select_columns(group=AGGREGATES)


class MVTouchpointConversions(backtosql.Model, RSBreakdownMixin):
    date = backtosql.Column("date", BREAKDOWN)
    source_id = backtosql.Column("source_id", BREAKDOWN)
    original_source_id = backtosql.Column("original_source_id", BREAKDOWN)

    account_id = backtosql.Column("account_id", BREAKDOWN)
    campaign_id = backtosql.Column("campaign_id", BREAKDOWN)
    ad_group_id = backtosql.Column("ad_group_id", BREAKDOWN)
    content_ad_id = backtosql.Column("content_ad_id", BREAKDOWN)
    publisher = backtosql.Column("publisher", BREAKDOWN)
    publisher_source_id = backtosql.Column("publisher_source_id", BREAKDOWN)
    placement = backtosql.Column("placement", BREAKDOWN)
    placement_type = backtosql.Column("placement_type", BREAKDOWN)

    device_type = backtosql.Column("device_type", BREAKDOWN)
    device_os = backtosql.Column("device_os", BREAKDOWN)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN)
    environment = backtosql.Column("environment", BREAKDOWN)
    browser = backtosql.Column("browser", BREAKDOWN)
    connection_type = backtosql.Column("connection_type", BREAKDOWN)

    country = backtosql.Column("country", BREAKDOWN)
    state = backtosql.Column("state", BREAKDOWN)
    dma = backtosql.Column("dma", BREAKDOWN)

    slug = backtosql.Column("slug", BREAKDOWN)
    conversion_window = backtosql.Column("conversion_window", BREAKDOWN)
    conversion_label = backtosql.Column("conversion_label", BREAKDOWN)

    touchpoint_count = backtosql.TemplateColumn("part_sum.sql", {"column_name": "touchpoint_count"}, AGGREGATES)
    conversion_count = backtosql.TemplateColumn("part_sum.sql", {"column_name": "conversion_count"}, AGGREGATES)
    conversion_value_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "conversion_value_nano"}, AGGREGATES
    )

    type = backtosql.Column("type", BREAKDOWN)

    def get_ordered_aggregates(self):
        """
        Returns aggregates in order as it is used in materialized view table definitions.
        """

        return self.select_columns(subset=["touchpoint_count", "conversion_count", "conversion_value_nano"])
