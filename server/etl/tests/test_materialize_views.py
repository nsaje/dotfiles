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


PostclickstatsResults = collections.namedtuple('Result2',
                                               ['ad_group_id', 'postclick_source', 'content_ad_id', 'source_slug',
                                                'publisher', 'bounced_visits', 'conversions', 'new_visits', 'pageviews',
                                                'total_time_on_site', 'visits'])


TPConversionResults = collections.namedtuple('Result3',
                                             ['ad_group_id', 'content_ad_id', 'source_id', 'publisher',
                                              'slug', 'conversion_window', 'count'])


class MasterViewTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ['test_materialize_views']

    @mock.patch('etl.materialize_views.MasterView._get_postclickstats')
    @mock.patch('etl.materialize_views.MasterView._get_touchpoint_conversions')
    def test_generate_rows(self, mock_get_touchpoint_conversions, mock_get_postclickstats):

        date = datetime.date(2016, 5, 1)
        breakdown_keys_with_traffic = set([(3, 1), (2, 2), (1, 3)])

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
        mock_cursor = mock.MagicMock()

        view = materialize_views.MasterView()
        self.assertItemsEqual(list(view.generate_rows(
            None, None, cursor=mock_cursor, date=date, breakdown_keys_with_traffic=breakdown_keys_with_traffic)), [
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

    @mock.patch('etl.materialize_views.MasterView._get_postclickstats_query_results')
    def test_get_postclickstats(self, mock_get_postclickstats_query_results):
        date = datetime.date(2016, 5, 1)

        mock_get_postclickstats_query_results.return_value = [
            PostclickstatsResults(1, 'gaapi', 1, 'outbrain', 'bla.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            # this one should be left out as its from lower priority postclick source
            PostclickstatsResults(1, 'ga_mail', 2, 'outbrain', 'beer.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            PostclickstatsResults(3, 'gaapi', 3, 'adblade', 'nesto.com', 12, '{einpix: 2}', 22, 100, 20, 2),
            PostclickstatsResults(2, 'gaapi', 4, 'outbrain', 'trol', 12, '{einpix: 2}', 22, 100, 20, 2),
        ]

        view = materialize_views.MasterView()
        view._prefetch()

        self.assertItemsEqual(list(view._get_postclickstats(None, date)), [
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
        self.assertItemsEqual(list(view._get_touchpoint_conversions(None, date)), [
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
