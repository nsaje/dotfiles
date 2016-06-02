import collections
import backtosql
import datetime
import json
import mock

from django.test import TestCase

from dash import models
from dash import constants

from etl import materialize_views
from etl import helpers


StatsResults = collections.namedtuple('Result1',
                                      ['source_slug', 'ad_group_id', 'content_ad_id', 'publisher',
                                       'device_type', 'country', 'state', 'dma', 'age', 'gender',
                                       'clicks', 'impressions', 'cost_micro', 'data_cost_micro'])


PostclickstatsResults = collections.namedtuple('Result2',
                                               ['ad_group_id', 'postclick_source', 'content_ad_id', 'source_slug',
                                                'publisher', 'bounced_visits', 'conversions', 'new_visits', 'pageviews',
                                                'total_time_on_site', 'visits'])


TPConversionResults = collections.namedtuple('Result3',
                                             ['ad_group_id', 'content_ad_id', 'source_id', 'publisher',
                                              'slug', 'conversion_window', 'count'])


class MasterViewTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @mock.patch('etl.materialize_views.MasterView._get_stats')
    @mock.patch('etl.materialize_views.MasterView._get_postclickstats')
    @mock.patch('etl.materialize_views.MasterView._get_touchpoint_conversions')
    def test_generate_rows(self, mock_get_touchpoint_conversions, mock_get_postclickstats, mock_get_stats):

        date = datetime.date(2016, 5, 1)

        mock_get_stats.return_value = [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.DESKTOP, 'US', 'CA', 866,
                      constants.AgeGroup.AGE_50_64, constants.Gender.MEN, constants.AgeGenderGroup.AGE_50_64_MEN,
                      22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2850000, 3040000, 1178000, None, None)),
            ((2, 2), (date, 2, 1, 2, 2, 2, 2, 'Trol', constants.DeviceType.TABLET, 'US', 'FL', 866,
                      constants.AgeGroup.AGE_21_29, constants.Gender.WOMEN, constants.AgeGenderGroup.AGE_21_29_WOMEN,
                      22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2700000, 2880000, 1004400, None, None)),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'beer', constants.DeviceType.UNDEFINED, 'US', 'MA', 866,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2550000, 2720000, 790500, None, None)),
        ]

        mock_get_postclickstats.return_value = [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None)),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None)),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'trol', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None)),
        ]

        mock_get_touchpoint_conversions.return_value = [
            ((3, 1),
             (
                 date, 3, 1, 1, 1, 1, 1, 'bla.com',
                 constants.DeviceType.UNDEFINED, None, None, None,
                 constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                     'blapix_168': 2,
                     'blapix_720': 2,
                     'einpix_24': 2,
                     'einpix_168': 10,
                     'einpix_720': 12,
                 }),
             )),
            ((2, 2),
             (
                 date, 2, 1, 1, 1, 1, 2, 'na.com',
                 constants.DeviceType.UNDEFINED, None, None, None,
                 constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                    'einpix_24': 2,
                    'einpix_168': 2,
                    'einpix_720': 2,
                 }),
             )),
            ((2, 1),
             (
                 date, 2, 1, 1, 1, 1, 1, 'a.com',
                 constants.DeviceType.UNDEFINED, None, None, None,
                 constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                    'einpix_168': 2,
                    'einpix_720': 2,
                 }),
             )),
        ]

        self.maxDiff = None

        view = materialize_views.MasterView()
        self.assertItemsEqual(list(view.generate_rows(date, {})), [
            (
                date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.DESKTOP, 'US', 'CA', 866,
                constants.AgeGroup.AGE_50_64, constants.Gender.MEN, constants.AgeGenderGroup.AGE_50_64_MEN,
                22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2850000, 3040000, 1178000, None, None
            ),
            (
                date, 2, 1, 2, 2, 2, 2, 'Trol', constants.DeviceType.TABLET, 'US', 'FL', 866,
                constants.AgeGroup.AGE_21_29, constants.Gender.WOMEN, constants.AgeGenderGroup.AGE_21_29_WOMEN,
                22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2700000, 2880000, 1004400, None, None
            ),
            (
                date, 1, 1, 1, 3, 3, 3, 'beer', constants.DeviceType.UNDEFINED, 'US', 'MA', 866,
                constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2550000, 2720000, 790500, None, None
            ),
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
                date, 3, 1, 1, 1, 1, 1, 'bla.com',
                constants.DeviceType.UNDEFINED, None, None, None,
                constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                    'blapix_168': 2,
                    'blapix_720': 2,
                    'einpix_24': 2,
                    'einpix_168': 10,
                    'einpix_720': 12,
                }),
            ),
            (
                date, 2, 1, 1, 1, 1, 2, 'na.com',
                constants.DeviceType.UNDEFINED, None, None, None,
                constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                    'einpix_24': 2,
                    'einpix_168': 2,
                    'einpix_720': 2,
                }),
            ),
        ])

    @mock.patch('etl.materialize_views.MasterView._get_stats_query_results')
    def test_get_stats(self, mock_get_stats_query_results):

        date = datetime.date(2016, 5, 1)

        campaign_factors = {
            models.Campaign.objects.get(pk=1): (0.95, 0.2),
            models.Campaign.objects.get(pk=2): (0.90, 0.18),
            models.Campaign.objects.get(pk=3): (0.85, 0.15),
        }

        mock_get_stats_query_results.return_value = [
            StatsResults('outbrain', 1, 1, 'bla.com', 2, 'US', 'CA', 866, '50-64', 'male', 12, 22, 3000, 3200),
            StatsResults('adiant', 2, 2, 'Trol', 5, 'US', 'FL', 866, '21-29', 'female', 12, 22, 3000, 3200),
            StatsResults('adblade', 3, 3, 'beer', 4, 'US', 'MA', 866, 'gibberish', 'gibberish', 12, 22, 3000, 3200),
        ]

        view = materialize_views.MasterView()
        view._prefetch()

        self.assertItemsEqual(list(view._get_stats(date, campaign_factors)), [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.DESKTOP, 'US', 'CA', 866,
                      constants.AgeGroup.AGE_50_64, constants.Gender.MEN, constants.AgeGenderGroup.AGE_50_64_MEN,
                      22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2850000, 3040000, 1178000, None, None)),
            ((2, 2), (date, 2, 1, 2, 2, 2, 2, 'Trol', constants.DeviceType.TABLET, 'US', 'FL', 866,
                      constants.AgeGroup.AGE_21_29, constants.Gender.WOMEN, constants.AgeGenderGroup.AGE_21_29_WOMEN,
                      22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2700000, 2880000, 1004400, None, None)),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'beer', constants.DeviceType.UNDEFINED, 'US', 'MA', 866,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      22, 12, 3000, 3200, 0, 0, 0, 0, 0, 2550000, 2720000, 790500, None, None)),
        ])

    @mock.patch('etl.materialize_views.MasterView._get_postclickstats_query_results')
    def test_get_postclickstats(self, mock_get_postclickstats_query_results):
        date = datetime.date(2016, 5, 1)

        mock_get_postclickstats_query_results.return_value = [
            PostclickstatsResults(1, 'gaapi', 1, 'b1_outbrain', 'bla.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            # this one should be left out as its from lower priority postclick source
            PostclickstatsResults(1, 'ga_mail', 2, 'b1_outbrain', 'beer.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            PostclickstatsResults(3, 'gaapi', 3, 'adblade', 'nesto.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            PostclickstatsResults(2, 'gaapi', 4, 'outbrain', 'trol', 12, '{einpix: 2}', 22, 100, 20, 2),
        ]

        view = materialize_views.MasterView()
        view._prefetch()

        self.assertItemsEqual(list(view._get_postclickstats(date)), [
            ((3, 1), (date, 3, 1, 1, 1, 1, 1, 'bla.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None)),
            ((3, 4), (date, 3, 1, 2, 2, 2, 4, 'trol', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None)),
            ((1, 3), (date, 1, 1, 1, 3, 3, 3, 'nesto.com', constants.DeviceType.UNDEFINED, None, None, None,
                      constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                      0, 0, 0, 0, 2, 22, 12, 100, 20, 0, 0, 0, '{einpix: 2}', None)),
        ])

    @mock.patch('etl.materialize_views.MasterView._get_touchpoint_conversions_query_results')
    def test_get_touchpoint_conversions(self, mock_get_touchpoint_conversions_query_results):
        date = datetime.date(2016, 5, 1)

        mock_get_touchpoint_conversions_query_results.return_value = [
            TPConversionResults(1, 1, 1, 'bla.com', 'einpix', 1, 2),
            TPConversionResults(1, 1, 1, 'bla.com', 'einpix', 50, 1),
            TPConversionResults(1, 1, 1, 'bla.com', 'einpix', 150, 7),
            TPConversionResults(1, 1, 1, 'bla.com', 'blapix', 52, 2),
            TPConversionResults(1, 1, 1, 'bla.com', 'einpix', 260, 2),
            TPConversionResults(1, 1, 2, 'na.com', 'einpix', 1, 2),
            TPConversionResults(1, 1, 2, 'a.com', 'einpix', 66, 2),
            TPConversionResults(1, 2, 1, 'aa.com', 'einpix', 999, 2),  # out of the max window, don't count
        ]

        view = materialize_views.MasterView()
        view._prefetch()

        self.maxDiff = None
        self.assertItemsEqual(list(view._get_touchpoint_conversions(date)), [
            ((1, 1),
             (
                 date, 1, 1, 1, 1, 1, 1, 'bla.com',
                 constants.DeviceType.UNDEFINED, None, None, None,
                 constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                     'blapix_168': 2,
                     'blapix_720': 2,
                     'einpix_24': 2,
                     'einpix_168': 10,
                     'einpix_720': 12,
                 }),
             )),
            ((2, 1),
             (
                 date, 2, 1, 1, 1, 1, 1, 'na.com',
                 constants.DeviceType.UNDEFINED, None, None, None,
                 constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                    'einpix_24': 2,
                    'einpix_168': 2,
                    'einpix_720': 2,
                 }),
             )),
            ((2, 1),
             (
                 date, 2, 1, 1, 1, 1, 1, 'a.com',
                 constants.DeviceType.UNDEFINED, None, None, None,
                 constants.AgeGroup.UNDEFINED, constants.Gender.UNDEFINED, constants.AgeGenderGroup.UNDEFINED,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, json.dumps({
                    'einpix_168': 2,
                    'einpix_720': 2,
                 }),
             )),
        ])

    def test_prepare_stats_query(self):

        date = datetime.date(2016, 5, 1)
        sql, params = materialize_views.MasterView._prepare_stats_query(date)

        self.assertSQLEquals(sql, """
        SELECT
            media_source AS source_slug,
            ad_group_id AS ad_group_id,
            content_ad_id AS content_ad_id,
            publisher AS publisher,
            device_type AS device_type,
            country AS country,
            state AS state,
            dma AS dma,
            age AS age,
            gender AS gender,
            SUM(clicks) clicks,
            SUM(spend) cost_micro,
            SUM(data_spend) data_cost_micro,
            SUM(impressions) impressions
        FROM stats
        WHERE
            (date=%(date)s AND hour IS NULL)
            OR (hour IS NOT NULL AND ((date=%(tzdate_from)s
                    AND hour >= %(tzhour_from)s)
                OR (date=%(tzdate_to)s
                    AND hour < %(tzhour_to)s)))
        GROUP BY
            source_slug,
            ad_group_id,
            content_ad_id,
            publisher,
            device_type,
            country,
            state,
            dma,
            age,
            gender;""")

        self.assertDictEqual(params, helpers.get_local_date_context(date))

    def test_prepare_postclickstats_query(self):
        date = datetime.date(2016, 5, 1)
        sql, params = materialize_views.MasterView._prepare_postclickstats_query(date)

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

    def test_prepare_touchpoint_conversions_query(self):
        date = datetime.date(2016, 5, 1)
        sql, params = materialize_views.MasterView._prepare_touchpoint_conversions_query(date)

        self.assertSQLEquals(sql, """
        SELECT
            ad_group_id AS ad_group_id,
            content_ad_id AS content_ad_id,
            source_id AS source_id,
            publisher AS publisher,
            slug AS slug,
            CASE
                WHEN conversion_lag <= 24 THEN 24
                WHEN conversion_lag > 24
                        AND conversion_lag <= 168 THEN 168
                ELSE 720
            END AS conversion_window,
            COUNT(*) AS count
        FROM conversions
        WHERE date=%(date)s
        GROUP BY ad_group_id,
                content_ad_id,
                source_id,
                publisher,
                slug,
                conversion_window;""")

        self.assertDictEqual(params, {'date': date})
