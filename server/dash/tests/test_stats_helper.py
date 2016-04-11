import datetime
import decimal
from mock import patch

from django import test
from django.contrib.auth.models import Permission

from dash import models, conversions_helper, stats_helper, constants
from dash.models import AdGroup
from utils.test_helper import ListMatcher
from zemauth.models import User

import reports.api_publishers


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
        defaults = {
            'slug': [cg.pixel.slug for cg in conversion_goals],
            'account': [cg.pixel.account_id for cg in conversion_goals],
            'conversion_window': [cg.conversion_window for cg in conversion_goals],
            'campaign': [cg.campaign.id for cg in conversion_goals],
        }
        if self.use_separate_rows_for_tp_conversions:
            for b in set(breakdown) - set(['slug', 'campaign']):
                defaults[b] = [9999 for cg in conversion_goals]
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

    def test_preserve_ordering_without_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.return_value = [
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 1),
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
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 10, 1),
                'impressions': 20,
                'clicks': 2,
                'cost': decimal.Decimal('10.00'),
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
                'cost': decimal.Decimal('30.00'),
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
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 9, 1),
                'impressions': 40,
                'clicks': 1,
                'cost': decimal.Decimal('40.00'),
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
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 10, 1),
                'impressions': 20,
                'clicks': 2,
                'cost': decimal.Decimal('10.00'),
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
                'cost': decimal.Decimal('30.00'),
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
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 9, 1),
                'impressions': 40,
                'clicks': 1,
                'cost': decimal.Decimal('40.00'),
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

    def test_ordering_with_conversion_goals(self, mock_as_query, mock_ca_query, mock_tp_query):
        conversion_goals = models.ConversionGoal.objects.filter(pk=1)
        mock_ca_query.return_value = [
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 1),
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
            },
        ]
        mock_tp_query.return_value = [{
            'ad_group': 2,
            'date': datetime.date(2015, 11, 30),
            'touchpoint_count': 10,
            'conversion_count': 5,
            'account': conversion_goals[0].pixel.account_id,
            'campaign': conversion_goals[0].campaign.id,
            'slug': conversion_goals[0].pixel.slug,
            'conversion_window': conversion_goals[0].conversion_window
        }]

        stats = stats_helper.get_stats_with_conversions(self.superuser, datetime.date(2015, 11, 30), datetime.date(2015, 12, 1),
                                                        breakdown=['date', 'ad_group'], order=['date'],
                                                        conversion_goals=conversion_goals)
        self.assertFalse(mock_as_query.called)
        self.assertTrue(mock_ca_query.called)
        self.assertTrue(mock_tp_query.called)

        self.assertEqual([
            {
                'ad_group': 2,
                'conversion_goal_1': 5,
                'date': datetime.date(2015, 11, 30)
            },
            {
                'ad_group': 1,
                'date': datetime.date(2015, 12, 1),
                'impressions': 10,
                'clicks': 1,
                'conversion_goal_1': 0,
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
            },
        ], stats)

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

    def test_multiple_conversion_goals_with_same_pixel(self, mock_as_query, mock_ca_query, mock_tp_query):
        mock_ca_query.side_effect = self._get_content_ad_stats
        mock_tp_query.side_effect = [
            [{
                "account": 1,
                "campaign": 1,
                "ad_group": 9999,
                "conversion_count": 5,
                "slug": "test",
                "touchpoint_count": 10,
                "conversion_window": 168,
            }, {
                "account": 1,
                "campaign": 1,
                "ad_group": 9999,
                "conversion_count": 4,
                "slug": "test",
                "touchpoint_count": 9,
                "conversion_window": 1,
            }, {
                "account": 1,
                "campaign": 1,
                "ad_group": 9999,
                "conversion_count": 11,
                "slug": "test",
                "touchpoint_count": 8,
                "conversion_window": 7,
            }],
        ]

        self.use_separate_rows_for_tp_conversions = True

        # add another 2 conversion goals with the same pixel but different windows
        extra1 = models.ConversionGoal.objects.get(pk=1)
        extra1.pk = None
        extra1.name = 'extra conversion goal 1'
        extra1.conversion_window = 1
        extra1.goal_id = '100'
        extra1.save()

        extra2 = models.ConversionGoal.objects.get(pk=1)
        extra2.pk = None
        extra2.name = 'extra conversion goal 2'
        extra2.conversion_window = 7
        extra2.goal_id = '101'
        extra2.save()

        conversion_goals = models.ConversionGoal.objects.filter(pk__in=[1, 2, extra1.pk, extra2.pk])
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
            'conversion_goal_3': 0,
            'conversion_goal_4': 0,
        }, {
            'ad_group': 9999,
            'conversion_goal_1': 5,
            'conversion_goal_3': 4,
            'conversion_goal_4': 11,
        }], stats)


