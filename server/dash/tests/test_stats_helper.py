import datetime
import decimal
from mock import patch

from django import test
from django.contrib.auth.models import Permission

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
                'cost': decimal.Decimal('10.00'),
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
                                         conversion_goals=None, constraints=None):
        # used as a side effect in mocks
        touchpoint_conversion_stats = [
            {
                'touchpoint_count': 10,
                'conversion_count': 5,
            }
        ]
        defaults = {'slug': [cg.pixel.slug for cg in conversion_goals]}
        if self.use_separate_rows_for_tp_conversions:
            for b in set(breakdown) - set(['slug']):
                defaults[b] = [9999 for cg in conversion_goals]

        _update_with_defaults(touchpoint_conversion_stats, breakdown,
                              defaults=defaults)
        return touchpoint_conversion_stats

    def setUp(self):
        self.use_separate_rows_for_tp_conversions = False

        self.superuser = User.objects.get(id=1)
        self.user = User.objects.get(id=2)

        # add permissions for postclick stats
        self.user.user_permissions.add(Permission.objects.get(codename='content_ads_postclick_acquisition'))
        self.user.user_permissions.add(Permission.objects.get(codename='content_ads_postclick_engagement'))

        self.assertTrue(self.superuser.has_perm('zemauth.can_see_redshift_postclick_statistics'))
        self.assertTrue(self.superuser.has_perm('zemauth.conversion_reports'))

        self.assertFalse(self.user.has_perm('zemauth.can_see_redshift_postclick_statistics'))
        self.assertFalse(self.user.has_perm('zemauth.conversion_reports'))

    def test_no_permissions(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_as_query.side_effect = self._get_content_ad_stats
        stats = stats_helper.get_stats_with_conversions(self.user, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[])

        self.assertTrue(mock_as_query.called)
        self.assertFalse(mock_ca_query.called)
        self.assertFalse(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0
        }], stats)

    def test_no_permissions_with_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_as_query.side_effect = self._get_content_ad_stats
        conversion_goals = models.ConversionGoal.objects.all()
        stats = stats_helper.get_stats_with_conversions(self.user, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals)

        self.assertTrue(mock_as_query.called)
        self.assertFalse(mock_ca_query.called)
        self.assertFalse(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0
        }], stats)

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
            'cost': decimal.Decimal('10.00'),
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

    def test_touchpoint_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats
        mock_tp_query.side_effect = self._get_touchpoint_conversion_stats

        conversion_goals = models.ConversionGoal.objects.filter(pk=1)
        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals)

        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0,
            'conversion_goal_1': 5,
        }], stats)

    def test_both_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats
        mock_tp_query.side_effect = self._get_touchpoint_conversion_stats

        conversion_goals = models.ConversionGoal.objects.filter(pk__in=[1, 2])
        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals)

        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0,
            'conversion_goal_1': 5,
            'conversion_goal_2': 1,
        }], stats)

    def test_both_conversion_goals_different_ad_group(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats
        mock_tp_query.side_effect = self._get_touchpoint_conversion_stats

        self.use_separate_rows_for_tp_conversions = True
        conversion_goals = models.ConversionGoal.objects.filter(pk__in=[1, 2])
        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 10, 1),
                                                        datetime.date(2015, 10, 31), breakdown=['ad_group'], order=[],
                                                        conversion_goals=conversion_goals)

        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)
        self.assertEqual([{
            'ad_group': 1,
            'impressions': 10,
            'clicks': 1,
            'cost': decimal.Decimal('10.00'),
            'cpc': decimal.Decimal('10.00'),
            'ctr': 0.1,
            'visits': 1,
            'click_discrepancy': 0,
            'pageviews': 5,
            'percent_new_users': 100,
            'bounce_rate': 0,
            'pv_per_visit': 5,
            'avg_tos': 0,
            'conversion_goal_1': 0,
            'conversion_goal_2': 1,
        }, {
            'ad_group': 9999,
            'conversion_goal_1': 5
        }], stats)
