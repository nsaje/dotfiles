import datetime
import decimal
from mock import patch

from django import test
from django.contrib.auth.models import Permission

from dash import constants
from dash import models
from dash import stats_helper
from zemauth.models import User


def _update_with_defaults(ret, keys, defaults={}):
    # a value in defaults should be a list that included the value for each new row separately
    # by default, the default value for inserted keys is 1
    if not keys:
        return ret
    defaults_counter = {k: 0 for k in defaults.keys()}
    for d in ret:
        for k in keys:
            val = 1
            if k in defaults:
                val = defaults[k][defaults_counter[k]]
                defaults_counter[k] += 1
            d[k] = val
    return ret


@patch('dash.stats_helper.reports.api_touchpointconversions.query')
@patch('dash.stats_helper.reports.api_contentads.query')
@patch('dash.stats_helper.reports.api.query')
class GetStatsWithConversionsTestCase(test.TestCase):

    fixtures = ['test_views.yaml']

    def _get_content_ad_stats(self, start_date, end_date, breakdown=None,
                              order=None, ignore_diff_rows=False, **constraints):
        # used as a side effect in mocks
        content_ad_stats = [
            {
                'impressions': 10,
                'clicks': 1,
                'media_cost': decimal.Decimal('10.00'),
                'e_media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 1,
                'click_discrepancy': 0,
                'pageviews': 5,
                'percent_new_users': 100,
                'bounce_rate': 0,
                'pv_per_visit': 5,
                'avg_tos': 0,
                'conversions': {
                    'ga__2': 1,
                }
            },
        ]

        _update_with_defaults(content_ad_stats, breakdown)
        return content_ad_stats

    def _get_touchpoint_conversion_stats(self, start_date, end_date, order=None, breakdown=None,
                                         pixels=None, constraints=None):
        # used as a side effect in mocks
        touchpoint_conversion_stats = [
            {
                'conversion_count_24': 5,
                'conversion_count_168': 5,
                'conversion_count_720': 5,
                'conversion_count_2160': 5,
            }
        ]
        defaults = {
            'slug': [pixel.slug for pixel in pixels],
            'account': [pixel.account_id for pixel in pixels],
            'conversion_window': [cw for cw in constants.ConversionWindows.get_all()],
        }
        if self.use_separate_rows_for_tp_conversions:
            for b in set(breakdown) - set(['slug', 'campaign']):
                defaults[b] = [9999 for pixel in pixels]
        bd = breakdown + ['slug', 'account', 'conversion_window']
        _update_with_defaults(touchpoint_conversion_stats, bd + ['campaign'] if 'campaign' not in bd else bd,
                              defaults=defaults)
        return touchpoint_conversion_stats

    def setUp(self):
        self.use_separate_rows_for_tp_conversions = False

        self.superuser = User.objects.get(id=1)
        self.user = User.objects.get(id=2)

        # add permissions for postclick stats
        self.user.user_permissions.add(Permission.objects.get(codename='content_ads_postclick_acquisition'))

        self.assertTrue(self.superuser.has_perm('zemauth.can_see_redshift_postclick_statistics'))
        self.assertTrue(self.superuser.has_perm('zemauth.can_view_platform_cost_breakdown'))
        self.assertFalse(self.user.has_perm('zemauth.can_see_redshift_postclick_statistics'))

    def test_report_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats

        conversion_goals = models.ConversionGoal.objects.filter(pk=2)
        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals)

        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertFalse(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'media_cost': decimal.Decimal('10.00'),
            'e_media_cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0,
            'conversion_goal_1': 1
        }], stats)

    def test_touchpoint_conversions_pixels(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats
        mock_tp_query.side_effect = self._get_touchpoint_conversion_stats

        conversion_goals = models.ConversionGoal.objects.filter(pk=1)
        pixels = models.ConversionPixel.objects.filter(pk=1)
        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals, pixels=pixels)

        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'media_cost': decimal.Decimal('10.00'),
            'e_media_cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0,
            'pixel_1_168': 5,
            'pixel_1_24': 5,
            'pixel_1_720': 5,
            'pixel_1_2160': 5,
            'avg_cost_per_pixel_1_168': 2,
            'avg_cost_per_pixel_1_24': 2,
            'avg_cost_per_pixel_1_720': 2,
            'avg_cost_per_pixel_1_2160': 2,
        }], stats)

    def test_preserve_ordering_without_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.return_value = [
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 1),
                'impressions': 10,
                'clicks': 1,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 1,
                'click_discrepancy': 0,
                'pageviews': 5,
                'percent_new_users': 100,
                'bounce_rate': 0,
                'pv_per_visit': 5,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 10, 1),
                'impressions': 20,
                'clicks': 2,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 2,
                'click_discrepancy': 0,
                'pageviews': 10,
                'percent_new_users': 200,
                'bounce_rate': 0,
                'pv_per_visit': 10,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 10),
                'impressions': 30,
                'clicks': 3,
                'media_cost': decimal.Decimal('30.00'),
                'cpc': decimal.Decimal('30.00'),
                'ctr': 0.1,
                'visits': 3,
                'click_discrepancy': 0,
                'pageviews': 15,
                'percent_new_users': 300,
                'bounce_rate': 0,
                'pv_per_visit': 15,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 11, 15),
                'impressions': 10,
                'clicks': 1,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 1,
                'click_discrepancy': 0,
                'pageviews': 5,
                'percent_new_users': 100,
                'bounce_rate': 0,
                'pv_per_visit': 5,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 9, 1),
                'impressions': 40,
                'clicks': 1,
                'media_cost': decimal.Decimal('40.00'),
                'cpc': decimal.Decimal('40.00'),
                'ctr': 0.1,
                'visits': 4,
                'click_discrepancy': 0,
                'pageviews': 20,
                'percent_new_users': 400,
                'bounce_rate': 0,
                'pv_per_visit': 20,
                'avg_tos': 0,
            },
        ]

        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 11, 30), datetime.date(2015, 12, 1),
                                                        breakdown=['date', 'ad_group'], order=['date'])
        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertFalse(mock_tp_query.called)

        self.assertEqual([
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 1),
                'impressions': 10,
                'clicks': 1,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 1,
                'click_discrepancy': 0,
                'pageviews': 5,
                'percent_new_users': 100,
                'bounce_rate': 0,
                'pv_per_visit': 5,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 10, 1),
                'impressions': 20,
                'clicks': 2,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 2,
                'click_discrepancy': 0,
                'pageviews': 10,
                'percent_new_users': 200,
                'bounce_rate': 0,
                'pv_per_visit': 10,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 10),
                'impressions': 30,
                'clicks': 3,
                'media_cost': decimal.Decimal('30.00'),
                'cpc': decimal.Decimal('30.00'),
                'ctr': 0.1,
                'visits': 3,
                'click_discrepancy': 0,
                'pageviews': 15,
                'percent_new_users': 300,
                'bounce_rate': 0,
                'pv_per_visit': 15,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 11, 15),
                'impressions': 10,
                'clicks': 1,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 1,
                'click_discrepancy': 0,
                'pageviews': 5,
                'percent_new_users': 100,
                'bounce_rate': 0,
                'pv_per_visit': 5,
                'avg_tos': 0,
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 9, 1),
                'impressions': 40,
                'clicks': 1,
                'media_cost': decimal.Decimal('40.00'),
                'cpc': decimal.Decimal('40.00'),
                'ctr': 0.1,
                'visits': 4,
                'click_discrepancy': 0,
                'pageviews': 20,
                'percent_new_users': 400,
                'bounce_rate': 0,
                'pv_per_visit': 20,
                'avg_tos': 0,
            },
        ], stats)

    def test_ordering_with_pixels(self, mock_as_query, mock_ca_query, mock_tp_query):
        conversion_goals = models.ConversionGoal.objects.filter(pk=1)
        pixels = models.ConversionPixel.objects.filter(pk=1)
        mock_ca_query.return_value = [
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 1),
                'impressions': 10,
                'clicks': 1,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 1,
                'click_discrepancy': 0,
                'pageviews': 5,
                'percent_new_users': 100,
                'bounce_rate': 0,
                'pv_per_visit': 5,
                'avg_tos': 0,
            },
        ]
        mock_tp_query.return_value = [{
            'ad_group': 2,
            'date': datetime.date(2015, 11, 30),
            'conversion_count_24': 5,
            'conversion_count_168': 5,
            'conversion_count_720': 5,
            'conversion_count_2160': 5,
            'account': conversion_goals[0].pixel.account_id,
            'campaign': conversion_goals[0].campaign.id,
            'slug': conversion_goals[0].pixel.slug,
            'conversion_window': conversion_goals[0].conversion_window
        }]

        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 11, 30), datetime.date(2015, 12, 1),
                                                        breakdown=['date', 'ad_group'], order=['date'],
                                                        conversion_goals=conversion_goals, pixels=pixels)
        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)

        self.assertEqual([
            {
                'ad_group': 2,
                'pixel_1_24': 5,
                'pixel_1_168': 5,
                'pixel_1_720': 5,
                'pixel_1_2160': 5,
                'avg_cost_per_pixel_1_24': None,
                'avg_cost_per_pixel_1_168': None,
                'avg_cost_per_pixel_1_720': None,
                'avg_cost_per_pixel_1_2160': None,
                'date': datetime.date(2015, 11, 30)
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 1),
                'impressions': 10,
                'clicks': 1,
                'media_cost': decimal.Decimal('10.00'),
                'cpc': decimal.Decimal('10.00'),
                'ctr': 0.1,
                'visits': 1,
                'click_discrepancy': 0,
                'pageviews': 5,
                'percent_new_users': 100,
                'bounce_rate': 0,
                'pv_per_visit': 5,
                'avg_tos': 0,
                'pixel_1_24': 0,
                'pixel_1_168': 0,
                'pixel_1_720': 0,
                'pixel_1_2160': 0,
                'avg_cost_per_pixel_1_24': None,
                'avg_cost_per_pixel_1_168': None,
                'avg_cost_per_pixel_1_720': None,
                'avg_cost_per_pixel_1_2160': None,
            },
        ], stats)

    def test_both_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats
        mock_tp_query.side_effect = self._get_touchpoint_conversion_stats

        conversion_goals = models.ConversionGoal.objects.filter(pk__in=[1, 2])
        pixels = models.ConversionPixel.objects.filter(pk=1)
        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals, pixels=pixels)

        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'media_cost': decimal.Decimal('10.00'),
            'e_media_cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0,
            'pixel_1_168': 5,
            'pixel_1_2160': 5,
            'pixel_1_24': 5,
            'pixel_1_720': 5,
            'avg_cost_per_pixel_1_168': 2,
            'avg_cost_per_pixel_1_2160': 2,
            'avg_cost_per_pixel_1_24': 2,
            'avg_cost_per_pixel_1_720': 2,
            'conversion_goal_2': 1,
        }], stats)

    def test_both_conversion_goals_different_ad_group(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats
        mock_tp_query.side_effect = self._get_touchpoint_conversion_stats

        self.use_separate_rows_for_tp_conversions = True
        conversion_goals = models.ConversionGoal.objects.filter(pk__in=[1, 2])
        pixels = models.ConversionPixel.objects.filter(pk=1)
        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals, pixels=pixels)

        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'media_cost': decimal.Decimal('10.00'),
            'e_media_cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0,
            'pixel_1_24': 0,
            'pixel_1_168': 0,
            'pixel_1_720': 0,
            'pixel_1_2160': 0,
            'conversion_goal_2': 1,
            'avg_cost_per_pixel_1_24': None,
            'avg_cost_per_pixel_1_168': None,
            'avg_cost_per_pixel_1_720': None,
            'avg_cost_per_pixel_1_2160': None,
        }, {
            'ad_group': 9999,
            'pixel_1_24': 5,
            'pixel_1_168': 5,
            'pixel_1_720': 5,
            'pixel_1_2160': 5,
            'avg_cost_per_pixel_1_24': None,
            'avg_cost_per_pixel_1_168': None,
            'avg_cost_per_pixel_1_720': None,
            'avg_cost_per_pixel_1_2160': None,
            'conversion_goal_2': None,
        }], stats)
