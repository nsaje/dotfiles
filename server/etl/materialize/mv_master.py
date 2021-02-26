import datetime
from collections import defaultdict
from functools import partial

from dateutil import rrule

import backtosql
import dash.models
from core.features import source_groups
from etl import helpers
from etl import models
from etl import redshift
from etl import s3
from redshiftapi import db
from utils import zlogging

from .materialize import Materialize

logger = zlogging.getLogger(__name__)


class MasterView(Materialize):
    """
    Represents breakdown by all dimensions available. It containts traffic, postclick, conversions
    and tochpoint conversions data.
    """

    TABLE_NAME = "mv_master"

    def generate(self, **kwargs):
        self.prefetch()

        for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):

            date = date.date()

            with db.get_write_stats_transaction():
                with db.get_write_stats_cursor() as c:
                    logger.info("Deleting data from table", table=self.TABLE_NAME, date=date, job=self.job_id)
                    sql, params = redshift.prepare_daily_delete_query(self.TABLE_NAME, date, self.account_id)
                    c.execute(sql, params)

                    logger.info(
                        "Running insert traffic data into table", table=self.TABLE_NAME, date=date, job=self.job_id
                    )
                    sql, params = self.prepare_insert_traffic_data_query(date)
                    c.execute(sql, params)

                    # generate csv in transaction as it needs data created in it
                    s3_path = s3.upload_csv(self.TABLE_NAME, date, self.job_id, partial(self.generate_rows, c, date))

                    logger.info("Copying CSV to table", table=self.TABLE_NAME, date=date, job=self.job_id)
                    sql, params = redshift.prepare_copy_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

    def generate_rows(self, cursor, date):
        for _, row, _ in self.get_postclickstats(cursor, date):
            yield row

    def prepare_insert_traffic_data_query(self, date):
        params = helpers.get_local_date_context(date)

        sql = backtosql.generate_sql(
            "etl_insert_mv_master_stats.sql",
            {"account_id": self.account_id, "valid_environments": dash.constants.Environment.get_all()},
        )

        params = self._add_account_id_param(params)
        params = self._add_ad_group_id_param(params)

        return sql, params

    def prefetch(self):
        ad_groups_qs = dash.models.AdGroup.objects.all()
        if self.account_id:
            ad_groups_qs = ad_groups_qs.filter(campaign__account_id=self.account_id)
        self.ad_groups_parents_map = {
            x["id"]: (x["campaign_id"], x["campaign__account_id"], x["campaign__account__agency__uses_source_groups"])
            for x in ad_groups_qs.values(
                "id", "campaign_id", "campaign__account_id", "campaign__account__agency__uses_source_groups"
            ).iterator()
        }

        sources_qs = dash.models.Source.objects.all()
        self.sources_slug_map = {
            helpers.extract_source_slug(x["bidder_slug"]): x["id"] for x in sources_qs.values("id", "bidder_slug")
        }

    def get_postclickstats(self, cursor, date):
        grouped_sources = source_groups.get_source_id_group_id_mapping()

        # group postclick rows by ad group and postclick source
        rows_by_ad_group = defaultdict(lambda: defaultdict(list))
        for row in self.get_postclickstats_query_results(cursor, date):
            postclick_source = helpers.extract_postclick_source(row.postclick_source)
            rows_by_ad_group[row.ad_group_id][postclick_source].append(row)
        for ad_group_id, rows_by_postclick_source in rows_by_ad_group.items():
            if len(list(rows_by_postclick_source.keys())) > 1:
                logger.info(
                    "Postclick stats for a single ad group from different sources",
                    ad_group=ad_group_id,
                    sources=list(rows_by_postclick_source.keys()),
                    date=date,
                )

            rows = helpers.get_highest_priority_postclick_source(rows_by_postclick_source)

            for row in rows:
                source_slug = helpers.extract_source_slug(row.source_slug)
                if source_slug not in self.sources_slug_map:
                    logger.info("Got postclick stats for unknown source", source=row.source_slug)
                    continue

                if row.ad_group_id not in self.ad_groups_parents_map:
                    logger.info("Got postclick stats for unknown ad group", ad_group=row.ad_group_id)
                    continue

                ad_group_id = row.ad_group_id
                campaign_id, account_id, uses_source_groups = self.ad_groups_parents_map[ad_group_id]
                source_id = self.sources_slug_map[source_slug]
                if date > datetime.date(2022, 1, 1) and uses_source_groups:  # Date will be changed when merged
                    parent_source_id = grouped_sources.get(source_id, source_id)
                else:
                    parent_source_id = source_id

                returning_users = helpers.calculate_returning_users(row.users, row.new_visits)

                publisher = row.publisher
                if publisher and source_id:
                    publisher = publisher.lower()

                yield (
                    helpers.get_breakdown_key_for_postclickstats(parent_source_id, row.content_ad_id),
                    (
                        date,
                        parent_source_id,
                        account_id,
                        campaign_id,
                        ad_group_id,
                        row.content_ad_id,
                        publisher,
                        "{}__{}".format(publisher if publisher else "", source_id),  # publisher_source_id
                        dash.constants.DeviceType.UNKNOWN,
                        None,  # device_os
                        None,  # device_os_version
                        dash.constants.Environment.UNKNOWN,
                        dash.constants.ZemPlacementType.UNKNOWN,
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
                        None,  # mrc50_measurable
                        None,  # mrc50_viewable
                        None,  # mrc100_measurable
                        None,  # mrc100_viewable
                        None,  # vast4_measurable
                        None,  # vast4_viewable
                        0,  # ssp_cost_nano
                        0,  # local_ssp_cost_nano
                        0,  # base_effective_cost_nano
                        0,  # base_effective_data_cost_nano
                        0,  # service_fee_nano
                        0,  # local_base_effective_cost_nano
                        0,  # local_base_effective_data_cost_nano
                        0,  # local_service_fee_nano,
                        dash.constants.BrowserFamily.UNKNOWN,
                        dash.constants.ConnectionType.UNKNOWN,
                        None,  # outbrain_publisher_id
                        None,  # outbrain_section_id
                        source_id,  # original_source_id
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
