import collections
import backtosql
import datetime
import mock
import textwrap

from django.test import TestCase, override_settings

from dash import models
from dash import constants

from utils import test_helper

from etl import materialize_views


PostclickstatsResults = collections.namedtuple('Result2',
                                               ['ad_group_id', 'postclick_source', 'content_ad_id', 'source_slug',
                                                'publisher', 'bounced_visits', 'conversions', 'new_visits', 'pageviews',
                                                'total_time_on_site', 'visits', 'users'])


@mock.patch('redshiftapi.db.get_write_stats_cursor')
@mock.patch('redshiftapi.db.get_write_stats_transaction')
@mock.patch('utils.s3helpers.S3Helper')
class MVHSourceTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersSource('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_source/2016/07/03/mvh_source_asd.csv",
            textwrap.dedent("""\
            1\tadblade\tadblade\r
            2\tadiant\tadiant\r
            3\toutbrain\toutbrain\r
            4\tyahoo\tyahoo\r
            """))

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_source (
                source_id int2 encode bytedict,
                bidder_slug varchar(127) encode lzo,
                clean_slug varchar(127) encode lzo
            ) sortkey(bidder_slug);""")),
            mock.call(backtosql.SQLMatcher("""
            COPY mvh_source
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            CREDENTIALS %(credentials)s
            MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mvh_source/2016/07/03/mvh_source_asd.csv',
                'delimiter': '\t',
            })
        ])


@mock.patch('redshiftapi.db.get_write_stats_cursor')
@mock.patch('redshiftapi.db.get_write_stats_transaction')
@mock.patch('utils.s3helpers.S3Helper')
class MVHCampaignFactorsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersCampaignFactors('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 2), account_id=None)

        mv.generate(campaign_factors={
            datetime.date(2016, 7, 1): {
                models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.25),
                models.Campaign.objects.get(pk=2): (0.2, 0.2, 0.25),
            },
            datetime.date(2016, 7, 2): {
                models.Campaign.objects.get(pk=1): (1.0, 0.3, 0.25),
                models.Campaign.objects.get(pk=2): (0.2, 0.3, 0.25),
            },
        })

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv",
            textwrap.dedent("""\
            2016-07-01\t1\t1.0\t0.2\t0.25\r
            2016-07-01\t2\t0.2\t0.2\t0.25\r
            2016-07-02\t1\t1.0\t0.3\t0.25\r
            2016-07-02\t2\t0.2\t0.3\t0.25\r
            """))

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_campaign_factors (
                date date not null encode delta,
                campaign_id int2 not null encode lzo,

                pct_actual_spend decimal(22, 18) encode lzo,
                pct_license_fee decimal(22, 18) encode lzo,
                pct_margin decimal(22, 18) encode lzo
            ) sortkey(date, campaign_id)""")),
            mock.call(backtosql.SQLMatcher("""
            COPY mvh_campaign_factors
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            CREDENTIALS %(credentials)s
            MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': ('s3://test_bucket/materialized_views/'
                           'mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv'),
                'delimiter': '\t',
            })
        ])

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    def test_generate_checks_range_continuation(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersCampaignFactors('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        with self.assertRaises(Exception):
            mv.generate(campaign_factors={
                datetime.date(2016, 7, 1): {
                    models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.25),
                    models.Campaign.objects.get(pk=2): (0.2, 0.2, 0.25),
                },
                # missing for 2016-07-02
                datetime.date(2016, 7, 3): {
                    models.Campaign.objects.get(pk=1): (1.0, 0.3, 0.25),
                    models.Campaign.objects.get(pk=2): (0.2, 0.3, 0.25),
                },
            })

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    def test_generate_account_id(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersCampaignFactors(
            'asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 2), account_id=1)

        mv.generate(campaign_factors={
            datetime.date(2016, 7, 1): {
                models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.25),
            },
            datetime.date(2016, 7, 2): {
                models.Campaign.objects.get(pk=1): (1.0, 0.3, 0.25),
            },
        })

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv",
            textwrap.dedent("""\
            2016-07-01\t1\t1.0\t0.2\t0.25\r
            2016-07-02\t1\t1.0\t0.3\t0.25\r
            """))

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_campaign_factors (
                date date not null encode delta,
                campaign_id int2 not null encode lzo,

                pct_actual_spend decimal(22, 18) encode lzo,
                pct_license_fee decimal(22, 18) encode lzo,
                pct_margin decimal(22, 18) encode lzo
            ) sortkey(date, campaign_id)""")),
            mock.call(backtosql.SQLMatcher("""
            COPY mvh_campaign_factors
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            CREDENTIALS %(credentials)s
            MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv',
                'delimiter': '\t',
            })
        ])


