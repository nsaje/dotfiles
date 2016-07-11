import collections
import backtosql
import datetime
import json
import mock
import textwrap

from django.test import TestCase, override_settings

from dash import models
from dash import constants

from etl import materialize_views
from etl import helpers


PostclickstatsResults = collections.namedtuple('Result2',
                                               ['ad_group_id', 'postclick_source', 'content_ad_id', 'source_slug',
                                                'publisher', 'bounced_visits', 'conversions', 'new_visits', 'pageviews',
                                                'total_time_on_site', 'visits'])


@mock.patch('redshiftapi.db.get_write_stats_cursor')
@mock.patch('redshiftapi.db.get_write_stats_transaction')
@mock.patch('utils.s3helpers.S3Helper')
class MVHSourceTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersSource('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_source/2016/07/03/view_asd.csv",
            textwrap.dedent("""\
            1\tadblade\tadblade\r
            2\tadiant\tadiant\r
            3\toutbrain\toutbrain\r
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
                's3_url': 's3://test_bucket/materialized_views/mvh_source/2016/07/03/view_asd.csv',
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
        mv = materialize_views.MVHelpersCampaignFactors('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))

        mv.generate(campaign_factors={
            datetime.date(2016, 7, 1): {
                models.Campaign.objects.get(pk=1): (1.0, 0.2),
                models.Campaign.objects.get(pk=2): (0.2, 0.2),
            },
            datetime.date(2016, 7, 2): {
                models.Campaign.objects.get(pk=1): (1.0, 0.3),
                models.Campaign.objects.get(pk=2): (0.2, 0.3),
            },
        })

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_campaign_factors/2016/07/03/view_asd.csv",
            textwrap.dedent("""\
            2016-07-01\t1\t1.0\t0.2\r
            2016-07-01\t2\t0.2\t0.2\r
            2016-07-02\t1\t1.0\t0.3\r
            2016-07-02\t2\t0.2\t0.3\r
            """))

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_campaign_factors (
                date date not null encode delta,
                campaign_id int2 not null encode lzo,

                pct_actual_spend decimal(22, 18) encode lzo,
                pct_license_fee decimal(22, 18) encode lzo
            ) sortkey(date, campaign_id)""")),
            mock.call(backtosql.SQLMatcher("""
            COPY mvh_campaign_factors
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            CREDENTIALS %(credentials)s
            MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mvh_campaign_factors/2016/07/03/view_asd.csv',
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
        mv = materialize_views.MVHelpersAdGroupStructure('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_adgroup_structure/2016/07/03/view_asd.csv",
            textwrap.dedent("""\
            1\t1\t1\t1\r
            1\t2\t2\t2\r
            1\t1\t3\t3\r
            1\t1\t1\t4\r
            """))

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_adgroup_structure (
                agency_id int2 encode lzo,
                account_id int2 encode lzo,
                campaign_id int2 encode lzo,
                ad_group_id int2 encode lzo
            ) sortkey(ad_group_id, campaign_id, account_id, agency_id)""")),
            mock.call(backtosql.SQLMatcher("""
            COPY mvh_adgroup_structure
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            CREDENTIALS %(credentials)s
            MAXERROR 0 BLANKSASNULL EMPTYASNULL;"""), {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mvh_adgroup_structure/2016/07/03/view_asd.csv',
                'delimiter': '\t',
            })
        ])


