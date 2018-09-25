import backtosql
from collections import defaultdict
from dateutil import rrule
import logging
import os.path

from django.conf import settings

import dash.models
from redshiftapi import db

from etl import constants
from etl import helpers
from etl import models
from etl import redshift
from etl import s3
from etl import spark
from .materialize import Materialize

logger = logging.getLogger(__name__)


class MasterSpark(Materialize):
    """
    Represents breakdown by all dimensions available. It containts traffic, postclick, conversions
    and tochpoint conversions data. This is only load to spark.

    NOTE: It excludes outbrain publishers as those are currently not linked to content ads and so
    breakdown by publisher and content ad is not possible for them.
    """

    IS_TEMPORARY_TABLE = True
    TABLE_NAME = "mv_master_on_spark"

    SPARK_TABLE_NAME = "mv_master"
    STATS_SPARK_TABLE_NAME = "mv_master_stats"
    POSTCLICK_SPARK_TABLE_NAME = "mv_master_postclick"
    POSTCLICK_SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("source_id", "int"),
        spark.Column("account_id", "int"),
        spark.Column("campaign_id", "int"),
        spark.Column("ad_group_id", "int"),
        spark.Column("content_ad_id", "int"),
        spark.Column("publisher", "string", nullable=True),
        spark.Column("publisher_source_id", "string", nullable=True),
        spark.Column("device_type", "int", nullable=True),
        spark.Column("device_os", "string", nullable=True),
        spark.Column("device_os_version", "string", nullable=True),
        spark.Column("placement_medium", "string", nullable=True),
        spark.Column("placement_type", "int", nullable=True),
        spark.Column("video_playback_method", "int", nullable=True),
        spark.Column("country", "string", nullable=True),
        spark.Column("state", "string", nullable=True),
        spark.Column("dma", "int", nullable=True),
        spark.Column("city_id", "int", nullable=True),
        spark.Column("age", "string", nullable=True),
        spark.Column("gender", "string", nullable=True),
        spark.Column("age_gender", "string", nullable=True),
        spark.Column("impressions", "int", nullable=True),
        spark.Column("clicks", "int", nullable=True),
        spark.Column("cost_nano", "long", nullable=True),
        spark.Column("data_cost_nano", "long", nullable=True),
        spark.Column("visits", "int", nullable=True),
        spark.Column("new_visits", "int", nullable=True),
        spark.Column("bounced_visits", "int", nullable=True),
        spark.Column("pageviews", "int", nullable=True),
        spark.Column("total_time_on_site", "int", nullable=True),
        spark.Column("effective_cost_nano", "long", nullable=True),
        spark.Column("effective_data_cost_nano", "long", nullable=True),
        spark.Column("license_fee_nano", "long", nullable=True),
        spark.Column("margin_nano", "long", nullable=True),
        spark.Column("users", "int", nullable=True),
        spark.Column("returning_users", "int", nullable=True),
        spark.Column("video_start", "int", nullable=True),
        spark.Column("video_first_quartile", "int", nullable=True),
        spark.Column("video_midpoint", "int", nullable=True),
        spark.Column("video_third_quartile", "int", nullable=True),
        spark.Column("video_complete", "int", nullable=True),
        spark.Column("video_progress_3s", "int", nullable=True),
        spark.Column("local_cost_nano", "long", nullable=True),
        spark.Column("local_data_cost_nano", "long", nullable=True),
        spark.Column("local_effective_cost_nano", "long", nullable=True),
        spark.Column("local_effective_data_cost_nano", "long", nullable=True),
        spark.Column("local_license_fee_nano", "long", nullable=True),
        spark.Column("local_margin_nano", "long", nullable=True),
    ]
    DIFF_SPARK_TABLE_NAME = "mv_master_diff"
    DIFF_SPARK_COLUMNS = [
        spark.Column("date", "string"),
        spark.Column("source_id", "int"),
        spark.Column("account_id", "int", nullable=True),
        spark.Column("campaign_id", "int", nullable=True),
        spark.Column("ad_group_id", "int"),
        spark.Column("content_ad_id", "int"),
        spark.Column("publisher", "string", nullable=True),
        spark.Column("device_type", "int", nullable=True),
        spark.Column("country", "string", nullable=True),
        spark.Column("state", "string", nullable=True),
        spark.Column("dma", "int", nullable=True),
        spark.Column("age", "string", nullable=True),
        spark.Column("gender", "string", nullable=True),
        spark.Column("age_gender", "string", nullable=True),
        spark.Column("impressions", "int", nullable=True),
        spark.Column("clicks", "int", nullable=True),
        spark.Column("cost_nano", "long", nullable=True),
        spark.Column("data_cost_nano", "long", nullable=True),
        spark.Column("visits", "int", nullable=True),
        spark.Column("new_visits", "int", nullable=True),
        spark.Column("bounced_visits", "int", nullable=True),
        spark.Column("pageviews", "int", nullable=True),
        spark.Column("total_time_on_site", "int", nullable=True),
        spark.Column("effective_cost_nano", "long", nullable=True),
        spark.Column("effective_data_cost_nano", "long", nullable=True),
        spark.Column("license_fee_nano", "long", nullable=True),
        spark.Column("users", "int", nullable=True),
        spark.Column("returning_users", "int", nullable=True),
        spark.Column("local_cost_nano", "long", nullable=True),
        spark.Column("local_data_cost_nano", "long", nullable=True),
        spark.Column("local_effective_cost_nano", "long", nullable=True),
        spark.Column("local_effective_data_cost_nano", "long", nullable=True),
        spark.Column("local_license_fee_nano", "long", nullable=True),
    ]

    def generate(self, **kwargs):
        self.prefetch()

        # stats
        sql = self.prepare_stats_spark_query()
        self.spark_session.run_file("sql_to_table.py.tmpl", sql=sql, table=self.STATS_SPARK_TABLE_NAME)

        # postclick
        s3_path = os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.POSTCLICK_SPARK_TABLE_NAME, "data.csv")
        s3.upload_csv(s3_path, self.generate_rows)
        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=self.POSTCLICK_SPARK_TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=s3_path,
            schema=spark.generate_schema(self.POSTCLICK_SPARK_COLUMNS),
        )

        # diff
        redshift.unload_table(
            self.job_id,
            self.DIFF_SPARK_TABLE_NAME,
            self.date_from,
            self.date_to,
            prefix=constants.SPARK_S3_PREFIX,
            account_id=self.account_id,
        )
        self.spark_session.run_file(
            "load_csv_from_s3_to_table.py.tmpl",
            table=self.DIFF_SPARK_TABLE_NAME,
            s3_bucket=settings.S3_BUCKET_STATS,
            s3_path=os.path.join(constants.SPARK_S3_PREFIX, self.job_id, self.DIFF_SPARK_TABLE_NAME, "*.gz"),
            schema=spark.generate_schema(self.DIFF_SPARK_COLUMNS),
        )
        sql = self.prepare_diff_spark_query()
        self.spark_session.run_file("sql_to_table.py.tmpl", sql=sql, table=self.DIFF_SPARK_TABLE_NAME)

        # union
        self.spark_session.run_file(
            "union_tables.py.tmpl",
            table=self.SPARK_TABLE_NAME,
            source_table_1=self.STATS_SPARK_TABLE_NAME,
            source_table_2=self.POSTCLICK_SPARK_TABLE_NAME,
        )
        self.spark_session.run_file(
            "union_tables.py.tmpl",
            table=self.SPARK_TABLE_NAME,
            source_table_1=self.SPARK_TABLE_NAME,
            source_table_2=self.DIFF_SPARK_TABLE_NAME,
        )

        # cache
        self.spark_session.run_file("cache_table.py.tmpl", table=self.SPARK_TABLE_NAME)

    def prepare_stats_spark_query(self):
        sql = backtosql.generate_sql(
            "etl_spark_mv_master_stats.sql",
            {
                "date_from": self.date_from.isoformat(),
                "date_to": self.date_to.isoformat(),
                "account_id": self.account_id,
            },
        )
        return sql

    def prepare_diff_spark_query(self):
        sql = backtosql.generate_sql(
            "etl_spark_mv_master_diff.sql",
            {
                "date_from": self.date_from.isoformat(),
                "date_to": self.date_to.isoformat(),
                "account_id": self.account_id,
            },
        )
        return sql

    def generate_rows(self):
        with db.get_write_stats_cursor() as cursor:
            for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
                date = date.date()
                for _, row, _ in self.get_postclickstats(cursor, date):
                    yield row

    def prefetch(self):
        if self.account_id:
            self.ad_groups_map = {
                x.id: x for x in dash.models.AdGroup.objects.filter(campaign__account_id=self.account_id)
            }
            self.campaigns_map = {x.id: x for x in dash.models.Campaign.objects.filter(account_id=self.account_id)}
            self.accounts_map = {x.id: x for x in dash.models.Account.objects.filter(id=self.account_id)}

        else:
            self.ad_groups_map = {x.id: x for x in dash.models.AdGroup.objects.all()}
            self.campaigns_map = {x.id: x for x in dash.models.Campaign.objects.all()}
            self.accounts_map = {x.id: x for x in dash.models.Account.objects.all()}

        self.sources_slug_map = {
            helpers.extract_source_slug(x.bidder_slug): x for x in dash.models.Source.objects.all()
        }
        self.sources_map = {x.id: x for x in dash.models.Source.objects.all()}
        self.outbrain = helpers.get_outbrain()
        self.yahoo = helpers.get_yahoo()

    def get_postclickstats(self, cursor, date):

        # group postclick rows by ad group and postclick source
        rows_by_ad_group = defaultdict(lambda: defaultdict(list))
        for row in self.get_postclickstats_query_results(cursor, date):
            postclick_source = helpers.extract_postclick_source(row.postclick_source)
            rows_by_ad_group[row.ad_group_id][postclick_source].append(row)

        for ad_group_id, rows_by_postclick_source in rows_by_ad_group.items():

            if len(list(rows_by_postclick_source.keys())) > 1:
                logger.info(
                    "Postclick stats for a single ad group (%s) from different sources %s, date %s",
                    ad_group_id,
                    list(rows_by_postclick_source.keys()),
                    date,
                )

            rows = helpers.get_highest_priority_postclick_source(rows_by_postclick_source)

            for row in rows:
                source_slug = helpers.extract_source_slug(row.source_slug)
                if source_slug not in self.sources_slug_map:
                    logger.info("Got postclick stats for unknown source: %s", row.source_slug)
                    continue

                if row.ad_group_id not in self.ad_groups_map:
                    logger.info("Got postclick stats for unknown ad group: %s", row.ad_group_id)
                    continue

                source = self.sources_slug_map[source_slug]
                ad_group = self.ad_groups_map[row.ad_group_id]
                campaign = self.campaigns_map[ad_group.campaign_id]
                account = self.accounts_map[campaign.account_id]

                returning_users = helpers.calculate_returning_users(row.users, row.new_visits)

                publisher = row.publisher
                if source.id == self.yahoo.id:
                    publisher = "all publishers"
                elif publisher and source.id != self.outbrain.id:
                    publisher = publisher.lower()

                yield (
                    helpers.get_breakdown_key_for_postclickstats(source.id, row.content_ad_id),
                    (
                        date,
                        source.id,
                        account.id,
                        campaign.id,
                        ad_group.id,
                        row.content_ad_id,
                        publisher,
                        "{}__{}".format(publisher if publisher else "", source.id),  # publisher_source_id
                        dash.constants.DeviceType.UNKNOWN,
                        None,  # device_os
                        None,  # device_os_version
                        dash.constants.PlacementMedium.UNKNOWN,
                        dash.constants.PlacementType.UNKNOWN,
                        dash.constants.VideoPlaybackMethod.UNKNOWN,
                        None,  # country
                        None,  # state
                        None,  # dma
                        None,  # city_id
                        dash.constants.Age.UNDEFINED,
                        dash.constants.Gender.UNDEFINED,
                        dash.constants.AgeGender.UNDEFINED,
                        0,  # impressions
                        0,  # clicks
                        0,  # cost_nano
                        0,  # data_cost_nano
                        row.visits,
                        row.new_visits,
                        row.bounced_visits,
                        row.pageviews,
                        row.total_time_on_site,
                        0,  # effective_cost_nano
                        0,  # effective_data_cost_nano
                        0,  # license_fee_nano
                        0,  # margin_nano
                        row.users,
                        returning_users,
                        None,  # video_start
                        None,  # video_first_quartile
                        None,  # video_midpoint
                        None,  # video_third_quartile
                        None,  # video_complete
                        None,  # video_progress_3s
                        None,  # local_cost_nano
                        None,  # local_data_cost_nano
                        None,  # local_effective_cost_nano
                        None,  # local_effective_data_cost_nano
                        None,  # local_license_fee_nano
                        None,  # local_margin_nano
                    ),
                    (row.conversions, row.postclick_source),
                )

    def get_postclickstats_query_results(self, c, date):
        sql, params = self.prepare_postclickstats_query(date)

        c.execute(sql, params)
        return db.xnamedtuplefetchall(c)

    def prepare_postclickstats_query(self, date):
        sql = backtosql.generate_sql(
            "etl_breakdown_simple_one_day.sql",
            {
                "breakdown": models.K1PostclickStats().get_breakdown(
                    ["ad_group_id", "postclick_source", "content_ad_id", "source_slug", "publisher"]
                ),
                "aggregates": models.K1PostclickStats().get_aggregates(),
                "table": "postclickstats",
                "account_id": self.account_id,
            },
        )

        return sql, self._add_ad_group_id_param({"date": date})
