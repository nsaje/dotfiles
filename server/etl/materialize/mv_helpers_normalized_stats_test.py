import datetime

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql
import dash.constants
from utils import test_helper

from .mv_helpers_normalized_stats import MVHelpersNormalizedStats


@mock.patch("backtosql.generate_sql", wraps=backtosql.generate_sql)
@mock.patch("etl.redshift.unload_table_tz")
@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
@override_settings(S3_BUCKET_STATS="test-bucket")
class MVHNormalizedStatsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    def test_generate(self, mock_transaction, mock_cursor, mock_unload, mock_backtosql):
        spark_session = mock.MagicMock()
        mv = MVHelpersNormalizedStats(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None, spark_session=spark_session
        )

        mv.generate()

        mock_unload.assert_called_once_with(
            "asd", "stats", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), prefix="spark", account_id=None
        )
        mock_backtosql.assert_any_call(
            "etl_spark_mvh_clean_stats.sql",
            {
                "account_id": None,
                "yahoo_slug": "yahoo",
                "outbrain_slug": "outbrain",
                "valid_placement_mediums": dash.constants.PlacementMedium.get_all(),
                "tzhour_from": 4,
                "tzhour_to": 4,
                "tzdate_from": "2016-07-01",
                "tzdate_to": "2016-07-04",
                "date_from": "2016-07-01",
                "date_to": "2016-07-03",
                "date_ranges": [
                    {
                        "date": "2016-07-01",
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-02",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-02",
                        "tzdate_from": "2016-07-02",
                        "tzdate_to": "2016-07-03",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-03",
                        "tzdate_from": "2016-07-03",
                        "tzdate_to": "2016-07-04",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                ],
            },
        )
        expected_sql = """
            SELECT
            CASE
                WHEN hour is null THEN date

                WHEN hour is not null AND (
                    (date='2016-07-01' AND hour >= 4) OR
                    (date='2016-07-02' AND hour < 4)
                )
                THEN '2016-07-01'

                WHEN hour is not null AND (
                    (date='2016-07-02' AND hour >= 4) OR
                    (date='2016-07-03' AND hour < 4)
                )
                THEN '2016-07-02'

                WHEN hour is not null AND (
                    (date='2016-07-03' AND hour >= 4) OR
                    (date='2016-07-04' AND hour < 4)
                )
                THEN '2016-07-03'

            END as date,
            stats.media_source as source_slug,

            ad_group_id,
            content_ad_id,
            -- no outbrain publishers here
            CASE
                WHEN media_source = 'yahoo' THEN 'all publishers'
                WHEN media_source = 'outbrain' THEN NULL  -- special case for outbrain to avoid coalesce and spark bug
                ELSE COALESCE(LOWER(publisher), '')  -- coalesce is here for spark bug treating empty values as null in input csv
            END as publisher,

            CASE WHEN device_type = 1 THEN 4  -- convert legacy OpenRTB `mobile` to `phone`
                WHEN device_type = 6 THEN 3
                WHEN device_type = 7 THEN 3
                ELSE NULLIF(device_type, 0)
            END AS device_type,
            CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
                WHEN LOWER(device_os) LIKE LOWER('%%unknown%%') THEN NULL
                WHEN LOWER(device_os) LIKE LOWER('Android%%') THEN 'Android'
                WHEN LOWER(device_os) LIKE LOWER('iOS%%') THEN 'iOS'
                WHEN LOWER(device_os) LIKE LOWER('WinPhone%%') THEN 'WinPhone'
                WHEN LOWER(device_os) LIKE LOWER('WinRT%%') THEN 'WinRT'
                WHEN LOWER(device_os) LIKE LOWER('Windows%%') THEN 'Windows'
                WHEN LOWER(device_os) LIKE LOWER('MacOSX%%') THEN 'macOS'
                WHEN LOWER(device_os) LIKE LOWER('macOS%%') THEN 'macOS'
                WHEN device_os IN ('Linux', 'Ubuntu', 'Debian', 'Fedora') THEN 'Linux'
                WHEN LOWER(device_os) LIKE LOWER('ChromeOS') THEN 'ChromeOS'
                WHEN NULLIF(TRIM(device_os), '') IS NOT NULL THEN 'Other'

            ELSE NULL
            END AS device_os,
            CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
                WHEN LOWER(device_os_version) LIKE LOWER('%%unknown%%') THEN NULL
                WHEN LOWER(device_os_version) LIKE LOWER('Android%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('iOS%%') THEN REPLACE(device_os_version, ';', '')  -- some special case
                WHEN LOWER(device_os_version) LIKE LOWER('WinPhone%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('WinRT%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('Windows%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('MacOS%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('ChromeOS%%') THEN device_os_version
                WHEN NULLIF(TRIM(device_os_version), '') IS NOT NULL THEN 'Other'
                ELSE NULL
            END AS device_os_version,

            CASE WHEN placement_medium IN (


                            'None',



                            'app',



                            'site'


                ) THEN placement_medium
                ELSE NULL
            END as placement_medium,

            NULLIF(placement_type, 0) as placement_type,
            NULLIF(video_playback_method, 0) as video_playback_method,

            NULLIF(TRIM(UPPER(country)), '') AS country,
            CASE WHEN state LIKE '%%-%%' THEN NULLIF(TRIM(UPPER(state)), '')
                ELSE NULLIF(TRIM(UPPER(country)), '') || '-' || NULLIF(TRIM(UPPER(state)), '')
            END AS state,
            CASE WHEN country LIKE 'US' AND dma BETWEEN 500 AND 882 THEN dma
                ELSE NULL
            END AS dma,
            NULLIF(city_id, 0) AS city_id,

            NULLIF(TRIM(LOWER(age)), '') as age,
            NULLIF(TRIM(LOWER(gender)), '') as gender,

            NULLIF(TRIM(LOWER(age)), '') || ' ' || COALESCE(TRIM(LOWER(gender)), '') AS age_gender,

            SUM(impressions) as impressions,
            SUM(clicks) as clicks,
            SUM(spend) as spend,
            SUM(data_spend) as data_spend,
            SUM(video_start) as video_start,
            SUM(video_first_quartile) as video_first_quartile,
            SUM(video_midpoint) as video_midpoint,
            SUM(video_third_quartile) as video_third_quartile,
            SUM(video_complete) as video_complete,
            SUM(video_progress_3s) as video_progress_3s
            FROM stats
            WHERE
            ((hour is null and date>='2016-07-01' AND date<='2016-07-03')
            OR
            (hour is not null and date>'2016-07-01' AND date<'2016-07-04')
            OR
            (hour IS NOT NULL AND (
                (date='2016-07-01' AND hour >= '4') OR
                (date='2016-07-04' AND hour < '4')
            )))

            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18
            ORDER BY 1, 2, 3, 4, 5
        """
        spark_session.run_file.assert_called_once_with(
            "mvh_clean_stats.py",
            bucket="test-bucket",
            input_table="stats",
            output_table="mvh_clean_stats",
            prefix="spark",
            sql=backtosql.SQLMatcher(expected_sql),
            job_id="asd",
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(mock.ANY),
                mock.call(
                    mock.ANY,
                    {
                        "s3_url": "s3://test-bucket/spark/asd/mvh_clean_stats",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    def test_generate_account_id(self, mock_transaction, mock_cursor, mock_unload, mock_backtosql):
        spark_session = mock.MagicMock()
        mv = MVHelpersNormalizedStats(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1, spark_session=spark_session
        )

        mv.generate()
        mock_unload.assert_called_once_with(
            "asd", "stats", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), prefix="spark", account_id=1
        )
        mock_backtosql.assert_any_call(
            "etl_spark_mvh_clean_stats.sql",
            {
                "account_id": 1,
                "ad_group_id": test_helper.ListMatcher([1, 3, 4]),
                "yahoo_slug": "yahoo",
                "outbrain_slug": "outbrain",
                "valid_placement_mediums": dash.constants.PlacementMedium.get_all(),
                "tzhour_from": 4,
                "tzhour_to": 4,
                "tzdate_from": "2016-07-01",
                "tzdate_to": "2016-07-04",
                "date_from": "2016-07-01",
                "date_to": "2016-07-03",
                "date_ranges": [
                    {
                        "date": "2016-07-01",
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-02",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-02",
                        "tzdate_from": "2016-07-02",
                        "tzdate_to": "2016-07-03",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-03",
                        "tzdate_from": "2016-07-03",
                        "tzdate_to": "2016-07-04",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                ],
            },
        )
        expected_sql = """
            SELECT
            CASE
                WHEN hour is null THEN date

                WHEN hour is not null AND (
                    (date='2016-07-01' AND hour >= 4) OR
                    (date='2016-07-02' AND hour < 4)
                )
                THEN '2016-07-01'

                WHEN hour is not null AND (
                    (date='2016-07-02' AND hour >= 4) OR
                    (date='2016-07-03' AND hour < 4)
                )
                THEN '2016-07-02'

                WHEN hour is not null AND (
                    (date='2016-07-03' AND hour >= 4) OR
                    (date='2016-07-04' AND hour < 4)
                )
                THEN '2016-07-03'

            END as date,
            stats.media_source as source_slug,

            ad_group_id,
            content_ad_id,
            -- no outbrain publishers here
            CASE
                WHEN media_source = 'yahoo' THEN 'all publishers'
                WHEN media_source = 'outbrain' THEN NULL  -- special case for outbrain to avoid coalesce and spark bug
                ELSE COALESCE(LOWER(publisher), '')  -- coalesce is here for spark bug treating empty values as null in input csv
            END as publisher,

            CASE WHEN device_type = 1 THEN 4  -- convert legacy OpenRTB `mobile` to `phone`
                WHEN device_type = 6 THEN 3
                WHEN device_type = 7 THEN 3
                ELSE NULLIF(device_type, 0)
            END AS device_type,
            CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
                WHEN LOWER(device_os) LIKE LOWER('%%unknown%%') THEN NULL
                WHEN LOWER(device_os) LIKE LOWER('Android%%') THEN 'Android'
                WHEN LOWER(device_os) LIKE LOWER('iOS%%') THEN 'iOS'
                WHEN LOWER(device_os) LIKE LOWER('WinPhone%%') THEN 'WinPhone'
                WHEN LOWER(device_os) LIKE LOWER('WinRT%%') THEN 'WinRT'
                WHEN LOWER(device_os) LIKE LOWER('Windows%%') THEN 'Windows'
                WHEN LOWER(device_os) LIKE LOWER('MacOSX%%') THEN 'macOS'
                WHEN LOWER(device_os) LIKE LOWER('macOS%%') THEN 'macOS'
                WHEN device_os IN ('Linux', 'Ubuntu', 'Debian', 'Fedora') THEN 'Linux'
                WHEN LOWER(device_os) LIKE LOWER('ChromeOS') THEN 'ChromeOS'
                WHEN NULLIF(TRIM(device_os), '') IS NOT NULL THEN 'Other'

            ELSE NULL
            END AS device_os,
            CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
                WHEN LOWER(device_os_version) LIKE LOWER('%%unknown%%') THEN NULL
                WHEN LOWER(device_os_version) LIKE LOWER('Android%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('iOS%%') THEN REPLACE(device_os_version, ';', '')  -- some special case
                WHEN LOWER(device_os_version) LIKE LOWER('WinPhone%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('WinRT%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('Windows%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('MacOS%%') THEN device_os_version
                WHEN LOWER(device_os_version) LIKE LOWER('ChromeOS%%') THEN device_os_version
                WHEN NULLIF(TRIM(device_os_version), '') IS NOT NULL THEN 'Other'
                ELSE NULL
            END AS device_os_version,

            CASE WHEN placement_medium IN (


                            'None',



                            'app',



                            'site'


                ) THEN placement_medium
                ELSE NULL
            END as placement_medium,

            NULLIF(placement_type, 0) as placement_type,
            NULLIF(video_playback_method, 0) as video_playback_method,

            NULLIF(TRIM(UPPER(country)), '') AS country,
            CASE WHEN state LIKE '%%-%%' THEN NULLIF(TRIM(UPPER(state)), '')
                ELSE NULLIF(TRIM(UPPER(country)), '') || '-' || NULLIF(TRIM(UPPER(state)), '')
            END AS state,
            CASE WHEN country LIKE 'US' AND dma BETWEEN 500 AND 882 THEN dma
                ELSE NULL
            END AS dma,
            NULLIF(city_id, 0) AS city_id,

            NULLIF(TRIM(LOWER(age)), '') as age,
            NULLIF(TRIM(LOWER(gender)), '') as gender,

            NULLIF(TRIM(LOWER(age)), '') || ' ' || COALESCE(TRIM(LOWER(gender)), '') AS age_gender,

            SUM(impressions) as impressions,
            SUM(clicks) as clicks,
            SUM(spend) as spend,
            SUM(data_spend) as data_spend,
            SUM(video_start) as video_start,
            SUM(video_first_quartile) as video_first_quartile,
            SUM(video_midpoint) as video_midpoint,
            SUM(video_third_quartile) as video_third_quartile,
            SUM(video_complete) as video_complete,
            SUM(video_progress_3s) as video_progress_3s
            FROM stats
            WHERE
            ((hour is null and date>='2016-07-01' AND date<='2016-07-03')
            OR
            (hour is not null and date>'2016-07-01' AND date<'2016-07-04')
            OR
            (hour IS NOT NULL AND (
                (date='2016-07-01' AND hour >= '4') OR
                (date='2016-07-04' AND hour < '4')
            )))


                AND ad_group_id IN (1,3,4)

            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18
            ORDER BY 1, 2, 3, 4, 5
        """
        spark_session.run_file.assert_called_once_with(
            "mvh_clean_stats.py",
            bucket="test-bucket",
            input_table="stats",
            output_table="mvh_clean_stats",
            prefix="spark",
            sql=backtosql.SQLMatcher(expected_sql),
            job_id="asd",
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(mock.ANY),
                mock.call(
                    mock.ANY,
                    {
                        "s3_url": "s3://test-bucket/spark/asd/mvh_clean_stats",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
