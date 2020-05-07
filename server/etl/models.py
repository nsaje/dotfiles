from django.db import models

import backtosql

BREAKDOWN = 1
AGGREGATES = 2


class MaterializationRun(models.Model):
    id = models.AutoField(primary_key=True)
    finished_dt = models.DateTimeField(auto_now_add=True, verbose_name="Finished at")


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

    account_id = backtosql.Column("account_id", BREAKDOWN)
    campaign_id = backtosql.Column("campaign_id", BREAKDOWN)
    ad_group_id = backtosql.Column("ad_group_id", BREAKDOWN)
    content_ad_id = backtosql.Column("content_ad_id", BREAKDOWN)
    publisher = backtosql.Column("publisher", BREAKDOWN)
    publisher_source_id = backtosql.Column("publisher_source_id", BREAKDOWN)

    device_type = backtosql.Column("device_type", BREAKDOWN, null=True)
    device_os = backtosql.Column("device_os", BREAKDOWN, null=True)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN, null=True)
    environment = backtosql.Column("environment", BREAKDOWN, null=True)

    zem_placement_type = backtosql.Column("zem_placement_type", BREAKDOWN, null=True)
    video_playback_method = backtosql.Column("video_playback_method", BREAKDOWN, null=True)

    country = backtosql.Column("country", BREAKDOWN, null=True)
    state = backtosql.Column("state", BREAKDOWN, null=True)
    dma = backtosql.Column("dma", BREAKDOWN, null=True)
    city_id = backtosql.Column("city_id", BREAKDOWN, null=True)

    age = backtosql.Column("age", BREAKDOWN, null=True)
    gender = backtosql.Column("gender", BREAKDOWN, null=True)
    age_gender = backtosql.Column("age_gender", BREAKDOWN, null=True)

    impressions = backtosql.TemplateColumn("part_sum.sql", {"column_name": "impressions"}, AGGREGATES)
    clicks = backtosql.TemplateColumn("part_sum.sql", {"column_name": "clicks"}, AGGREGATES)
    cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "cost_nano"}, AGGREGATES)
    data_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "data_cost_nano"}, AGGREGATES)

    visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "visits"}, AGGREGATES)
    new_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "new_visits"}, AGGREGATES)
    bounced_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "bounced_visits"}, AGGREGATES)
    pageviews = backtosql.TemplateColumn("part_sum.sql", {"column_name": "pageviews"}, AGGREGATES)
    total_time_on_site = backtosql.TemplateColumn("part_sum.sql", {"column_name": "total_time_on_site"}, AGGREGATES)

    effective_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "effective_cost_nano"}, AGGREGATES)
    effective_data_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "effective_data_cost_nano"}, AGGREGATES
    )  # noqa
    license_fee_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "license_fee_nano"}, AGGREGATES)
    margin_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "margin_nano"}, AGGREGATES)

    users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "users"}, AGGREGATES)
    returning_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "returning_users"}, AGGREGATES)

    video_start = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_start"}, AGGREGATES)
    video_first_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_first_quartile"}, AGGREGATES)
    video_midpoint = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_midpoint"}, AGGREGATES)
    video_third_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_third_quartile"}, AGGREGATES)
    video_complete = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_complete"}, AGGREGATES)
    video_progress_3s = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_progress_3s"}, AGGREGATES)

    local_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "local_cost_nano"}, AGGREGATES)
    local_data_cost_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "local_data_cost_nano"}, AGGREGATES)
    local_effective_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_effective_cost_nano"}, AGGREGATES
    )  # noqa
    local_effective_data_cost_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_effective_data_cost_nano"}, AGGREGATES
    )  # noqa
    local_license_fee_nano = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "local_license_fee_nano"}, AGGREGATES
    )  # noqa
    local_margin_nano = backtosql.TemplateColumn("part_sum.sql", {"column_name": "local_margin_nano"}, AGGREGATES)

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
            ]
        )


class MVPublishers(MVMaster):
    external_id = backtosql.Column("external_id", BREAKDOWN)


class MVAdGroupPlacement(MVMaster):
    placement = backtosql.Column("placement", BREAKDOWN, null=True)
    placement_type = backtosql.Column("placement_type", BREAKDOWN, null=True)


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

    account_id = backtosql.Column("account_id", BREAKDOWN)
    campaign_id = backtosql.Column("campaign_id", BREAKDOWN)
    ad_group_id = backtosql.Column("ad_group_id", BREAKDOWN)
    content_ad_id = backtosql.Column("content_ad_id", BREAKDOWN)
    publisher = backtosql.Column("publisher", BREAKDOWN)
    publisher_source_id = backtosql.Column("publisher_source_id", BREAKDOWN)
    placement = backtosql.Column("placement", BREAKDOWN, null=True)
    placement_type = backtosql.Column("placement_type", BREAKDOWN, null=True)

    device_type = backtosql.Column("device_type", BREAKDOWN)
    device_os = backtosql.Column("device_os", BREAKDOWN)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN)
    environment = backtosql.Column("environment", BREAKDOWN)

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
    )  # noqa

    type = backtosql.Column("type", BREAKDOWN)

    def get_ordered_aggregates(self):
        """
        Returns aggregates in order as it is used in materialized view table definitions.
        """

        return self.select_columns(subset=["touchpoint_count", "conversion_count", "conversion_value_nano"])
