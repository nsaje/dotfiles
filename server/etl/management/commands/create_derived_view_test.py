import datetime

import mock
from django.test import TestCase

import backtosql
from etl.management.commands import create_derived_view
from etl.materialize.mv_derived_view import MasterDerivedView
from utils import dates_helper


class CreateDerivedViewTest(TestCase, backtosql.TestSQLMixin):
    @mock.patch("etl.management.commands.create_derived_view.STATS_DB_HOT_CLUSTER_MAX_DAYS", 20)
    @mock.patch("etl.management.commands.create_derived_view.STATS_DB_POSTGRES_MAX_DAYS", 10)
    @mock.patch("etl.management.commands.create_derived_view.STATS_DB_COLD_CLUSTER", "test_cold")
    @mock.patch("etl.management.commands.create_derived_view.STATS_DB_HOT_CLUSTER", "test_hot")
    @mock.patch("etl.management.commands.create_derived_view.STATS_DB_POSTGRES", ["test_pg_1", "test_pg_2"])
    @mock.patch("etl.management.commands.create_derived_view._update_mv_postgres")
    @mock.patch("etl.management.commands.create_derived_view._create_mv_postgres")
    @mock.patch("etl.management.commands.create_derived_view._update_mv_redshift")
    @mock.patch("etl.management.commands.create_derived_view._create_mv_redshift")
    @mock.patch("etl.refresh.generate_job_id", return_value="jobid")
    def test_create_derived_view(self, mock_job_id, mock_create_rs, mock_update_rs, mock_create_pg, mock_update_pg):
        local_today = dates_helper.local_today()
        redshift_from = local_today - datetime.timedelta(20)
        postgres_from = local_today - datetime.timedelta(10)
        mv_class = create_derived_view._get_mv_class("mv_account")
        create_derived_view.create_derived_view("mv_account")

        mock_create_rs.assert_has_calls(
            [mock.call("jobid", mv_class, "test_cold", backfill_data=True), mock.call("jobid", mv_class, "test_hot")]
        )
        mock_update_rs.assert_called_with("jobid", mv_class, redshift_from, local_today, "test_cold", "test_hot")
        mock_create_pg.assert_has_calls(
            [mock.call("jobid", mv_class, db_name) for db_name in ["test_pg_1", "test_pg_2"]]
        )
        mock_update_pg.assert_has_calls(
            [
                mock.call("jobid", mv_class, postgres_from, local_today, "test_cold", "test_pg_1", s3_path=None),
                mock.call("jobid", mv_class, postgres_from, local_today, "test_cold", "test_pg_2", s3_path=mock.ANY),
            ]
        )

    def test_get_mv_class(self):
        with self.assertRaises(Exception):
            create_derived_view._get_mv_class("mv_doesntexist")

        with self.assertRaises(Exception):
            create_derived_view._get_mv_class("mv_master")

        with self.assertRaises(Exception):
            create_derived_view._get_mv_class("mvh_source")

        mv_class = create_derived_view._get_mv_class("mv_account")
        self.assertEquals("mv_account", mv_class.TABLE_NAME)

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_create_mv_redshift_no_backfill(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (1,)

        mv_class = MasterDerivedView.create(
            table_name="new_table",
            breakdown=["date", "source_id", "account_id"],
            sortkey=["date", "source_id", "account_id"],
            distkey="source_id",
        )

        create_derived_view._create_mv_redshift("jobid", mv_class, "db_name", backfill_data=False)

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
                CREATE TABLE IF NOT EXISTS new_table (
                    date date not null encode delta,
                    source_id int2 encode zstd,
                    account_id integer encode zstd,

                    impressions integer encode zstd,
                    clicks integer encode zstd,
                    cost_nano bigint encode zstd,
                    data_cost_nano bigint encode zstd,
                    visits integer encode zstd,
                    new_visits integer encode zstd,
                    bounced_visits integer encode zstd,
                    pageviews integer encode zstd,
                    total_time_on_site integer encode zstd,
                    effective_cost_nano bigint encode zstd,
                    effective_data_cost_nano bigint encode zstd,
                    license_fee_nano bigint encode zstd,
                    margin_nano bigint encode zstd,
                    users integer encode lzo,
                    returning_users integer encode lzo,
                    video_start integer encode lzo,
                    video_first_quartile integer encode lzo,
                    video_midpoint integer encode lzo,
                    video_third_quartile integer encode lzo,
                    video_complete integer encode lzo,
                    video_progress_3s integer encode lzo,
                    local_cost_nano bigint encode zstd,
                    local_data_cost_nano bigint encode zstd,
                    local_effective_cost_nano bigint encode zstd,
                    local_effective_data_cost_nano bigint encode zstd,
                    local_license_fee_nano bigint encode zstd,
                    local_margin_nano bigint encode zstd,
                    mrc50_measurable integer encode AZ64,
                    mrc50_viewable integer encode AZ64,
                    mrc100_measurable integer encode AZ64,
                    mrc100_viewable integer encode AZ64,
                    vast4_measurable integer encode AZ64,
                    vast4_viewable integer encode AZ64,
                    ssp_cost_nano bigint encode AZ64,
                    local_ssp_cost_nano bigint encode AZ64
                )
                diststyle key distkey(source_id) sortkey(date, source_id, account_id)
                """
                    )
                )
            ]
        )

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_create_mv_redshift_backfill_not_empty(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (1,)

        mv_class = MasterDerivedView.create(
            table_name="new_table",
            breakdown=["date", "source_id", "account_id"],
            sortkey=["date", "source_id", "account_id"],
            distkey="source_id",
        )

        create_derived_view._create_mv_redshift("jobid", mv_class, "db_name", backfill_data=True)

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
                CREATE TABLE IF NOT EXISTS new_table (
                    date date not null encode delta,
                    source_id int2 encode zstd,
                    account_id integer encode zstd,

                    impressions integer encode zstd,
                    clicks integer encode zstd,
                    cost_nano bigint encode zstd,
                    data_cost_nano bigint encode zstd,
                    visits integer encode zstd,
                    new_visits integer encode zstd,
                    bounced_visits integer encode zstd,
                    pageviews integer encode zstd,
                    total_time_on_site integer encode zstd,
                    effective_cost_nano bigint encode zstd,
                    effective_data_cost_nano bigint encode zstd,
                    license_fee_nano bigint encode zstd,
                    margin_nano bigint encode zstd,
                    users integer encode lzo,
                    returning_users integer encode lzo,
                    video_start integer encode lzo,
                    video_first_quartile integer encode lzo,
                    video_midpoint integer encode lzo,
                    video_third_quartile integer encode lzo,
                    video_complete integer encode lzo,
                    video_progress_3s integer encode lzo,
                    local_cost_nano bigint encode zstd,
                    local_data_cost_nano bigint encode zstd,
                    local_effective_cost_nano bigint encode zstd,
                    local_effective_data_cost_nano bigint encode zstd,
                    local_license_fee_nano bigint encode zstd,
                    local_margin_nano bigint encode zstd,
                    mrc50_measurable integer encode AZ64,
                    mrc50_viewable integer encode AZ64,
                    mrc100_measurable integer encode AZ64,
                    mrc100_viewable integer encode AZ64,
                    vast4_measurable integer encode AZ64,
                    vast4_viewable integer encode AZ64,
                    ssp_cost_nano bigint encode AZ64,
                    local_ssp_cost_nano bigint encode AZ64
                )
                diststyle key distkey(source_id) sortkey(date, source_id, account_id)
                """
                    )
                ),
                mock.call(backtosql.SQLMatcher("SELECT count(1) FROM new_table")),
            ]
        )

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_create_mv_redshift_backfill(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (0,)

        mv_class = MasterDerivedView.create(
            table_name="new_table",
            breakdown=["date", "source_id", "account_id"],
            sortkey=["date", "source_id", "account_id"],
            distkey="source_id",
        )

        create_derived_view._create_mv_redshift("jobid", mv_class, "db_name", backfill_data=True)

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
                CREATE TABLE IF NOT EXISTS new_table (
                    date date not null encode delta,
                    source_id int2 encode zstd,
                    account_id integer encode zstd,

                    impressions integer encode zstd,
                    clicks integer encode zstd,
                    cost_nano bigint encode zstd,
                    data_cost_nano bigint encode zstd,
                    visits integer encode zstd,
                    new_visits integer encode zstd,
                    bounced_visits integer encode zstd,
                    pageviews integer encode zstd,
                    total_time_on_site integer encode zstd,
                    effective_cost_nano bigint encode zstd,
                    effective_data_cost_nano bigint encode zstd,
                    license_fee_nano bigint encode zstd,
                    margin_nano bigint encode zstd,
                    users integer encode lzo,
                    returning_users integer encode lzo,
                    video_start integer encode lzo,
                    video_first_quartile integer encode lzo,
                    video_midpoint integer encode lzo,
                    video_third_quartile integer encode lzo,
                    video_complete integer encode lzo,
                    video_progress_3s integer encode lzo,
                    local_cost_nano bigint encode zstd,
                    local_data_cost_nano bigint encode zstd,
                    local_effective_cost_nano bigint encode zstd,
                    local_effective_data_cost_nano bigint encode zstd,
                    local_license_fee_nano bigint encode zstd,
                    local_margin_nano bigint encode zstd,
                    mrc50_measurable integer encode AZ64,
                    mrc50_viewable integer encode AZ64,
                    mrc100_measurable integer encode AZ64,
                    mrc100_viewable integer encode AZ64,
                    vast4_measurable integer encode AZ64,
                    vast4_viewable integer encode AZ64,
                    ssp_cost_nano bigint encode AZ64,
                    local_ssp_cost_nano bigint encode AZ64
                )
                diststyle key distkey(source_id) sortkey(date, source_id, account_id)
                """
                    )
                ),
                mock.call(backtosql.SQLMatcher("SELECT count(1) FROM new_table")),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                INSERT INTO new_table
                (
                    date,
                    source_id,
                    account_id,

                    impressions,
                    clicks,
                    cost_nano,
                    data_cost_nano,
                    visits,
                    new_visits,
                    bounced_visits,
                    pageviews,
                    total_time_on_site,
                    effective_cost_nano,
                    effective_data_cost_nano,
                    license_fee_nano,
                    margin_nano,
                    users,
                    returning_users,
                    video_start,
                    video_first_quartile,
                    video_midpoint,
                    video_third_quartile,
                    video_complete,
                    video_progress_3s,
                    local_cost_nano,
                    local_data_cost_nano,
                    local_effective_cost_nano,
                    local_effective_data_cost_nano,
                    local_license_fee_nano,
                    local_margin_nano,
                    mrc50_measurable,
                    mrc50_viewable,
                    mrc100_measurable,
                    mrc100_viewable,
                    vast4_measurable,
                    vast4_viewable,
                    ssp_cost_nano,
                    local_ssp_cost_nano
                )
                (SELECT
                    date AS date,
                    source_id AS source_id,
                    account_id AS account_id,

                    SUM(impressions) impressions,
                    SUM(clicks) clicks,
                    SUM(cost_nano) cost_nano,
                    SUM(data_cost_nano) data_cost_nano,
                    SUM(visits) visits,
                    SUM(new_visits) new_visits,
                    SUM(bounced_visits) bounced_visits,
                    SUM(pageviews) pageviews,
                    SUM(total_time_on_site) total_time_on_site,
                    SUM(effective_cost_nano) effective_cost_nano,
                    SUM(effective_data_cost_nano) effective_data_cost_nano,
                    SUM(license_fee_nano) license_fee_nano,
                    SUM(margin_nano) margin_nano,
                    SUM(users) users,
                    SUM(returning_users) returning_users,
                    SUM(video_start) video_start,
                    SUM(video_first_quartile) video_first_quartile,
                    SUM(video_midpoint) video_midpoint,
                    SUM(video_third_quartile) video_third_quartile,
                    SUM(video_complete) video_complete,
                    SUM(video_progress_3s) video_progress_3s,
                    SUM(local_cost_nano) local_cost_nano,
                    SUM(local_data_cost_nano) local_data_cost_nano,
                    SUM(local_effective_cost_nano) local_effective_cost_nano,
                    SUM(local_effective_data_cost_nano) local_effective_data_cost_nano,
                    SUM(local_license_fee_nano) local_license_fee_nano,
                    SUM(local_margin_nano) local_margin_nano,
                    SUM(mrc50_measurable) mrc50_measurable,
                    SUM(mrc50_viewable) mrc50_viewable,
                    SUM(mrc100_measurable) mrc100_measurable,
                    SUM(mrc100_viewable) mrc100_viewable,
                    SUM(vast4_measurable) vast4_measurable,
                    SUM(vast4_viewable) vast4_viewable,
                    SUM(ssp_cost_nano) ssp_cost_nano,
                    SUM(local_ssp_cost_nano) local_ssp_cost_nano
                FROM mv_master
                WHERE 1=1
                GROUP BY date, source_id, account_id
                ORDER BY date, source_id, account_id
                );
                """
                    ),
                    [],
                ),
            ]
        )

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_create_mv_postgres(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (1,)

        mv_class = MasterDerivedView.create(
            table_name="new_table",
            breakdown=["date", "source_id", "account_id"],
            sortkey=["date", "source_id", "account_id"],
            distkey="source_id",
        )

        create_derived_view._create_mv_postgres("jobid", mv_class, "db_name")

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
                CREATE TABLE IF NOT EXISTS new_table (
                    date date not null,
                    source_id int2,
                    account_id integer,

                    impressions integer,
                    clicks integer,
                    cost_nano bigint,
                    data_cost_nano bigint,
                    visits integer,
                    new_visits integer,
                    bounced_visits integer,
                    pageviews integer,
                    total_time_on_site integer,
                    effective_cost_nano bigint,
                    effective_data_cost_nano bigint,
                    license_fee_nano bigint,
                    margin_nano bigint,
                    users integer,
                    returning_users integer,
                    video_start integer,
                    video_first_quartile integer,
                    video_midpoint integer,
                    video_third_quartile integer,
                    video_complete integer,
                    video_progress_3s integer,
                    local_cost_nano bigint,
                    local_data_cost_nano bigint,
                    local_effective_cost_nano bigint,
                    local_effective_data_cost_nano bigint,
                    local_license_fee_nano bigint,
                    local_margin_nano bigint,
                    mrc50_measurable integer,
                    mrc50_viewable integer,
                    mrc100_measurable integer,
                    mrc100_viewable integer,
                    vast4_measurable integer,
                    vast4_viewable integer,
                    ssp_cost_nano bigint,
                    local_ssp_cost_nano bigint
                );
                CREATE INDEX IF NOT EXISTS new_table_main_idx ON new_table (source_id, account_id, date);
                """
                    )
                )
            ]
        )

    @mock.patch("etl.redshift.update_table_from_s3")
    @mock.patch("etl.redshift.unload_table")
    def test_update_mv_redshift(self, mock_unload, mock_s3):
        mock_unload.return_value = "s3_path"
        mv_class = create_derived_view._get_mv_class("mv_account")
        date_from = datetime.datetime(2020, 1, 1)
        date_to = datetime.datetime(2020, 1, 2)
        create_derived_view._update_mv_redshift("jobid", mv_class, date_from, date_to, "source_db", "dest_db")
        mock_unload.assert_called_with("jobid", mv_class.TABLE_NAME, date_from, date_to, db_name="source_db")
        mock_s3.assert_called_with("dest_db", "s3_path", mv_class.TABLE_NAME, date_from, date_to)

    @mock.patch("etl.redshift.update_table_from_s3_postgres")
    @mock.patch("etl.redshift.unload_table")
    def test_update_mv_postgres(self, mock_unload, mock_s3):
        mock_unload.return_value = "s3_path"
        mv_class = create_derived_view._get_mv_class("mv_account")
        date_from = datetime.datetime(2020, 1, 1)
        date_to = datetime.datetime(2020, 1, 2)
        create_derived_view._update_mv_postgres("jobid", mv_class, date_from, date_to, "source_db", "dest_db")
        mock_unload.assert_called_with("jobid", mv_class.TABLE_NAME, date_from, date_to, db_name="source_db")
        mock_s3.assert_called_with("dest_db", "s3_path", mv_class.TABLE_NAME, date_from, date_to)
