from collections import defaultdict
import datetime
from mock import patch
import re

from django.test import TestCase

import dash.constants
import dash.models
from reports import api_touchpointconversions
from utils.test_helper import RedshiftTestCase


@patch('reports.redshift.get_cursor')
class ApiTouchpointConversionsQueryTestCase(TestCase):
    fixtures = ['test_api_touchpointconversions.yaml']

    outer_query_aggregations = [
        'SUM(CASE WHEN conversion_id_ranked = 1 THEN 1 ELSE 0 END) AS "conversion_count"',
        'COUNT("touchpoint_id") AS "touchpoint_count"'
    ]

    inner_query_aggregations = [
        '*,',
        'RANK() OVER (PARTITION BY conversion_id ORDER BY touchpoint_timestamp DESC) AS "conversion_id_ranked"'
    ]

    def _get_query(self, mock_cursor):
        return mock_cursor().execute.call_args[0][0]

    def _check_parts(self, query, required_statements):
        for rs in required_statements:
            self.assertIn(rs, query)

    def test_query_no_breakdown(self, mock_cursor):
        campaign = dash.models.Campaign.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        conversion_goals = campaign.conversiongoal_set.all()
        constraints = {'campaign': campaign, 'source': dash.models.Source.objects.all()}

        api_touchpointconversions.query(start_date, end_date, conversion_goals=conversion_goals, constraints=constraints)
        q = self._get_query(mock_cursor)

        m = re.search('SELECT(.+?)FROM.*SELECT(.+?)FROM', q)
        self.assertTrue(m, 'should contain SELECT and FROM twice')
        self._check_parts(m.group(1), self.outer_query_aggregations + ['slug,', 'account_id,'])
        self._check_parts(m.group(2), self.inner_query_aggregations)

        outer_group_by = re.search('GROUP BY (.+)$', q).group(1)
        self.assertItemsEqual(['account_id', 'slug'], outer_group_by.split(','))

        self.assertEqual(2, q.count('WHERE'))

        where_regex = re.search('WHERE \((.+?)\)\) WHERE \((.+?)\) GROUP BY', q)
        inner_where = where_regex.group(1)
        self._check_parts(inner_where, ['account_id=%s AND slug=%s AND "conversion_lag"<=%s'])
        outer_where = where_regex.group(2)
        self._check_parts(outer_where, ['source_id IN ({})'.format(','.join(['%s'] * len(dash.models.Source.objects.all()))),
                                        'campaign_id=%s',
                                        '"date">=%s',
                                        '"date"<=%s'])

    def test_query_one_breakdown(self, mock_cursor):
        campaign = dash.models.Campaign.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = ['content_ad']
        conversion_goals = campaign.conversiongoal_set.all()
        constraints = {'campaign': campaign, 'source': dash.models.Source.objects.all()}

        api_touchpointconversions.query(start_date, end_date, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints)
        q = self._get_query(mock_cursor)

        m = re.search('SELECT(.+?)FROM.*SELECT(.+?)FROM', q)
        self.assertTrue(m, 'should contain SELECT and FROM twice')
        self._check_parts(m.group(1), self.outer_query_aggregations + ['slug,', 'account_id,', 'content_ad_id'])
        self._check_parts(m.group(2), self.inner_query_aggregations)

        outer_group_by = re.search('GROUP BY (.+)$', q).group(1)
        self.assertItemsEqual(['account_id', 'content_ad_id', 'slug'], outer_group_by.split(','))

        self.assertEqual(2, q.count('WHERE'))

        where_regex = re.search('WHERE \((.+?)\)\) WHERE \((.+?)\) GROUP BY', q)
        inner_where = where_regex.group(1)
        self._check_parts(inner_where, ['account_id=%s AND slug=%s AND "conversion_lag"<=%s'])
        outer_where = where_regex.group(2)
        self._check_parts(outer_where, ['source_id IN ({})'.format(','.join(['%s'] * len(dash.models.Source.objects.all()))),
                                        'campaign_id=%s',
                                        '"date">=%s',
                                        '"date"<=%s'])

    def test_query_two_breakdowns(self, mock_cursor):
        campaign = dash.models.Campaign.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = ['ad_group', 'source']
        conversion_goals = campaign.conversiongoal_set.all()
        constraints = {'campaign': campaign, 'source': dash.models.Source.objects.all()}

        api_touchpointconversions.query(start_date, end_date, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints)
        q = self._get_query(mock_cursor)

        m = re.search('SELECT(.+?)FROM.*SELECT(.+?)FROM', q)
        self.assertTrue(m, 'should contain SELECT and FROM twice')
        self._check_parts(m.group(1), self.outer_query_aggregations + ['slug,', 'account_id,', 'ad_group_id,', 'source_id'])
        self._check_parts(m.group(2), self.inner_query_aggregations)

        outer_group_by = re.search('GROUP BY (.+)$', q).group(1)
        self.assertItemsEqual(['account_id', 'ad_group_id', 'slug', 'source_id'], outer_group_by.split(','))

        self.assertEqual(2, q.count('WHERE'))

        where_regex = re.search('WHERE \((.+?)\)\) WHERE \((.+?)\) GROUP BY', q)
        inner_where = where_regex.group(1)
        self._check_parts(inner_where, ['account_id=%s AND slug=%s AND "conversion_lag"<=%s'])
        outer_where = where_regex.group(2)
        self._check_parts(outer_where, ['source_id IN ({})'.format(','.join(['%s'] * len(dash.models.Source.objects.all()))),
                                        'campaign_id=%s',
                                        '"date">=%s',
                                        '"date"<=%s'])

    def test_query_multiple_conversion_pixels(self, mock_cursor):
        cp = dash.models.ConversionPixel.objects.create(account=dash.models.Account.objects.get(id=1), slug='slug2')
        dash.models.ConversionGoal.objects.create(campaign=dash.models.Campaign.objects.get(id=1), type=dash.constants.ConversionGoalType.PIXEL, name='goal name 2', pixel=cp)

        campaign = dash.models.Campaign.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = ['ad_group', 'source']
        conversion_goals = campaign.conversiongoal_set.all()
        constraints = {'campaign': campaign, 'source': dash.models.Source.objects.all()}

        api_touchpointconversions.query(start_date, end_date, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints)
        q = self._get_query(mock_cursor)

        self.assertEqual(2, q.count('WHERE'))

        where_regex = re.search('WHERE \((.+?)\)\) WHERE \((.+?)\) GROUP BY', q)
        inner_where = where_regex.group(1)
        self._check_parts(inner_where, ['(account_id=%s AND slug=%s AND "conversion_lag"<=%s) OR (account_id=%s AND slug=%s AND "conversion_lag"<=%s)'])
        outer_where = where_regex.group(2)
        self._check_parts(outer_where, ['source_id IN ({})'.format(','.join(['%s'] * len(dash.models.Source.objects.all()))),
                                        'campaign_id=%s',
                                        '"date">=%s',
                                        '"date"<=%s'])


