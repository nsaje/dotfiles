from decimal import Decimal
from mock import patch

from django import test

from automation import autopilot_cpc
from automation.constants import CpcChangeComment
import dash.models
from reports import refresh


class AutopilotCpcTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    @patch('automation.autopilot_settings.AUTOPILOT_CPC_CHANGE_TABLE', (
        {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.5,
            'bid_cpc_proc_increase': Decimal('0.1')},
        {'underspend_upper_limit': -0.5, 'underspend_lower_limit': -
            0.1, 'bid_cpc_proc_increase': Decimal('0.5')},
        {'underspend_upper_limit': -0.1, 'underspend_lower_limit': 0,
            'bid_cpc_proc_increase': Decimal('-0.5')}
    )
    )
    @patch('automation.autopilot_settings.AUTOPILOT_MIN_CPC', Decimal('0.1'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_CPC', Decimal('3'))
    @patch('automation.autopilot_settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE', Decimal('0.2'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE', Decimal('0.3'))
    @patch('automation.autopilot_settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE', Decimal('0.05'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE', Decimal('0.25'))
    def test_calculate_new_autopilot_cpc(self):
        test_cases = (
            #  cpc, daily_budget, yesterday_spend, new_cpc, comments
            ('0', '10', '5', '0.1', [CpcChangeComment.CPC_NOT_SET,
                                     CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('0.5', '10', '8', '0.75', []),
            ('2.5', '10', '8', '2.75', []),
            ('0.5', '10', '10', '0.25', []),
            ('0.5', '10', '2', '0.55', []),
            ('0.5', '10', '0', '0.55', []),  # no yesterday spend
            ('0.5', '10', '5', '0.55', []),
            ('0.5', '-10', '5', '0.5', [CpcChangeComment.BUDGET_NOT_SET]),
            ('0.5', '10', '-5', '0.5', []),
            ('-0.5', '10', '5', '0.1', [CpcChangeComment.CPC_NOT_SET,
                                        CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('0.35', '10', '9.96', '0.15', []),
            ('2.8', '10', '9.96', '2.5', []),
            ('3.5', '10', '1', '3', [CpcChangeComment.CURRENT_CPC_TOO_HIGH]),
            ('0.05', '10', '1', '0.1', [CpcChangeComment.CURRENT_CPC_TOO_LOW])
        )
        for test_case in test_cases:
            self.assertEqual(autopilot_cpc.calculate_new_autopilot_cpc(
                Decimal(test_case[0]),
                Decimal(test_case[1]),
                Decimal(test_case[2])),
                (Decimal(test_case[3]), test_case[4]))

    @patch('automation.autopilot_settings.AUTOPILOT_MIN_CPC', Decimal('0.1'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_CPC', Decimal('3'))
    def test_get_calculate_cpc_comments(self):
        test_cases = (
            #  cpc, daily_budget, yesterday_spend, new_cpc, comments
            ('0.5', '0', '5', '0.5', [CpcChangeComment.BUDGET_NOT_SET]),
            ('0', '10', '5', '0.1', [CpcChangeComment.CPC_NOT_SET,
                                     CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('-0.5', '10', '5', '0.1', [CpcChangeComment.CPC_NOT_SET,
                                        CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('3.5', '10', '1', '3', [CpcChangeComment.CURRENT_CPC_TOO_HIGH]),
            ('0.5', '-10', '5', '0.5', [CpcChangeComment.BUDGET_NOT_SET]),
            ('0.05', '10', '1', '0.1', [CpcChangeComment.CURRENT_CPC_TOO_LOW])
        )
        for test_case in test_cases:
            self.assertEqual(autopilot_cpc._get_calculate_cpc_comments(
                Decimal(test_case[0]),
                Decimal(test_case[1]),
                Decimal(test_case[2])),
                (Decimal(test_case[3]), test_case[4]))

    @patch('automation.autopilot_settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE', Decimal('0.1'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE', Decimal('0.5'))
    def test_threshold_reducing_cpc(self):
        test_cases = (
            # old, new, returned_new
            ('0.3', '0.1', '0.1'),
            ('0.6', '0.1', '0.1'),
            ('0.8', '0.1', '0.3'),
            ('0.3', '0.25', '0.2'),
            ('0.3', '0.2', '0.2')
        )

        for test_case in test_cases:
            self.assertEqual(autopilot_cpc._threshold_reducing_cpc(
                Decimal(test_case[0]),
                Decimal(test_case[1])),
                Decimal(test_case[2]))

    @patch('automation.autopilot_settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE', Decimal('0.1'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE', Decimal('0.5'))
    def test_threshold_increasing_cpc(self):
        test_cases = (
            # old, new, returned_new
            ('0.1', '0.3', '0.3'),
            ('0.1', '0.6', '0.6'),
            ('0.1', '0.7', '0.6'),
            ('0.1', '0.15', '0.2')
        )

        for test_case in test_cases:
            self.assertEqual(autopilot_cpc._threshold_increasing_cpc(
                Decimal(test_case[0]),
                Decimal(test_case[1])),
                Decimal(test_case[2]))

    @patch('automation.autopilot_cpc._get_source_type_min_max_cpc')
    def test_threshold_source_constraints(self, mock_source_type_min_max_cpc):
        mock_source_type_min_max_cpc.return_value = (Decimal('0.1'), Decimal('1.0'))
        ags = dash.models.AdGroupSource.objects.get(id=1).source
        test_cases = (
            # proposed_cpc, returned_cpc, returned_comments
            ('0.1', '0.1', []),
            ('1.0', '1.0', []),
            ('0.01', '0.1', [CpcChangeComment.UNDER_SOURCE_MIN_CPC]),
            ('1.1', '1.0', [CpcChangeComment.OVER_SOURCE_MAX_CPC])
        )

        for test_case in test_cases:
            comments = []
            self.assertEqual(autopilot_cpc._threshold_source_constraints(
                Decimal(test_case[0]), ags, comments),
                Decimal(test_case[1]))
            self.assertEqual(comments, test_case[2])

    def test_threshold_ad_group_constraints(self):
        adgroup = dash.models.AdGroup.objects.get(id=1)
        test_cases = (
            # proposed_cpc, returned_cpc, returned_comments
            ('0.1', '0.1', []),
            ('100.00', '100.00', []),
            ('10000.00', '100.00', [CpcChangeComment.OVER_AD_GROUP_MAX_CPC])
        )

        for test_case in test_cases:
            comments = []
            self.assertEqual(autopilot_cpc._threshold_ad_group_constraints(
                Decimal(test_case[0]), adgroup, comments),
                Decimal(test_case[1]))
            self.assertEqual(comments, test_case[2])
