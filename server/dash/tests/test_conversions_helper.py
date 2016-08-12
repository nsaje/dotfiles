from django import test
from dash import conversions_helper
from dash.models import AdGroup


class ConversionHelperTestCase(test.TestCase):
    fixtures = ['test_views.yaml', 'test_api.yaml']

    def _get_group_conversions_rows(self):
        rows = [{
            'dummy': 1,
            'conversions--1': 2,
            'conversions--dummy': 3,
        }, {
            'conversion-xyz': 'not_present',
            'conversions--xyz': 'present',
            'ignored__key': 'ignored_value',
        }]
        return rows

    def _get_transform_to_conversion_goals_rows(self):
        rows = [{
            'dummy_param_1': 'dummy_value_1',
            'dummy_param_2': 'dummy_value_2',
            'conversions': {
                'omniture__5': 5,
                'omniture__4': 4,
                'ga__3': 3,
                'dummy_conversion': -1,
            }
        }]
        return rows

    def _get_publishers_data(self):
        rows = [{
            'domain': 'dummy_domain',
            'exchange': 'adiant',
            'dummy_info': -100,
        }, {
            'domain': 'dummy_domain_2',
            'exchange': 'adiant',
            'dummy_info_2': -200,
        }]
        return rows

    def _get_touchpoint_data(self):
        rows = [{
            'source': 7,
            'publisher': 'dummy_domain',
            'slug': 'goal_1',
            'conversion_count': 100,
            'dummy_info': -1000,
            'account': 1,
            'conversion_window': 10
        }, {
            'source': -1,
            'publisher': 'wont_be_used',
            'slug': 'goal_none',
            'account': 1,
            'conversion_window': 12,
        }]
        return rows

    def test_empty_group_conversions(self):
        result = conversions_helper.group_conversions([])
        self.assertFalse(result)

    def test_group_conversions(self):
        rows = self._get_group_conversions_rows()
        result = conversions_helper.group_conversions(rows)

        self.assertDictEqual(result[0], {
            'dummy': 1,
            'conversions': {'1': 2, 'dummy': 3}
        })
        self.assertDictEqual(result[1], {
            'conversion-xyz': 'not_present',
            'ignored__key': 'ignored_value',
            'conversions': {'xyz': 'present'}
        })

    def test_empty_transform_to_conversion_goals(self):
        rows = self._get_transform_to_conversion_goals_rows()
        conversions_helper.transform_to_conversion_goals(rows, [])
        self.assertDictEqual(rows[0], rows[0])

    def test_transform_to_conversion_goals(self):
        ad_group = AdGroup.objects.get(pk=1)
        conversion_goals = ad_group.campaign.conversiongoal_set.all()

        rows = self._get_transform_to_conversion_goals_rows()
        conversions_helper.transform_to_conversion_goals(rows, conversion_goals)

        self.assertDictEqual(rows[0], {
            'dummy_param_1': 'dummy_value_1',
            'dummy_param_2': 'dummy_value_2',
            'conversion_goal_1': 0,
            'conversion_goal_2': None,
            'conversion_goal_3': 3,
            'conversion_goal_4': 4,
            'conversion_goal_5': 5,
        })

    def test_transform_report_conversion_goals(self):
        ad_group = AdGroup.objects.get(pk=1)
        report_conversion_goals = [cg for cg in ad_group.campaign.conversiongoal_set.all() if
                                   cg.type in conversions_helper.REPORT_GOAL_TYPES]

        rows = self._get_transform_to_conversion_goals_rows()
        conversions_helper.transform_to_conversion_goals(rows, report_conversion_goals)

        self.assertDictEqual(rows[0], {
            'dummy_param_1': 'dummy_value_1',
            'dummy_param_2': 'dummy_value_2',
            'conversion_goal_1': None,
            'conversion_goal_2': 3,
            'conversion_goal_3': 4,
            'conversion_goal_4': 5,
        })

    def test_empty_merge_touchpoint_convertions(self):
        publisher_data = [{'dummy': 'dummy'}]

        merged_data, reorder = conversions_helper.merge_touchpoint_conversions_to_publishers_data(
            publisher_data, [], [], [])
        self.assertEqual(merged_data, publisher_data)
        self.assertFalse(reorder)

    def test_merge_touchpoint_conversions_to_publishers_data(self):
        publishers_data = self._get_publishers_data()
        touchpoint_data = self._get_touchpoint_data()
        publisher_breakdown_fields = ['domain', 'exchange']
        touchpoint_breakdown_fields = ['publisher', 'source']

        merged_data, reorder = conversions_helper.merge_touchpoint_conversions_to_publishers_data(
            publishers_data,
            touchpoint_data,
            publisher_breakdown_fields,
            touchpoint_breakdown_fields)

        self.assertDictEqual(merged_data[0], {
            'domain': 'dummy_domain',
            'exchange': 'adiant',
            'dummy_info': -100,
            'conversions': {
                ('goal_1', 1, 10): 100,
            }
        })
        self.assertDictEqual(merged_data[1], {
            'domain': 'dummy_domain_2',
            'exchange': 'adiant',
            'dummy_info_2': -200,
        })
        self.assertFalse(reorder)

    def test_convert_touchpoint_source_id_field_to_bidder_slug(self):
        touchpoint_data = self._get_touchpoint_data()

        touchpoint_data = conversions_helper.convert_touchpoint_source_id_field_to_publisher_exchange(touchpoint_data)

        self.assertEqual(len(touchpoint_data), 1)
        self.assertDictEqual(touchpoint_data[0], {
            'source': 'adiant',
            'publisher': 'dummy_domain',
            'slug': 'goal_1',
            'conversion_count': 100,
            'dummy_info': -1000,
            'conversion_window': 10,
            'account': 1,
        })

    def test_empty_convert_constraint_exchange_to_source_id(self):
        constraints = {'ad_group_id': 1}
        results = conversions_helper.convert_constraint_exchanges_to_source_ids(constraints)

        self.assertDictEqual(constraints, results)

    def test_convert_constraint_exchange_to_source_id(self):
        constraints = {'ad_group_id': 1, 'exchange': ['adiant', 'dummy']}
        result = conversions_helper.convert_constraint_exchanges_to_source_ids(constraints)

        self.assertDictEqual(result, {
            'ad_group_id': 1,
            'source': [7],
        })