@mock.patch('redshiftapi.db.get_write_stats_cursor')
@mock.patch('redshiftapi.db.get_write_stats_transaction')
@mock.patch('utils.s3helpers.S3Helper')
class MVHAdGroupStructureTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersAdGroupStructure('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv",
            textwrap.dedent("""\
            1\t1\t1\t1\r
            1\t2\t2\t2\r
            1\t1\t3\t3\r
            1\t1\t1\t4\r
            """))

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_adgroup_structure (
                agency_id integer encode lzo,
                account_id integer encode lzo,
                campaign_id integer encode lzo,
                ad_group_id integer encode lzo
            ) sortkey(ad_group_id, campaign_id, account_id, agency_id)""")),
            mock.call(backtosql.SQLMatcher("""
            COPY mvh_adgroup_structure
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            CREDENTIALS %(credentials)s
            MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': ('s3://test_bucket/materialized_views/'
                           'mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv'),
                'delimiter': '\t',
            })
        ])

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    def test_generate_account_id(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersAdGroupStructure(
            'asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()

        self.assertTrue(mock_s3helper.called)

        # only account_id=1 is used to generate CSV
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv",
            textwrap.dedent("""\
            1\t1\t1\t1\r
            1\t1\t3\t3\r
            1\t1\t1\t4\r
            """))

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_adgroup_structure (
                agency_id integer encode lzo,
                account_id integer encode lzo,
                campaign_id integer encode lzo,
                ad_group_id integer encode lzo
            ) sortkey(ad_group_id, campaign_id, account_id, agency_id)""")),
            mock.call(backtosql.SQLMatcher("""
            COPY mvh_adgroup_structure
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            CREDENTIALS %(credentials)s
            MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': ('s3://test_bucket/materialized_views/'
                           'mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv'),
                'delimiter': '\t',
            })
        ])


