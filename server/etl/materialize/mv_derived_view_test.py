import datetime

import mock
from django.test import TestCase

import backtosql

from .mv_derived_view import MasterDerivedView
from .mv_derived_view import TouchpointConversionsDerivedView


@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
class DerivedMaterializedViewTest(TestCase, backtosql.TestSQLMixin):
    def test_generate(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (5,)

        mv_cls = MasterDerivedView.create(
            table_name="newtable",
            breakdown=["date", "source_id", "account_id"],
            sortkey=["date", "source_id", "account_id"],
            distkey="source_id",
        )

        mv = mv_cls("jobid", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
                CREATE TABLE IF NOT EXISTS newtable (
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
                mock.call(backtosql.SQLMatcher("SELECT count(1) FROM newtable")),
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM newtable WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3)},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                INSERT INTO newtable
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
                WHERE (date>=%s AND date<=%s)
                GROUP BY date, source_id, account_id
                ORDER BY date, source_id, account_id
                );
                """
                    ),
                    [datetime.date(2016, 7, 1), datetime.date(2016, 7, 3)],
                ),
            ]
        )

    def test_generate_account_id(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (1,)

        mv_cls = MasterDerivedView.create(
            table_name="newtable",
            breakdown=["date", "source_id", "account_id"],
            sortkey=["date", "source_id", "account_id"],
            distkey="source_id",
        )

        mv = mv_cls("jobid", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(mock.ANY),
                mock.call(mock.ANY),
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM newtable WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;"
                    ),  # noqa
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3), "account_id": 1},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                INSERT INTO newtable
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
                WHERE (account_id=%s AND date>=%s AND date<=%s)
                GROUP BY date, source_id, account_id
                ORDER BY date, source_id, account_id
                );
                """
                    ),
                    [1, datetime.date(2016, 7, 1), datetime.date(2016, 7, 3)],
                ),
            ]
        )

    def test_generate_empty_table(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (0,)

        mv_cls = MasterDerivedView.create(
            table_name="newtable",
            breakdown=["date", "source_id", "account_id"],
            sortkey=["date", "source_id", "account_id"],
            distkey="source_id",
        )
        mv = mv_cls("jobid", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls(
            [mock.call(mock.ANY), mock.call(mock.ANY), mock.call(mock.ANY, [])]
        )

    def test_prepare_insert_query(self, mock_transaction, mock_cursor):
        touchpoint_view = TouchpointConversionsDerivedView.create(
            table_name="mv_derived", breakdown=["slug", "type"], sortkey=["slug"], distkey="content_ad_id"
        )
        touchpoint_view = touchpoint_view(123, "2019-05-19", "2019-05-22", account_id=1234)
        sql, params = touchpoint_view.prepare_insert_query("2019-05-19", "2019-05-22")
        self.assertEqual(
            sql,
            """INSERT INTO mv_derived
(
    slug, type,
    touchpoint_count, conversion_count, conversion_value_nano
)
(
    SELECT
        slug AS slug, type AS type,
        SUM(touchpoint_count) touchpoint_count, SUM(conversion_count) conversion_count, SUM(conversion_value_nano) conversion_value_nano
    FROM
        mv_touchpointconversions
    WHERE
        (account_id=%s AND date>=%s AND date<=%s)
    GROUP BY
        slug, type
    ORDER BY
        slug
);""",
        )
        self.assertEqual(params, [1234, "2019-05-19", "2019-05-22"])
