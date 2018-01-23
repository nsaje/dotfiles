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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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
                campaign_id integer not null encode lzo,

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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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
                campaign_id integer not null encode lzo,

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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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
            mock.call(mock.ANY),
            mock.call(mock.ANY, {
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
            mock.call(mock.ANY),
            mock.call(mock.ANY, {
                'tzhour_from': 4,
                'tzhour_to': 4,
                'tzdate_from': '2016-07-01',
                'tzdate_to': '2016-07-04',
                'date_from': '2016-07-01',
                'date_to': '2016-07-03',
                'ad_group_id': test_helper.ListMatcher([1, 3, 4]),
            })
        ])


class MasterViewTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @override_settings(S3_BUCKET_STATS='test_bucket')
    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        mv = materialize_views.MasterView('asd', date_from, date_to, account_id=None)

        mv.generate()

        insert_into_master_sql = mock.ANY

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
            ((3, 1), (date, 3, 1, 1, 1, 1, 'bla.com', 'bla.com__3',
                      constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                      constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                      None, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None), None),
            ((1, 3), (date, 1, 1, 3, 3, 3, 'nesto.com', 'nesto.com__1',
                      constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                      constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                      None, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None), None),
            ((3, 4), (date, 3, 2, 2, 2, 4, 'trol', 'trol__3',
                      constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                      constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                      None, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None), None),
        ]

        with mock.patch.object(materialize_views.MasterView, 'get_postclickstats',
                               return_value=postclickstats_return_value):
            mv = materialize_views.MasterView('asd', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)
            rows = list(mv.generate_rows(mock_cursor, date))

            self.maxDiff = None
            self.assertItemsEqual(rows, [
                (
                    date, 3, 1, 1, 1, 1, 'bla.com', 'bla.com__3',
                    constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                    constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                    None, None, None, None,
                    constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                    0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None
                ),
                (
                    date, 1, 1, 3, 3, 3, 'nesto.com', 'nesto.com__1',
                    constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                    constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                    None, None, None, None,
                    constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                    0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None
                ),
                (
                    date, 3, 2, 2, 2, 4, 'trol', 'trol__3',
                    constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                    constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                    None, None, None, None,
                    constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
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
            ((3, 1), (date, 3, 1, 1, 1, 1, 'Bla.com', 'Bla.com__3',
                      constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                      constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                      None, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, 0, 24, 2,
                      None, None, None, None, None, None), ('{einpix: 2}', 'gaapi')),
            ((3, 4), (date, 3, 2, 2, 2, 4, 'Trol', 'Trol__3',
                      constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                      constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                      None, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, 0, 24, 2,
                      None, None, None, None, None, None), ('{einpix: 2}', 'omniture')),
            ((1, 3), (date, 1, 1, 3, 3, 3, 'nesto.com', 'nesto.com__1',
                      constants.DeviceType.UNKNOWN, None, None, constants.PlacementMedium.UNKNOWN,
                      constants.PlacementType.UNKNOWN, constants.VideoPlaybackMethod.UNKNOWN,
                      None, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, 0, 24, 2,
                      None, None, None, None, None, None), ('{einpix: 2}', 'gaapi')),
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

    @override_settings(S3_BUCKET_STATS='test_bucket')
    @mock.patch('redshiftapi.db.get_write_stats_cursor')
    @mock.patch('redshiftapi.db.get_write_stats_transaction')
    @mock.patch('utils.s3helpers.S3Helper')
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        account_id = 1
        mv = materialize_views.MasterView('asd', date_from, date_to, account_id=account_id)

        mv.generate()

        insert_into_master_sql = mock.ANY
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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNKNOWN, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0), ('{"einpix": 2, "preuba": 1}', 'gaapi')),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNKNOWN, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  ('{"poop": 111}', 'omniture')),
            ((1, 3), (date, 2, 1, 1, 3, 3, 3, 'nesto2.com', constants.DeviceType.UNKNOWN, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  ('{}', None)),
            ((1, 3), (date, 3, 1, 1, 3, 3, 3, 'nesto3.com', constants.DeviceType.UNKNOWN, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  ('', None)),
            ((1, 3), (date, 4, 1, 1, 3, 3, 3, 'nesto4.com', constants.DeviceType.UNKNOWN, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0),  (None, 'gaapi')),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'trol', constants.DeviceType.UNKNOWN, None, None, None,
                      constants.Age.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGender.UNDEFINED,
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

    @override_settings(S3_BUCKET_STATS='test_bucket')
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
            mock.call(mock.ANY, {
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
            mock.call(mock.ANY, {
                'date_from': datetime.date(2016, 7, 1),
                'date_to': datetime.date(2016, 7, 3),
                'account_id': 1,
            }
            )
        ])


@mock.patch('redshiftapi.db.get_write_stats_cursor')
@mock.patch('redshiftapi.db.get_write_stats_transaction')
class DerivedMaterializedViewTest(TestCase, backtosql.TestSQLMixin):

    def test_generate(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (5,)

        mv_cls = materialize_views.MasterDerivedView.create(
            table_name='newtable',
            breakdown=['date', 'source_id', 'account_id'],
            sortkey=['date', 'source_id', 'account_id'],
            distkey='source_id')

        mv = mv_cls('jobid', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(
                backtosql.SQLMatcher("""
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
                    video_progress_3s integer encode lzo
                )
                diststyle key distkey(source_id) sortkey(date, source_id, account_id)
                """)
            ),
            mock.call(backtosql.SQLMatcher("SELECT count(1) FROM newtable")),
            mock.call(
                backtosql.SQLMatcher("DELETE FROM newtable WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"),
                {'date_from': datetime.date(2016, 7, 1), 'date_to': datetime.date(2016, 7, 3)}
            ),
            mock.call(
                backtosql.SQLMatcher("""
                INSERT INTO newtable (SELECT
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
                    SUM(video_progress_3s) video_progress_3s
                FROM mv_master
                WHERE (date>=%s AND date<=%s)
                GROUP BY date, source_id, account_id
                ORDER BY date, source_id, account_id
                );
                """),
                [datetime.date(2016, 7, 1), datetime.date(2016, 7, 3)])
        ])

    def test_generate_account_id(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (1,)

        mv_cls = materialize_views.MasterDerivedView.create(
            table_name='newtable',
            breakdown=['date', 'source_id', 'account_id'],
            sortkey=['date', 'source_id', 'account_id'],
            distkey='source_id')

        mv = mv_cls('jobid', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(mock.ANY),
            mock.call(mock.ANY),
            mock.call(
                backtosql.SQLMatcher("DELETE FROM newtable WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;"),  # noqa
                {'date_from': datetime.date(2016, 7, 1), 'date_to': datetime.date(2016, 7, 3), 'account_id': 1}
            ),
            mock.call(
                backtosql.SQLMatcher("""
                INSERT INTO newtable (SELECT
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
                    SUM(video_progress_3s) video_progress_3s
                FROM mv_master
                WHERE (account_id=%s AND date>=%s AND date<=%s)
                GROUP BY date, source_id, account_id
                ORDER BY date, source_id, account_id
                );
                """),
                [1, datetime.date(2016, 7, 1), datetime.date(2016, 7, 3)])
        ])

    def test_generate_empty_table(self, mock_transaction, mock_cursor):
        mock_cursor().__enter__().fetchone.return_value = (0,)

        mv_cls = materialize_views.MasterDerivedView.create(
            table_name='newtable',
            breakdown=['date', 'source_id', 'account_id'],
            sortkey=['date', 'source_id', 'account_id'],
            distkey='source_id')
        mv = mv_cls('jobid', datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        mock_cursor().__enter__().execute.assert_has_calls([
            mock.call(mock.ANY),
            mock.call(mock.ANY),
            mock.call(mock.ANY, [])
        ])


class ReplicasTest(TestCase, backtosql.TestSQLMixin):

    @override_settings(S3_BUCKET_STATS='test_bucket')
    def test_prepare_unload_query(self):
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        sql, params = materialize_views.prepare_unload_csv_query(
            'mypath/', 'mv_master', from_date, to_date)

        self.assertSQLEquals(sql, """
        UNLOAD
        ('SELECT * FROM mv_master WHERE (date BETWEEN \\'2016-05-01\\' AND \\'2016-05-03\\') ')
        TO %(s3_url)s
        DELIMITER AS %(delimiter)s
        CREDENTIALS %(credentials)s
        ESCAPE
        NULL AS '$NA$'
        GZIP
        MANIFEST
        ;
        """)

        self.assertDictEqual(
            params,
            {
                's3_url': 's3://test_bucket/mypath/',
                'credentials': 'aws_access_key_id=bar;aws_secret_access_key=foo',
                'delimiter': materialize_views.CSV_DELIMITER
            }
        )

    @override_settings(S3_BUCKET_STATS='test_bucket')
    def test_prepare_unload_query_account(self):
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        sql, params = materialize_views.prepare_unload_csv_query(
            'mypath/', 'mv_master', from_date, to_date, account_id=16)

        self.assertSQLEquals(sql, """
        UNLOAD
        ('SELECT * FROM mv_master WHERE (date BETWEEN \\'2016-05-01\\' AND \\'2016-05-03\\') AND account_id = 16')
        TO %(s3_url)s
        DELIMITER AS %(delimiter)s
        CREDENTIALS %(credentials)s
        ESCAPE
        NULL AS '$NA$'
        GZIP
        MANIFEST
        ;
        """)

    @mock.patch('redshiftapi.db.get_write_stats_cursor', autospec=True)
    @mock.patch.object(materialize_views, 'prepare_unload_csv_query', autospec=True)
    def test_unload_table(self, mock_prepare_query, mock_cursor):
        mock_prepare_query.return_value = '', {}
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        materialize_views.unload_table('jobid', 'mytable', from_date, to_date, account_id=16)
        mock_prepare_query.assert_called_with(
            'materialized_views_replication/jobid/mytable/mytable-2016-05-01-2016-05-03-16', 'mytable', from_date, to_date, 16)

    @mock.patch('redshiftapi.db.get_write_stats_transaction', autospec=True)
    @mock.patch('redshiftapi.db.get_write_stats_cursor', autospec=True)
    @mock.patch.object(materialize_views, 'prepare_copy_csv_query', autospec=True)
    @mock.patch.object(materialize_views, 'prepare_date_range_delete_query', autospec=True)
    def test_update_table_from_s3(self, mock_prepare_delete, mock_prepare_copy, mock_cursor, mock_transaction):
        mock_prepare_copy.return_value = '', {}
        mock_prepare_delete.return_value = '', {}
        mock_cursor.return_value = mock.MagicMock()
        mock_transaction.return_value = mock.MagicMock()
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        materialize_views.update_table_from_s3('mydb', 's3://mypath/', 'mytable', from_date, to_date, account_id=16)
        mock_transaction.assert_called_with('mydb')
        mock_cursor.assert_called_with('mydb')