@mock.patch('redshiftapi.db.get_write_stats_cursor')
@mock.patch('redshiftapi.db.get_write_stats_transaction')
class MVHNormalizedStatsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ['test_materialize_views']

    def test_generate(self, mock_transaction, mock_cursor):
        mv = materialize_views.MVHelpersNormalizedStats('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(backtosql.SQLMatcher("""
            CREATE TEMP TABLE mvh_clean_stats (
                date date not null encode delta,
                source_slug varchar(127) encode lzo,

                ad_group_id int2 encode lzo,
                content_ad_id integer encode lzo,
                publisher varchar(255) encode lzo,

                device_type int2 encode bytedict,
                country varchar(2) encode bytedict,
                state varchar(5) encode bytedict,
                dma int2 encode bytedict,
                age int2 encode bytedict,
                gender int2 encode bytedict,
                age_gender int2 encode bytedict,

                impressions integer encode lzo,
                clicks integer encode lzo,
                spend bigint encode lzo,
                data_spend bigint encode lzo
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
                    publisher,
                    extract_device_type(device_type) as device_type,
                    extract_country(country) as country,
                    extract_state(state) as state,
                    extract_dma(dma) as dma,
                    extract_age(age) as age,
                    extract_gender(gender) as gender,
                    extract_age_gender(stats.age, stats.gender) as age_gender,
                    SUM(impressions) as impressions,
                    SUM(clicks) as clicks,
                    SUM(spend) as spend,
                    SUM(data_spend) as data_spend
                FROM stats
                WHERE (hour is null
                        and date>=%(date_from)s
                        AND date<=%(date_to)s)
                    OR (hour is not null
                        and date>%(tzdate_from)s
                        AND date<%(tzdate_to)s)
                    OR (hour IS NOT NULL
                        AND ((date=%(tzdate_from)s
                            AND hour >= %(tzhour_from)s)
                            OR (date=%(tzdate_to)s
                                AND hour < %(tzhour_to)s)))
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12);"""), {
                    'tzhour_from': 4,
                    'tzhour_to': 4,
                    'tzdate_from': '2016-07-01',
                    'tzdate_to': '2016-07-04',
                    'date_from': '2016-07-01',
                    'date_to': '2016-07-03'
                })
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

        mv = materialize_views.MasterView('asd', date_from, date_to)

        mv.generate()

        insert_into_master_sql = backtosql.SQLMatcher("""
            INSERT INTO mv_master
                (SELECT
                    a.date as date,
                    b.source_id as source_id,
                    c.agency_id as agency_id,
                    c.account_id as account_id,
                    c.campaign_id as campaign_id,
                    a.ad_group_id as ad_group_id,
                    a.content_ad_id as content_ad_id,
                    a.publisher as publisher,
                    a.device_type as device_type,
                    a.country as country,
                    a.state as state,
                    a.dma as dma,
                    a.age as age,
                    a.gender as gender,
                    a.age_gender as age_gender,
                    a.impressions as impressions,
                    a.clicks as clicks,
                    a.spend::bigint * 1000 as cost_nano,
                    a.data_spend::bigint * 1000 as data_cost_nano,
                    null as visits,
                    null as new_visits,
                    null as bounced_visits,
                    null as pageviews,
                    null as total_time_on_site,
                    round(a.spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_cost_nano,
                    round(a.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_data_cost_nano,
                    round( (
                        (nvl(a.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                        (nvl(a.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                    ) * pct_license_fee::decimal(10, 8) * 1000 ) as license_fee_nano
                FROM ( (mvh_clean_stats a left outer join mvh_source b on a.source_slug=b.bidder_slug)
                    join mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id )
                        join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and a.date=cf.date
                WHERE a.date=%(date)s);
            """)

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 1)}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 1)}),
            mock.call(backtosql.SQLMatcher("""
                SELECT date, source_id, content_ad_id
                FROM mv_master
                WHERE date=%(date)s GROUP BY 1, 2, 3;
            """), {'date': datetime.date(2016, 7, 1)}
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
                    's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/01/view_asd.csv',
                    'delimiter': '\t'
                }
            ),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 2)}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/02/view_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_master WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 3)}
            ),
            mock.call(insert_into_master_sql, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_master/2016/07/03/view_asd.csv',
                'delimiter': '\t'
            }),
        ])

    def test_generate_rows(self):

        date = datetime.date(2016, 5, 1)
        breakdown_keys_with_traffic = set([(3, 1), (2, 2), (1, 3)])

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
            mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))
            rows = list(mv.generate_rows(mock_cursor, date, breakdown_keys_with_traffic))

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
            ])

    @mock.patch('etl.materialize_views.MasterView.get_postclickstats_query_results')
    def test_get_postclickstats(self, mock_get_postclickstats_query_results):
        date = datetime.date(2016, 5, 1)

        mock_get_postclickstats_query_results.return_value = [
            PostclickstatsResults(1, 'gaapi', 1, 'outbrain', 'bla.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            # this one should be left out as its from lower priority postclick source
            PostclickstatsResults(1, 'ga_mail', 2, 'outbrain', 'beer.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            PostclickstatsResults(3, 'gaapi', 3, 'adblade', 'nesto.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            PostclickstatsResults(2, 'gaapi', 4, 'outbrain', 'trol', 12, '{einpix: 2}', 22, 100, 20, 2),
        ]

        mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))
        mv.prefetch()

        self.assertItemsEqual(list(mv.get_postclickstats(None, date)), [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), '{einpix: 2}'),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'trol', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), '{einpix: 2}'),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), '{einpix: 2}'),
        ])

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))
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


class MVConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket', AWS_ACCESS_KEY_ID='bar', AWS_SECRET_ACCESS_KEY='foo')
    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = materialize_views.MVConversions('asd', date_from, date_to)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 1)}
            ),
            mock.call(backtosql.SQLMatcher("""
                SELECT date, source_id, content_ad_id
                FROM mv_master
                WHERE date=%(date)s GROUP BY 1, 2, 3;
            """), {'date': datetime.date(2016, 7, 1)}
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
                    's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/01/view_asd.csv',
                    'delimiter': '\t'
                }
            ),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 2)}
            ),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 2)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/02/view_asd.csv',
                'delimiter': '\t'
            }),
            mock.call(
                backtosql.SQLMatcher('DELETE FROM mv_conversions WHERE date=%(date)s'),
                {'date': datetime.date(2016, 7, 3)}
            ),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {'date': datetime.date(2016, 7, 3)}),
            mock.call(mock.ANY, {
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                's3_url': 's3://test_bucket/materialized_views/mv_conversions/2016/07/03/view_asd.csv',
                'delimiter': '\t'
            }),
        ])

    def test_generate_rows(self):
        date = datetime.date(2016, 7, 1)

        breakdown_keys_with_traffic = set([(3, 1), (2, 2), (1, 3)])

        mock_cursor = mock.MagicMock()

        postclickstats_return_value = [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), '{"einpix": 2, "preuba": 1}'),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  '{"poop": 111}'),
            ((1, 3), (date, 2, 1, 1, 3, 3, 3, 'nesto2.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  '{}'),
            ((1, 3), (date, 3, 1, 1, 3, 3, 3, 'nesto3.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  ''),
            ((1, 3), (date, 4, 1, 1, 3, 3, 3, 'nesto4.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  None),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'trol', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), '{"poop": 23}'),
        ]

        with mock.patch.object(materialize_views.MasterView, 'get_postclickstats',
                               return_value=postclickstats_return_value):

            mv = materialize_views.MVConversions('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))
            rows = list(mv.generate_rows(mock_cursor, date, breakdown_keys_with_traffic))

            self.assertItemsEqual(rows, [
                (date, 3, 1, 1, 1, 1, 1, 'bla.com', 'einpix', 2),
                (date, 3, 1, 1, 1, 1, 1, 'bla.com', 'preuba', 1),
                (date, 1, 1, 1, 3, 3, 3, 'nesto.com', 'poop', 111),
            ])


class MVTouchpointConversionsTest(TestCase, backtosql.TestSQLMixin):

    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    def test_generate(self, mock_transaction, mock_cursor):
        mv = materialize_views.MVTouchpointConversions('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher(
                    "DELETE FROM mv_touchpointconversions WHERE date BETWEEN %(date_from)s AND %(date_to)s;"),
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
                    a.publisher as publisher,
                    a.slug as slug,
                    CASE
                    WHEN a.conversion_lag <= 24 THEN 24
                    WHEN a.conversion_lag <= 168 THEN 168
                    WHEN a.conversion_lag <= 720 THEN 720
                    ELSE 2160
                    END AS conversion_window,
                    count(1) as touchpoint_count
                FROM conversions a join mvh_adgroup_structure s on a.ad_group_id=s.ad_group_id
                WHERE a.conversion_lag <= 2160 AND a.date BETWEEN %(date_from)s AND %(date_to)s
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10);"""), {
                'date_from': datetime.date(2016, 7, 1),
                'date_to': datetime.date(2016, 7, 3),
            })
        ])


@mock.patch('redshiftapi.db.get_write_stats_transaction')
class DerivedMaterializedViewTest(TestCase, backtosql.TestSQLMixin):

    DERIVED_VIEWS = [
        (materialize_views.MVContentAdDelivery, 'mv_content_ad_delivery'),
        (materialize_views.MVAdGroupDelivery, 'mv_ad_group_delivery'),
        (materialize_views.MVCampaignDelivery, 'mv_campaign_delivery'),
        (materialize_views.MVAccountDelivery, 'mv_account_delivery'),
        (materialize_views.MVContentAd, 'mv_content_ad'),
        (materialize_views.MVAdGroup, 'mv_ad_group'),
        (materialize_views.MVCampaign, 'mv_campaign'),
        (materialize_views.MVAccount, 'mv_account'),
    ]

    def test_generate(self, mock_transaction):
        for mv_class, table_name in self.DERIVED_VIEWS:
            mv = mv_class('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3))

            with mock.patch('redshiftapi.db.get_write_stats_cursor') as mock_cursor:

                mv.generate()

                mock_cursor().__enter__().execute.assert_has_calls([
                    mock.call(
                        backtosql.SQLMatcher(
                            "DELETE FROM {} WHERE date BETWEEN %(date_from)s AND %(date_to)s;".format(table_name)),
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