@mock.patch('redshiftapi.db.get_write_stats_cursor')
@mock.patch('redshiftapi.db.get_write_stats_transaction')
class MVHNormalizedStatsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_materialize_views']

    def test_generate(self, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersNormalizedStats('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_clean_stats (
                date date not null encode delta,
                source_slug varchar(127) encode lzo,

                ad_group_id integer encode lzo,
                content_ad_id integer encode lzo,
                publisher varchar(255) encode lzo,

                device_type int2 encode bytedict,
                country varchar(2) encode bytedict,
                state varchar(5) encode bytedict,
                dma int2 encode bytedict,
                city_id integer encode lzo,

                placement_type integer encode lzo,
                video_playback_method integer encode lzo,

                age int2 encode bytedict,
                gender int2 encode bytedict,
                age_gender int2 encode bytedict,

                impressions integer encode lzo,
                clicks integer encode lzo,
                spend bigint encode lzo,
                data_spend bigint encode lzo,

                video_start integer encode lzo,
                video_first_quartile integer encode lzo,
                video_midpoint integer encode lzo,
                video_third_quartile integer encode lzo,
                video_complete integer encode lzo,
                video_progress_3s integer encode lzo
            ) distkey(date) sortkey(date, source_slug, ad_group_id, content_ad_id, publisher)""")),
            mock.call(backtosql.SQLMatcher("""
            INSERT INTO mvh_clean_stats
                (SELECT
                    CASE WHEN hour is null THEN date
                         WHEN hour is not null
                             AND ((date='2016-07-01'::date AND hour >= 4)
                                 OR (date='2016-07-02'::date
                             AND hour < 4)) THEN '2016-07-01'::date
                         WHEN hour is not null
                           AND ((date='2016-07-02'::date
                                   AND hour >= 4)
                                   OR (date='2016-07-03'::date
                                       AND hour < 4)) THEN '2016-07-02'::date
                         WHEN hour is not null
                           AND ((date='2016-07-03'::date
                                   AND hour >= 4)
                                   OR (date='2016-07-04'::date
                                       AND hour < 4)) THEN '2016-07-03'::date
                    END as date,
                    stats.media_source as source_slug,
                    ad_group_id,
                    content_ad_id,
                    CASE
                        WHEN media_source = 'yahoo' THEN 'all publishers' ELSE LOWER(publisher)
                    END as publisher,
                    CASE
                        WHEN device_type = 4 THEN 3
                        WHEN device_type = 2 THEN 1
                        WHEN device_type = 5 THEN 2
                        ELSE 0
                    END as device_type,
                    CASE WHEN LEN(TRIM(country)) <= 2 THEN UPPER(TRIM(country))
                        ELSE NULL
                    END AS country,
                    CASE WHEN LEN(TRIM(state)) <= 5 THEN UPPER(TRIM(state))
                        ELSE NULL
                    END AS state,
                    CASE WHEN 499 < dma AND dma < 1000 THEN dma
                        ELSE NULL
                    END AS dma,
                    city_id,
                    placement_type,
                    video_playback_method,
                    CASE WHEN TRIM(age)='18-20' THEN 1
                        WHEN TRIM(age)='21-29' THEN 2
                        WHEN TRIM(age)='30-39' THEN 3
                        WHEN TRIM(age)='40-49' THEN 4
                        WHEN TRIM(age)='50-64' THEN 5
                        WHEN TRIM(age)='65+'   THEN 6
                        ELSE 0
                    END AS age,
                    CASE WHEN TRIM(LOWER(gender))='male'   THEN 1
                        WHEN TRIM(LOWER(gender))='female' THEN 2
                        ELSE 0
                    END AS gender,
                    CASE
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='18-20' THEN 1
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='18-20' THEN 2
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='18-20' THEN 3
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='21-29' THEN 4
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='21-29' THEN 5
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='21-29' THEN 6
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='30-39' THEN 7
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='30-39' THEN 8
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='30-39' THEN 9
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='40-49' THEN 10
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='40-49' THEN 11
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='40-49' THEN 12
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='50-64' THEN 13
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='50-64' THEN 14
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='50-64' THEN 15
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='65+'   THEN 16
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='65+'   THEN 17
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='65+'   THEN 18
                    ELSE 0
                    END AS age_gender,
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
                WHERE ((hour is null
                        and date>=%(date_from)s
                        AND date<=%(date_to)s)
                    OR (hour is not null
                        and date>%(tzdate_from)s
                        AND date<%(tzdate_to)s)
                    OR (hour IS NOT NULL
                        AND ((date=%(tzdate_from)s
                            AND hour >= %(tzhour_from)s)
                            OR (date=%(tzdate_to)s
                                AND hour < %(tzhour_to)s))))
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15);"""), {
                'tzhour_from': 4,
                'tzhour_to': 4,
                'tzdate_from': '2016-07-01',
                'tzdate_to': '2016-07-04',
                'date_from': '2016-07-01',
                'date_to': '2016-07-03'
            })
        ])

    def test_generate_account_id(self, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersNormalizedStats(
            'asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_clean_stats (
                date date not null encode delta,
                source_slug varchar(127) encode lzo,

                ad_group_id integer encode lzo,
                content_ad_id integer encode lzo,
                publisher varchar(255) encode lzo,

                device_type int2 encode bytedict,
                country varchar(2) encode bytedict,
                state varchar(5) encode bytedict,
                dma int2 encode bytedict,
                city_id integer encode lzo,

                placement_type integer encode lzo,
                video_playback_method integer encode lzo,

                age int2 encode bytedict,
                gender int2 encode bytedict,
                age_gender int2 encode bytedict,

                impressions integer encode lzo,
                clicks integer encode lzo,
                spend bigint encode lzo,
                data_spend bigint encode lzo,

                video_start integer encode lzo,
                video_first_quartile integer encode lzo,
                video_midpoint integer encode lzo,
                video_third_quartile integer encode lzo,
                video_complete integer encode lzo,
                video_progress_3s integer encode lzo
            ) distkey(date) sortkey(date, source_slug, ad_group_id, content_ad_id, publisher)""")),
            mock.call(
                backtosql.SQLMatcher("""
                INSERT INTO mvh_clean_stats
                (SELECT
                    CASE WHEN hour is null THEN date
                         WHEN hour is not null
                             AND ((date='2016-07-01'::date AND hour >= 4)
                                 OR (date='2016-07-02'::date
                             AND hour < 4)) THEN '2016-07-01'::date
                         WHEN hour is not null
                           AND ((date='2016-07-02'::date
                                   AND hour >= 4)
                                   OR (date='2016-07-03'::date
                                       AND hour < 4)) THEN '2016-07-02'::date
                         WHEN hour is not null
                           AND ((date='2016-07-03'::date
                                   AND hour >= 4)
                                   OR (date='2016-07-04'::date
                                       AND hour < 4)) THEN '2016-07-03'::date
                    END as date,
                    stats.media_source as source_slug,
                    ad_group_id,
                    content_ad_id,
                    CASE
                        WHEN media_source = 'yahoo' THEN 'all publishers' ELSE LOWER(publisher)
                    END as publisher,
                    CASE
                        WHEN device_type = 4 THEN 3
                        WHEN device_type = 2 THEN 1
                        WHEN device_type = 5 THEN 2
                        ELSE 0
                    END as device_type,

                    CASE WHEN LEN(TRIM(country)) <= 2 THEN UPPER(TRIM(country))
                        ELSE NULL
                    END AS country,
                    CASE WHEN LEN(TRIM(state)) <= 5 THEN UPPER(TRIM(state))
                        ELSE NULL
                    END AS state,
                    CASE WHEN 499 < dma AND dma < 1000 THEN dma
                        ELSE NULL
                    END AS dma,
                    city_id,
                    placement_type,
                    video_playback_method,
                    CASE WHEN TRIM(age)='18-20' THEN 1
                        WHEN TRIM(age)='21-29' THEN 2
                        WHEN TRIM(age)='30-39' THEN 3
                        WHEN TRIM(age)='40-49' THEN 4
                        WHEN TRIM(age)='50-64' THEN 5
                        WHEN TRIM(age)='65+'   THEN 6
                        ELSE 0
                    END AS age,
                    CASE WHEN TRIM(LOWER(gender))='male'   THEN 1
                        WHEN TRIM(LOWER(gender))='female' THEN 2
                        ELSE 0
                    END AS gender,
                    CASE
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='18-20' THEN 1
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='18-20' THEN 2
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='18-20' THEN 3
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='21-29' THEN 4
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='21-29' THEN 5
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='21-29' THEN 6
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='30-39' THEN 7
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='30-39' THEN 8
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='30-39' THEN 9
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='40-49' THEN 10
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='40-49' THEN 11
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='40-49' THEN 12
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='50-64' THEN 13
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='50-64' THEN 14
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='50-64' THEN 15
                        WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='65+'   THEN 16
                        WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='65+'   THEN 17
                        WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='65+'   THEN 18
                    ELSE 0
                    END AS age_gender,

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
                WHERE ((hour is null
                        and date>=%(date_from)s
                        AND date<=%(date_to)s)
                    OR (hour is not null
                        and date>%(tzdate_from)s
                        AND date<%(tzdate_to)s)
                    OR (hour IS NOT NULL
                        AND ((date=%(tzdate_from)s
                            AND hour >= %(tzhour_from)s)
                            OR (date=%(tzdate_to)s
                                AND hour < %(tzhour_to)s))))
                    AND ad_group_id=ANY(%(ad_group_id)s)
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15);"""), {
                    'tzhour_from': 4,
                    'tzhour_to': 4,
                    'tzdate_from': '2016-07-01',
                    'tzdate_to': '2016-07-04',
                    'date_from': '2016-07-01',
                    'date_to': '2016-07-03',
                    'ad_group_id': test_helper.ListMatcher([1, 3, 4]),
                }
            )
        ])


class MasterViewTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = materialize_views.MasterView('asd', date_from, date_to, account_id=None)

        mv.generate()

        insert_into_master_sql = backtosql.SQLMatcher("""
            INSERT INTO mv_master
                (SELECT
                    d.date as date,
                    d.source_id as source_id,
                    c.agency_id as agency_id,
                    c.account_id as account_id,
                    c.campaign_id as campaign_id,
                    d.ad_group_id as ad_group_id,
                    d.content_ad_id as content_ad_id,
                    d.publisher as publisher,
                    d.device_type as device_type,
                    d.country as country,
                    d.state as state,
                    d.dma as dma,
                    d.age as age,
                    d.gender as gender,
                    d.age_gender as age_gender,
                    d.impressions as impressions,
                    d.clicks as clicks,
                    d.spend::bigint * 1000 as cost_nano,
                    d.data_spend::bigint * 1000 as data_cost_nano,
                    null as visits,
                    null as new_visits,
                    null as bounced_visits,
                    null as pageviews,
                    null as total_time_on_site,
                    round(d.spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_cost_nano,
                    round(d.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_data_cost_nano,
                    round( (
                        (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                        (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                    ) * cf.pct_license_fee::decimal(10, 8) * 1000
                    ) as license_fee_nano,
                    round(
                        (
                            (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                            (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                            (
                                (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                                (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                            ) * cf.pct_license_fee::decimal(10, 8)
                        ) * cf.pct_margin::decimal(10, 8) * 1000
                    ) as margin_nano,
                    null as users,
                    null as returning_users,

                    d.city_id as city_id,

                    d.placement_type as placement_type,
                    d.video_playback_method as video_playback_method,
                    d.video_start as video_start,
                    d.video_first_quartile as video_first_quartile,
                    d.video_midpoint as video_midpoint,
                    d.video_third_quartile as video_third_quartile,
                    d.video_complete as video_complete,
                    d.video_progress_3s as video_progress_3s
                FROM
                    (
                      (mvh_clean_stats a left outer join mvh_source b on a.source_slug=b.bidder_slug)
                      natural full outer join (
                        SELECT
                          date, source_id, ad_group_id, content_ad_id,
                          CASE WHEN source_id = 3 THEN NULL ELSE publisher END AS publisher
                        FROM mv_touchpointconversions
                        WHERE date=%(date)s
                        GROUP BY 1, 2, 3, 4, 5
                      ) tpc
                    ) d
                    join mvh_adgroup_structure c on d.ad_group_id=c.ad_group_id
                    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and d.date=cf.date
                WHERE d.date=%(date)s);
            """)

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 1)}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 1)}),
            mock.call(backtosql.SQLMatcher("""
                SELECT
                    ad_group_id AS ad_group_id,
                    type AS postclick_source,
                    content_ad_id AS content_ad_id,
                    source AS source_slug,
                    publisher AS publisher,
                    SUM(bounced_visits) bounced_visits,
                    json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
                    SUM(new_visits) new_visits,
                    SUM(pageviews) pageviews,
                    SUM(total_time_on_site) total_time_on_site,
                    SUM(users) users,
                    SUM(visits) visits
                FROM postclickstats
                WHERE date=%(date)s
                GROUP BY ad_group_id, postclick_source, content_ad_id, source_slug, publisher;
            """), {'date': datetime.date(2016, 7, 1)}
            ),
            mock.call(backtosql.SQLMatcher("""
                COPY mv_master
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                CREDENTIALS %(credentials)s
                MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': ('s3://test_bucket/materialized_views/'
                           'mv_master/2016/07/01/mv_master_asd.csv'),
                'delimiter': '\t'
            }),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 1)}),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 2)}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/02/mv_master_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2)}),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 3)}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/03/mv_master_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3)}),
        ])

    def test_generate_rows(self):

        date = datetime.date(2016, 5, 1)

        mock_cursor = mock.MagicMock()

        postclickstats_return_value = [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None), None),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None), None),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'trol', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None), None),
        ]

        with mock.patch.object(materialize_views.MasterView, 'get_postclickstats',
                               return_value=postclickstats_return_value):
            mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
            rows = list(mv.generate_rows(mock_cursor, date))

            self.assertItemsEqual(rows, [
                (
                    date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                    constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                    0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None
                ),
                (
                    date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                    constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                    0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None
                ),
                (
                    date, 3, 1, 2, 2, 2, 4, 'trol', 0, None, None, None,
                    constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                    0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None
                )
            ])

    @mock.patch('etl.materialize_views.MasterView.get_postclickstats_query_results')
    def test_get_postclickstats(self, mock_get_postclickstats_query_results):
        date = datetime.date(2016, 5, 1)

        mock_get_postclickstats_query_results.return_value = [
            PostclickstatsResults(1, 'gaapi', 1, 'outbrain', 'Bla.com', 12, '{einpix: 2}', 22, 100, 20, 2, 24),
            # this one should be left out as its from lower priority postclick source
            PostclickstatsResults(1, 'ga_mail', 2, 'outbrain', 'beer.com', 12, '{einpix: 2}', 22, 100, 20, 2, 24),
            PostclickstatsResults(3, 'gaapi', 3, 'adblade', 'Nesto.com', 12, '{einpix: 2}', 22, 100, 20, 2, 24),
            PostclickstatsResults(2, 'omniture', 4, 'outbrain', 'Trol', 12, '{einpix: 2}', 22, 100, 20, 2, 24),
        ]

        mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
        mv.prefetch()

        self.maxDiff = None
        self.assertItemsEqual(list(mv.get_postclickstats(None, date)), [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'Bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, 0, 24, 2,
                      None, None, None, None, None, None, None, None, None), ('{einpix: 2}', 'gaapi')),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'Trol', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, 0, 24, 2,
                      None, None, None, None, None, None, None, None, None), ('{einpix: 2}', 'omniture')),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, 0, 24, 2,
                      None, None, None, None, None, None, None, None, None), ('{einpix: 2}', 'gaapi')),
        ])

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
        sql, params = mv.prepare_postclickstats_query(date)

        self.assertSQLEquals(sql, """
        SELECT
            ad_group_id AS ad_group_id,
            type AS postclick_source,
            content_ad_id AS content_ad_id,
            source AS source_slug,
            publisher AS publisher,
            SUM(bounced_visits) bounced_visits,
            json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
            SUM(new_visits) new_visits,
            SUM(pageviews) pageviews,
            SUM(total_time_on_site) total_time_on_site,
            SUM(users) users,
            SUM(visits) visits
        FROM postclickstats
        WHERE date=%(date)s
        GROUP BY
            ad_group_id,
            postclick_source,
            content_ad_id,
            source_slug,
            publisher;""")

        self.assertDictEqual(params, {'date': date})


class MasterViewTestByAccountId(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        account_id = 1
        mv = materialize_views.MasterView('asd', date_from, date_to, account_id=account_id)

        mv.generate()

        insert_into_master_sql = backtosql.SQLMatcher("""
            INSERT INTO mv_master
                (SELECT
                    d.date as date,
                    d.source_id as source_id,
                    c.agency_id as agency_id,
                    c.account_id as account_id,
                    c.campaign_id as campaign_id,
                    d.ad_group_id as ad_group_id,
                    d.content_ad_id as content_ad_id,
                    d.publisher as publisher,
                    d.device_type as device_type,
                    d.country as country,
                    d.state as state,
                    d.dma as dma,
                    d.age as age,
                    d.gender as gender,
                    d.age_gender as age_gender,
                    d.impressions as impressions,
                    d.clicks as clicks,
                    d.spend::bigint * 1000 as cost_nano,
                    d.data_spend::bigint * 1000 as data_cost_nano,
                    null as visits,
                    null as new_visits,
                    null as bounced_visits,
                    null as pageviews,
                    null as total_time_on_site,
                    round(d.spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_cost_nano,
                    round(d.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_data_cost_nano,
                    round( (
                        (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                        (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                    ) * cf.pct_license_fee::decimal(10, 8) * 1000
                    ) as license_fee_nano,
                    round(
                        (
                            (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                            (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                            (
                                (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                                (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                            ) * cf.pct_license_fee::decimal(10, 8)
                        ) * cf.pct_margin::decimal(10, 8) * 1000
                    ) as margin_nano,
                    null as users,
                    null as returning_users,

                    d.city_id as city_id,

                    d.placement_type as placement_type,
                    d.video_playback_method as video_playback_method,
                    d.video_start as video_start,
                    d.video_first_quartile as video_first_quartile,
                    d.video_midpoint as video_midpoint,
                    d.video_third_quartile as video_third_quartile,
                    d.video_complete as video_complete,
                    d.video_progress_3s as video_progress_3s
                FROM
                (
                  (mvh_clean_stats a left outer join mvh_source b on a.source_slug=b.bidder_slug)
                  natural full outer join (
                    SELECT
                      date, source_id, ad_group_id, content_ad_id,
                      CASE WHEN source_id = 3 THEN NULL ELSE publisher END AS publisher
                    FROM mv_touchpointconversions
                    WHERE date=%(date)s
                      AND account_id=%(account_id)s
                    GROUP BY 1, 2, 3, 4, 5
                  ) tpc
                ) d
                join mvh_adgroup_structure c on d.ad_group_id=c.ad_group_id
                join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and d.date=cf.date
                WHERE d.date=%(date)s AND c.account_id=%(account_id)s);
            """)

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s AND account_id=%(account_id)s'),
                {'date': datetime.date(2016, 7, 1), 'account_id': account_id}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 1), 'account_id': account_id}),
            mock.call(backtosql.SQLMatcher("""
                SELECT
                    ad_group_id AS ad_group_id,
                    type AS postclick_source,
                    content_ad_id AS content_ad_id,
                    source AS source_slug,
                    publisher AS publisher,
                    SUM(bounced_visits) bounced_visits,
                    json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
                    SUM(new_visits) new_visits,
                    SUM(pageviews) pageviews,
                    SUM(total_time_on_site) total_time_on_site,
                    SUM(users) users,
                    SUM(visits) visits
                FROM postclickstats
                WHERE date=%(date)s AND ad_group_id=ANY(%(ad_group_id)s)
                GROUP BY ad_group_id, postclick_source, content_ad_id, source_slug, publisher;
            """), {'date': datetime.date(2016, 7, 1), 'ad_group_id': test_helper.ListMatcher([1, 3, 4])}
            ),
            mock.call(backtosql.SQLMatcher("""
                COPY mv_master
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                CREDENTIALS %(credentials)s
                MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/01/mv_master_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 1), 'account_id': account_id}),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s AND account_id=%(account_id)s'),
                {'date': datetime.date(2016, 7, 2), 'account_id': account_id}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 2), 'account_id': account_id}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2), 'ad_group_id': test_helper.ListMatcher([1, 3, 4])}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/02/mv_master_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2), 'account_id': account_id}),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s AND account_id=%(account_id)s'),
                {'date': datetime.date(2016, 7, 3), 'account_id': account_id}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 3), 'account_id': account_id}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3), 'ad_group_id': test_helper.ListMatcher([1, 3, 4])}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/03/mv_master_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3), 'account_id': account_id}),
        ])

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)
        sql, params = mv.prepare_postclickstats_query(date)

        self.assertSQLEquals(sql, """
        SELECT
            ad_group_id AS ad_group_id,
            type AS postclick_source,
            content_ad_id AS content_ad_id,
            source AS source_slug,
            publisher AS publisher,
            SUM(bounced_visits) bounced_visits,
            json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
            SUM(new_visits) new_visits,
            SUM(pageviews) pageviews,
            SUM(total_time_on_site) total_time_on_site,
            SUM(users) users,
            SUM(visits) visits
        FROM postclickstats
        WHERE date=%(date)s AND ad_group_id=ANY(%(ad_group_id)s)
        GROUP BY
            ad_group_id,
            postclick_source,
            content_ad_id,
            source_slug,
            publisher;""")

        self.assertDictEqual(params, {'date': date, 'ad_group_id': test_helper.ListMatcher([1, 3, 4])})


class MVConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = materialize_views.MVConversions('asd', date_from, date_to, account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 1)}
            ),
            mock.call(backtosql.SQLMatcher("""
                SELECT
                    ad_group_id AS ad_group_id,
                    type AS postclick_source,
                    content_ad_id AS content_ad_id,
                    source AS source_slug,
                    publisher AS publisher,
                    SUM(bounced_visits) bounced_visits,
                    json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
                    SUM(new_visits) new_visits,
                    SUM(pageviews) pageviews,
                    SUM(total_time_on_site) total_time_on_site,
                    SUM(users) users,
                    SUM(visits) visits
                FROM postclickstats
                WHERE date=%(date)s
                GROUP BY ad_group_id, postclick_source, content_ad_id, source_slug, publisher;
            """), {'date': datetime.date(2016, 7, 1)}
            ),
            mock.call(backtosql.SQLMatcher("""
                COPY mv_conversions
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                CREDENTIALS %(credentials)s
                MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/01/mv_conversions_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 2)}
            ),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/02/mv_conversions_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 3)}
            ),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/03/mv_conversions_asd.csv',
                'delimiter': '\t'
            }),
        ])

    def test_generate_rows(self):
        date = datetime.date(2016, 7, 1)

        mock_cursor = mock.MagicMock()

        postclickstats_return_value = [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), ('{"einpix": 2, "preuba": 1}', 'gaapi')),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  ('{"poop": 111}', 'omniture')),
            ((1, 3), (date, 2, 1, 1, 3, 3, 3, 'nesto2.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  ('{}', None)),
            ((1, 3), (date, 3, 1, 1, 3, 3, 3, 'nesto3.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  ('', None)),
            ((1, 3), (date, 4, 1, 1, 3, 3, 3, 'nesto4.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  (None, 'gaapi')),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'trol', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), ('{"poop": 23}', 'ga_mail')),
        ]

        with mock.patch.object(materialize_views.MasterView, 'get_postclickstats',
                               return_value=postclickstats_return_value):

            mv = materialize_views.MVConversions('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
            rows = list(mv.generate_rows(mock_cursor, date))

            self.assertItemsEqual(rows, [
                (date, 3, 1, 1, 1, 1, 1, 'bla.com', 'ga__einpix', 2),
                (date, 3, 1, 1, 1, 1, 1, 'bla.com', 'ga__preuba', 1),
                (date, 1, 1, 1, 3, 3, 3, 'nesto.com', 'omniture__poop', 111),
                (date, 3, 1, 2, 2, 2, 4, 'trol', 'ga__poop', 23),
            ])


class MVConversionsTestAccountId(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = materialize_views.MVConversions('asd', date_from, date_to, account_id=1)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s AND account_id=%(account_id)s'),
                {'date': datetime.date(2016, 7, 1), 'account_id': 1}
            ),
            mock.call(backtosql.SQLMatcher("""
                SELECT
                    ad_group_id AS ad_group_id,
                    type AS postclick_source,
                    content_ad_id AS content_ad_id,
                    source AS source_slug,
                    publisher AS publisher,
                    SUM(bounced_visits) bounced_visits,
                    json_dict_sum(LISTAGG(conversions, ';'), ';') AS conversions,
                    SUM(new_visits) new_visits,
                    SUM(pageviews) pageviews,
                    SUM(total_time_on_site) total_time_on_site,
                    SUM(users) users,
                    SUM(visits) visits
                FROM postclickstats
                WHERE date=%(date)s AND ad_group_id=ANY(%(ad_group_id)s)
                GROUP BY ad_group_id, postclick_source, content_ad_id, source_slug, publisher;
            """), {'date': datetime.date(2016, 7, 1), 'ad_group_id': test_helper.ListMatcher([1, 3, 4])}
            ),
            mock.call(backtosql.SQLMatcher("""
                COPY mv_conversions
                FROM %(s3_url)s
                FORMAT CSV
                DELIMITER AS %(delimiter)s
                CREDENTIALS %(credentials)s
                MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/01/mv_conversions_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s AND account_id=%(account_id)s'),
                {'date': datetime.date(2016, 7, 2), 'account_id': 1}
            ),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2), 'ad_group_id': test_helper.ListMatcher([1, 3, 4])}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/02/mv_conversions_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s AND account_id=%(account_id)s'),
                {'date': datetime.date(2016, 7, 3), 'account_id': 1}
            ),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3), 'ad_group_id': test_helper.ListMatcher([1, 3, 4])}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/03/mv_conversions_asd.csv',
                'delimiter': '\t'
            }),
        ])


class MVTouchpointConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    def test_generate(self, mock_transaction, mock_cursor):
        mv = materialize_views.MVTouchpointConversions('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher(
                    "DELETE FROM mv_touchpointconversions WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"),
                {
                    'date_from': datetime.date(2016, 7, 1),
                    'date_to': datetime.date(2016, 7, 3),
                }
            ),
            mock.call(backtosql.SQLMatcher("""
            INSERT INTO mv_touchpointconversions (
                SELECT
                    a.date as date,
                    a.source_id as source_id,
                    s.agency_id as agency_id,
                    s.account_id as account_id,
                    s.campaign_id as campaign_id,
                    a.ad_group_id as ad_group_id,
                    a.content_ad_id as content_ad_id,
                    CASE WHEN a.source_id = 3 THEN a.publisher
                         WHEN a.source_id = 4 THEN 'all publishers'
                         ELSE LOWER(a.publisher)
                    END as publisher,
                    a.slug as slug,
                    CASE
                        WHEN a.conversion_lag <= 24 THEN 24
                        WHEN a.conversion_lag <= 168 THEN 168
                        WHEN a.conversion_lag <= 720 THEN 720
                    ELSE 2160
                    END AS conversion_window,
                    COUNT(a.touchpoint_id) as touchpoint_count,
                    SUM(CASE WHEN a.conversion_id_ranked = 1 THEN 1 ELSE 0 END) AS conversion_count,

                    SUM(a.conversion_value_nano) as conversion_value_nano,
                    a.conversion_label as conversion_label
                FROM (
                    SELECT
                        c.date as date,
                        c.source_id as source_id,

                        c.ad_group_id as ad_group_id,
                        c.content_ad_id as content_ad_id,
                        c.publisher as publisher,

                        c.slug as slug,

                        c.conversion_lag as conversion_lag,

                        c.touchpoint_id as touchpoint_id,
                        RANK() OVER
                            (PARTITION BY c.conversion_id, c.ad_group_id ORDER BY c.touchpoint_timestamp DESC) AS conversion_id_ranked,

                        c.value_nano as conversion_value_nano,
                        c.label as conversion_label
                    FROM conversions c
                    WHERE c.conversion_lag <= 2160 AND c.date BETWEEN %(date_from)s AND %(date_to)s
                ) a join mvh_adgroup_structure s on a.ad_group_id=s.ad_group_id
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, conversion_label);"""), {
                'date_from': datetime.date(2016, 7, 1),
                'date_to': datetime.date(2016, 7, 3),
            })
        ])

    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    def test_generate_account_id(self, mock_transaction, mock_cursor):
        mv = materialize_views.MVTouchpointConversions(
            'asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher(
                    "DELETE FROM mv_touchpointconversions WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;"),
                {
                    'date_from': datetime.date(2016, 7, 1),
                    'date_to': datetime.date(2016, 7, 3),
                    'account_id': 1,
                }
            ),
            mock.call(backtosql.SQLMatcher("""
            INSERT INTO mv_touchpointconversions (
                SELECT
                    a.date as date,
                    a.source_id as source_id,
                    s.agency_id as agency_id,
                    s.account_id as account_id,
                    s.campaign_id as campaign_id,
                    a.ad_group_id as ad_group_id,
                    a.content_ad_id as content_ad_id,
                    CASE WHEN a.source_id = 3 THEN a.publisher
                         WHEN a.source_id = 4 THEN 'all publishers'
                         ELSE LOWER(a.publisher)
                    END as publisher,
                    a.slug as slug,
                    CASE
                    WHEN a.conversion_lag <= 24 THEN 24
                    WHEN a.conversion_lag <= 168 THEN 168
                    WHEN a.conversion_lag <= 720 THEN 720
                    ELSE 2160
                    END AS conversion_window,
                    COUNT(a.touchpoint_id) as touchpoint_count,
                    SUM(CASE WHEN a.conversion_id_ranked = 1 THEN 1 ELSE 0 END) AS conversion_count,

                    SUM(a.conversion_value_nano) as conversion_value_nano,
                    a.conversion_label as conversion_label
                FROM (
                    SELECT
                        c.date as date,
                        c.source_id as source_id,

                        c.ad_group_id as ad_group_id,
                        c.content_ad_id as content_ad_id,
                        c.publisher as publisher,

                        c.slug as slug,

                        c.conversion_lag as conversion_lag,

                        c.touchpoint_id as touchpoint_id,
                        RANK() OVER
                            (PARTITION BY c.conversion_id, c.ad_group_id ORDER BY c.touchpoint_timestamp DESC) AS conversion_id_ranked,

                        c.value_nano as conversion_value_nano,
                        c.label as conversion_label
                    FROM conversions c
                    WHERE c.conversion_lag <= 2160 AND c.date BETWEEN %(date_from)s AND %(date_to)s AND c.account_id=%(account_id)s
                ) a join mvh_adgroup_structure s on a.ad_group_id=s.ad_group_id
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, conversion_label);"""), {
                'date_from': datetime.date(2016, 7, 1),
                'date_to': datetime.date(2016, 7, 3),
                'account_id': 1,
            }
            )
        ])