class ApiTouchpointConversionsDuplicatesRedshiftTest(RedshiftTestCase):

    fixtures = ['test_api_touchpointconversions.yaml', 'test_api_touchpointconversions.stats.yaml']

    def _check_values(self, with_breakdown, totals, breakdown, expected_values):
        breakdown_dict = {}
        for stat in with_breakdown:
            self.assertEqual(1, stat['account'])
            self.assertEqual('slug1', stat['slug'])
            self.assertTrue(tuple(stat[b] for b in breakdown) not in breakdown_dict)
            breakdown_dict[tuple(stat[b] for b in breakdown)] = stat

        totals_expected = defaultdict(int)
        keys = []
        for key, expected in expected_values.iteritems():
            if not isinstance(key, list):
                key = [key]
            key = tuple(key)
            keys.append(key)
            for expected_key, expected_val in expected.iteritems():
                self.assertEqual(expected_val, breakdown_dict[key][expected_key])
                totals_expected[expected_key] += expected_val
        self.assertTrue(len(set(breakdown_dict.keys()) - set(keys)) == 0)

        for k, v in totals_expected.iteritems():
            self.assertEqual(v, totals[k])

    def test_no_breakdown(self):
        d1 = datetime.date(2015, 11, 1)
        d2 = datetime.date(2015, 11, 30)
        ad_group = dash.models.AdGroup.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = []
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        constraints = {'ad_group': ad_group, 'source': dash.models.Source.objects.all()}

        result = api_touchpointconversions.query(d1, d2, conversion_goals=conversion_goals, constraints=constraints)
        self.assertEqual(result, [{'account': 1, 'conversion_count': 1L, 'touchpoint_count': 3L, 'slug': u'slug1'}])

    def test_no_duplicates_content_ad_level(self):
        d1 = datetime.date(2015, 11, 1)
        d2 = datetime.date(2015, 11, 30)
        ad_group = dash.models.AdGroup.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = ['content_ad']
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        constraints = {'ad_group': ad_group, 'source': dash.models.Source.objects.all()}

        with_breakdown = api_touchpointconversions.query(d1, d2, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints)
        totals = api_touchpointconversions.query(d1, d2, conversion_goals=conversion_goals, constraints=constraints)

        expected_values = {
            1: {
                'touchpoint_count': 2,
                'conversion_count': 1,
            },
            2: {
                'touchpoint_count': 1,
                'conversion_count': 0,
            }
        }
        self._check_values(with_breakdown, totals, breakdown, expected_values)

        ad_group_2 = dash.models.AdGroup.objects.get(id=2)
        constraints_ad_group_2 = {'ad_group': ad_group_2, 'source': dash.models.Source.objects.all()}
        with_breakdown_ad_group_2 = api_touchpointconversions.query(d1, d2, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints_ad_group_2)
        totals_ad_group_2 = api_touchpointconversions.query(d1, d2, conversion_goals=conversion_goals, constraints=constraints_ad_group_2)

        expected_values_ad_group_2 = {
            3: {
                'touchpoint_count': 1,
                'conversion_count': 0,
            },
        }
        self._check_values(with_breakdown_ad_group_2, totals_ad_group_2, breakdown, expected_values_ad_group_2)

    def test_no_duplicates_ad_group_source_level(self):
        d1 = datetime.date(2015, 11, 1)
        d2 = datetime.date(2015, 11, 30)
        ad_group = dash.models.AdGroup.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = ['source']
        conversion_goals = ad_group.campaign.conversiongoal_set.all()
        constraints = {'ad_group': ad_group, 'source': dash.models.Source.objects.all()}

        with_breakdown = api_touchpointconversions.query(d1, d2, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints)
        totals = api_touchpointconversions.query(d1, d2, conversion_goals=conversion_goals, constraints=constraints)

        expected_values = {
            1: {
                'touchpoint_count': 2,
                'conversion_count': 1,
            },
            2: {
                'touchpoint_count': 1,
                'conversion_count': 0,
            }
        }
        self._check_values(with_breakdown, totals, breakdown, expected_values)

        ad_group_2 = dash.models.AdGroup.objects.get(id=2)
        constraints_ad_group_2 = {'ad_group': ad_group_2, 'source': dash.models.Source.objects.all()}
        with_breakdown_ad_group_2 = api_touchpointconversions.query(d1, d2, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints_ad_group_2)
        totals_ad_group_2 = api_touchpointconversions.query(d1, d2, conversion_goals=conversion_goals, constraints=constraints_ad_group_2)

        expected_values_ad_group_2 = {
            1: {
                'touchpoint_count': 1,
                'conversion_count': 0,
            },
        }
        self._check_values(with_breakdown_ad_group_2, totals_ad_group_2, breakdown, expected_values_ad_group_2)


    def test_no_duplicates_campaign_ad_group_level(self):
        d1 = datetime.date(2015, 11, 1)
        d2 = datetime.date(2015, 11, 30)
        campaign = dash.models.Campaign.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = ['ad_group']
        conversion_goals = campaign.conversiongoal_set.all()
        constraints = {'campaign': campaign, 'source': dash.models.Source.objects.all()}

        with_breakdown = api_touchpointconversions.query(d1, d2, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints)
        totals = api_touchpointconversions.query(d1, d2, conversion_goals=conversion_goals, constraints=constraints)

        expected_values = {
            1: {
                'touchpoint_count': 3,
                'conversion_count': 1,
            },
            2: {
                'touchpoint_count': 1,
                'conversion_count': 0,
            }
        }
        self._check_values(with_breakdown, totals, breakdown, expected_values)


    def test_no_duplicates_campaign_source_level(self):
        d1 = datetime.date(2015, 11, 1)
        d2 = datetime.date(2015, 11, 30)
        campaign = dash.models.Campaign.objects.get(id=1)
        start_date = datetime.date(2015, 11, 1)
        end_date = datetime.date(2015, 11, 18)
        breakdown = ['source']
        conversion_goals = campaign.conversiongoal_set.all()
        constraints = {'campaign': campaign, 'source': dash.models.Source.objects.all()}

        with_breakdown = api_touchpointconversions.query(d1, d2, breakdown=breakdown, conversion_goals=conversion_goals, constraints=constraints)
        totals = api_touchpointconversions.query(d1, d2, conversion_goals=conversion_goals, constraints=constraints)

        expected_values = {
            1: {
                'touchpoint_count': 3,
                'conversion_count': 1,
            },
            2: {
                'touchpoint_count': 1,
                'conversion_count': 0,
            }
        }
        self._check_values(with_breakdown, totals, breakdown, expected_values)