@patch('dash.table.reports.api_touchpointconversions.query')
@patch('dash.table.reports.api_publishers.query')
class GetPublishersDataAndConversionGoalsTestCase(test.TestCase):
    fixtures = ['test_views.yaml', 'test_api.yaml']

    def _mock_publisher_data(self, date):
        mock_stats = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'e_data_cost': 0,
            'external_id': '12345',
            'total_cost': 3,
            'billing_cost': 3,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'license_fee': 0.6,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'example.com',
            'exchange': 'adiant',
        }]
        return mock_stats

    def _mock_touchpoint_data(self, date):
        mock_stats = [{
            'date': date.isoformat(),
            'conversion_count': 64,
            'slug': 'test',
            'source': 7,
            'publisher': 'example.com',
            'conversion_window': 168,
            'account': 1,
        }]
        return mock_stats

    def _mock_publishers_and_touchpoint_data(self, date):
        mock_stats = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'e_data_cost': 0,
            'external_id': '12345',
            'total_cost': 3,
            'billing_cost': 3,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'license_fee': 0.6,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'example.com',
            'exchange': 'adiant',
            'conversion_goal_1': 64,
            'conversion_goal_2': None,
            'conversion_goal_3': None,
            'conversion_goal_4': None,
            'conversion_goal_5': None,
        }]
        return mock_stats

    def setUp(self):
        self.superuser = User.objects.get(id=1)
        self.user = User.objects.get(id=2)

        self.assertTrue(self.superuser.has_perm('zemauth.view_pubs_conversion_goals'))
        self.assertFalse(self.user.has_perm('zemauth.view_pubs_conversion_goals'))

    def test_no_permissions(self, mock_query, mock_touchpointconversins_query):
        ad_group = AdGroup.objects.get(pk=1)
        constraints = {'ad_group': ad_group.id}
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        date = datetime.date(2016, 3, 14)

        publisher_data_mock = self._mock_publisher_data(date)
        mock_query.side_effect = [publisher_data_mock]

        publishers_breakdown_fields = ['domain', 'exchange']
        publisher_data = stats_helper.get_publishers_data_and_conversion_goals(self.user, reports.api_publishers.query,
                                                                               date, date, constraints,
                                                                               conversion_goals,
                                                                               publishers_breakdown_fields)

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=publishers_breakdown_fields,
            order_fields=[],
            constraints=constraints,
            conversion_goals=[],
            constraints_list=[],
        )

        self.assertFalse(mock_touchpointconversins_query.called)
        self.assertEqual(publisher_data_mock, publisher_data)

    def test_with_conversion_goals_permissions(self, mock_query, mock_touchpointconversions_query):
        ad_group = AdGroup.objects.get(pk=1)
        constraints = {'ad_group': ad_group.id}
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        touchpoint_conversion_goal = ad_group.campaign.conversiongoal_set.filter(type=conversions_helper.PIXEL_GOAL_TYPE)[0]
        date = datetime.date(2016, 3, 14)

        publisher_data_mock = self._mock_publisher_data(date)
        mock_query.side_effect = [publisher_data_mock]

        touchpoint_data_mock = self._mock_touchpoint_data(date)
        mock_touchpointconversions_query.side_effect = [touchpoint_data_mock]

        publishers_breakdown_fields = ['domain', 'exchange']
        touchpoint_breakdown_fields = ['publisher', 'source']
        publisher_data = stats_helper.get_publishers_data_and_conversion_goals(self.superuser,
                                                                               reports.api_publishers.query,
                                                                               date,
                                                                               date,
                                                                               constraints,
                                                                               conversion_goals,
                                                                               publishers_breakdown_fields,
                                                                               touchpoint_breakdown_fields)

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=publishers_breakdown_fields,
            order_fields=[],
            constraints=constraints,
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversions_query.assert_any_call(
            date,
            date,
            breakdown=touchpoint_breakdown_fields,
            conversion_goals=[touchpoint_conversion_goal],
            constraints=constraints,
            constraints_list=[],
        )

        result_mock = self._mock_publishers_and_touchpoint_data(date)
        self.assertEqual(result_mock, publisher_data)

    @patch('dash.table.reports.api_publishers.query_active_publishers')
    def test_active_publishers_no_permissions(self, mock_active, mock_query, mock_touchpointconversions_query):
        ad_group = AdGroup.objects.get(pk=1)
        constraints = {'ad_group': ad_group.id}
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        date = datetime.date(2016, 3, 14)

        publisher_data_mock = self._mock_publisher_data(date)
        mock_active.side_effect = [publisher_data_mock]

        publishers_breakdown_fields = ['domain', 'exchange']
        touchpoint_breakdown_fields = ['publisher', 'source']
        publisher_data = stats_helper.get_publishers_data_and_conversion_goals(
            self.user,
            reports.api_publishers.query_active_publishers,
            date,
            date,
            constraints,
            conversion_goals,
            publishers_breakdown_fields,
            touchpoint_breakdown_fields,
            show_blacklisted_publishers=constants.PublisherBlacklistFilter.SHOW_ACTIVE)

        mock_active.assert_any_call(
            date,
            date,
            breakdown_fields=publishers_breakdown_fields,
            order_fields=[],
            constraints=constraints,
            conversion_goals=[],
            constraints_list=[],
        )

        self.assertFalse(mock_query.called)
        self.assertFalse(mock_touchpointconversions_query.called)
        self.assertEqual(publisher_data_mock, publisher_data)

    @patch('dash.table.reports.api_publishers.query_active_publishers')
    def test_active_publishers_with_conversion_goals_permissions(self, mock_active, mock_query, mock_touchpointconversions_query):
        ad_group = AdGroup.objects.get(pk=1)
        constraints = {'ad_group': ad_group.id}
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        touchpoint_conversion_goal = ad_group.campaign.conversiongoal_set.filter(type=conversions_helper.PIXEL_GOAL_TYPE)[0]
        date = datetime.date(2016, 3, 14)

        publisher_data_mock = self._mock_publisher_data(date)
        mock_active.side_effect = [publisher_data_mock]

        touchpoint_data_mock = self._mock_touchpoint_data(date)
        mock_touchpointconversions_query.side_effect = [touchpoint_data_mock]

        publishers_breakdown_fields = ['domain', 'exchange']
        touchpoint_breakdown_fields = ['publisher', 'source']
        publisher_data = stats_helper.get_publishers_data_and_conversion_goals(
            self.superuser,
            reports.api_publishers.query_active_publishers,
            date,
            date,
            constraints,
            conversion_goals,
            publishers_breakdown_fields,
            touchpoint_breakdown_fields,
            show_blacklisted_publishers=constants.PublisherBlacklistFilter.SHOW_ACTIVE)

        mock_active.assert_any_call(
            date,
            date,
            breakdown_fields=publishers_breakdown_fields,
            order_fields=[],
            constraints=constraints,
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversions_query.assert_any_call(
            date,
            date,
            breakdown=touchpoint_breakdown_fields,
            conversion_goals=[touchpoint_conversion_goal],
            constraints=constraints,
            constraints_list=[],
        )

        self.assertFalse(mock_query.called)

        result_mock = self._mock_publishers_and_touchpoint_data(date)
        self.assertEqual(result_mock, publisher_data)

    @patch('dash.table.reports.api_publishers.query_blacklisted_publishers')
    def test_blacklisted_publishers_no_permissions(self, mock_blacklisted, mock_query, mock_touchpointconversions_query):
        ad_group = AdGroup.objects.get(pk=1)
        constraints = {'ad_group': ad_group.id}
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        date = datetime.date(2016, 3, 14)

        publisher_data_mock = self._mock_publisher_data(date)
        mock_blacklisted.side_effect = [publisher_data_mock]

        publishers_breakdown_fields = ['domain', 'exchange']
        touchpoint_breakdown_fields = ['publisher', 'source']
        publisher_data = stats_helper.get_publishers_data_and_conversion_goals(
            self.user,
            reports.api_publishers.query_blacklisted_publishers,
            date,
            date,
            constraints,
            conversion_goals,
            publishers_breakdown_fields,
            touchpoint_breakdown_fields,
            show_blacklisted_publishers=constants.PublisherBlacklistFilter.SHOW_BLACKLISTED)

        mock_blacklisted.assert_any_call(
            date,
            date,
            breakdown_fields=publishers_breakdown_fields,
            order_fields=[],
            constraints=constraints,
            conversion_goals=[],
            constraints_list=[],
        )

        self.assertFalse(mock_query.called)
        self.assertFalse(mock_touchpointconversions_query.called)
        self.assertEqual(publisher_data_mock, publisher_data)

    @patch('dash.table.reports.api_publishers.query_blacklisted_publishers')
    def test_blacklisted_publishers_with_conversion_goals_permissions(self, mock_blacklisted, mock_query, mock_touchpointconversions_query):
        ad_group = AdGroup.objects.get(pk=1)
        constraints = {'ad_group': ad_group.id}
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        touchpoint_conversion_goal = ad_group.campaign.conversiongoal_set.filter(type=conversions_helper.PIXEL_GOAL_TYPE)[0]
        date = datetime.date(2016, 3, 14)

        publisher_data_mock = self._mock_publisher_data(date)
        mock_blacklisted.side_effect = [publisher_data_mock]

        touchpoint_data_mock = self._mock_touchpoint_data(date)
        mock_touchpointconversions_query.side_effect = [touchpoint_data_mock]

        publishers_breakdown_fields = ['domain', 'exchange']
        touchpoint_breakdown_fields = ['publisher', 'source']
        publisher_data = stats_helper.get_publishers_data_and_conversion_goals(
            self.superuser,
            reports.api_publishers.query_blacklisted_publishers,
            date,
            date,
            constraints,
            conversion_goals,
            publishers_breakdown_fields,
            touchpoint_breakdown_fields,
            show_blacklisted_publishers=constants.PublisherBlacklistFilter.SHOW_BLACKLISTED)

        mock_blacklisted.assert_any_call(
            date,
            date,
            breakdown_fields=publishers_breakdown_fields,
            order_fields=[],
            constraints=constraints,
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversions_query.assert_any_call(
            date,
            date,
            breakdown=touchpoint_breakdown_fields,
            conversion_goals=[touchpoint_conversion_goal],
            constraints=constraints,
            constraints_list=[],
        )

        self.assertFalse(mock_query.called)

        result_mock = self._mock_publishers_and_touchpoint_data(date)
        self.assertEqual(result_mock, publisher_data)

    @patch('dash.table.reports.api_publishers.query_active_publishers')
    def test_multiple_conversion_goals_with_same_pixel(self, mock_active, mock_query, mock_touchpointconversions_query):
        # add another 2 conversion goals with the same pixel but different windows
        extra1 = models.ConversionGoal.objects.get(pk=1)
        extra1.pk = None
        extra1.name = 'extra conversion goal 1'
        extra1.conversion_window = 1
        extra1.goal_id = '100'
        extra1.save()

        extra2 = models.ConversionGoal.objects.get(pk=1)
        extra2.pk = None
        extra2.name = 'extra conversion goal 2'
        extra2.conversion_window = 7
        extra2.goal_id = '101'
        extra2.save()

        ad_group = AdGroup.objects.get(pk=1)
        constraints = {'ad_group': ad_group.id}
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        touchpoint_conversion_goals = ad_group.campaign.conversiongoal_set.filter(type=conversions_helper.PIXEL_GOAL_TYPE)
        date = datetime.date(2016, 3, 14)

        publisher_data_mock = self._mock_publisher_data(date)
        mock_active.side_effect = [publisher_data_mock]

        mock_stats = [{
            'date': date.isoformat(),
            'conversion_count': 1168,
            'slug': 'test',
            'source': 7,
            'publisher': 'example.com',
            'conversion_window': 168,
            'account': 1,
        }, {
            'date': date.isoformat(),
            'conversion_count': 11,
            'slug': 'test',
            'source': 7,
            'publisher': 'example.com',
            'conversion_window': 1,
            'account': 1,
        }, {
            'date': date.isoformat(),
            'conversion_count': 77,
            'slug': 'test',
            'source': 7,
            'publisher': 'example.com',
            'conversion_window': 7,
            'account': 1,
        }]
        touchpoint_data_mock = mock_stats

        mock_touchpointconversions_query.side_effect = [touchpoint_data_mock]

        publishers_breakdown_fields = ['domain', 'exchange']
        touchpoint_breakdown_fields = ['publisher', 'source']
        publisher_data = stats_helper.get_publishers_data_and_conversion_goals(
            self.superuser,
            reports.api_publishers.query_active_publishers,
            date,
            date,
            constraints,
            conversion_goals,
            publishers_breakdown_fields,
            touchpoint_breakdown_fields,
            show_blacklisted_publishers=constants.PublisherBlacklistFilter.SHOW_ACTIVE)

        mock_active.assert_any_call(
            date,
            date,
            breakdown_fields=publishers_breakdown_fields,
            order_fields=[],
            constraints=constraints,
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversions_query.assert_any_call(
            date,
            date,
            breakdown=touchpoint_breakdown_fields,
            conversion_goals=list(touchpoint_conversion_goals),
            constraints=constraints,
            constraints_list=[],
        )

        self.assertFalse(mock_query.called)

        self.assertEqual([{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'e_data_cost': 0,
            'external_id': '12345',
            'total_cost': 3,
            'billing_cost': 3,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'license_fee': 0.6,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'example.com',
            'exchange': 'adiant',
            'conversion_goal_1': 1168,
            'conversion_goal_2': None,
            'conversion_goal_3': None,
            'conversion_goal_4': None,
            'conversion_goal_5': None,
            'conversion_goal_6': 11,
            'conversion_goal_7': 77,
        }], publisher_data)