@mock.patch('redshiftapi.db.get_write_stats_transaction')
class DerivedMaterializedViewTest(TestCase, backtosql.TestSQLMixin):

    DERIVED_VIEWS = [
        (materialize_views.MVContentAdDeliveryGeo, 'mv_content_ad_delivery_geo'),
        (materialize_views.MVContentAdDeliveryDemo, 'mv_content_ad_delivery_demo'),
        (materialize_views.MVAdGroupDeliveryGeo, 'mv_ad_group_delivery_geo'),
        (materialize_views.MVAdGroupDeliveryDemo, 'mv_ad_group_delivery_demo'),
        (materialize_views.MVCampaignDeliveryGeo, 'mv_campaign_delivery_geo'),
        (materialize_views.MVCampaignDeliveryDemo, 'mv_campaign_delivery_demo'),
        (materialize_views.MVAccountDeliveryGeo, 'mv_account_delivery_geo'),
        (materialize_views.MVAccountDeliveryDemo, 'mv_account_delivery_demo'),
        (materialize_views.MVContentAd, 'mv_content_ad'),
        (materialize_views.MVAdGroup, 'mv_ad_group'),
        (materialize_views.MVCampaign, 'mv_campaign'),
        (materialize_views.MVAccount, 'mv_account'),
        (materialize_views.MVTouchpointAccount, 'mv_touch_account'),
        (materialize_views.MVTouchpointCampaign, 'mv_touch_campaign'),
        (materialize_views.MVTouchpointAdGroup, 'mv_touch_ad_group'),
        (materialize_views.MVTouchpointContentAd, 'mv_touch_content_ad'),
        (materialize_views.MVConversionsAccount, 'mv_conversions_account'),
        (materialize_views.MVConversionsCampaign, 'mv_conversions_campaign'),
        (materialize_views.MVConversionsAdGroup, 'mv_conversions_ad_group'),
        (materialize_views.MVConversionsContentAd, 'mv_conversions_content_ad'),
    ]

    def test_generate(self, mock_transaction):
        for mv_class, table_name in self.DERIVED_VIEWS:
            mv = mv_class('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

            with mock.patch('redshiftapi.db.get_write_stats_cursor') as mock_cursor:

                mv.generate()

                mock_cursor().__enter__().execute.assert_has_calls([
                    mock.call(
                        backtosql.SQLMatcher(
                            "DELETE FROM {} WHERE (date BETWEEN %(date_from)s AND %(date_to)s);".format(table_name)),
                        {
                            'date_from': datetime.date(2016, 7, 1),
                            'date_to': datetime.date(2016, 7, 3),
                        }
                    ),
                    mock.call(mock.ANY, {
                        'date_from': datetime.date(2016, 7, 1),
                        'date_to': datetime.date(2016, 7, 3),
                    })
                ])

    def test_generate_account_id(self, mock_transaction):
        for mv_class, table_name in self.DERIVED_VIEWS:
            mv = mv_class('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

            with mock.patch('redshiftapi.db.get_write_stats_cursor') as mock_cursor:

                mv.generate()

                mock_cursor().__enter__().execute.assert_has_calls([
                    mock.call(
                        backtosql.SQLMatcher(
                            "DELETE FROM {} WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;".format(
                                table_name)),
                        {
                            'date_from': datetime.date(2016, 7, 1),
                            'date_to': datetime.date(2016, 7, 3),
                            'account_id': 1,
                        }
                    ),
                    mock.call(mock.ANY, {
                        'date_from': datetime.date(2016, 7, 1),
                        'date_to': datetime.date(2016, 7, 3),
                        'account_id': 1,
                    })
                ])
