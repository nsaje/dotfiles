import decimal
from decimal import Decimal
from mock import patch

from django import test

from automation import autopilot_cpc
from automation.constants import CpcChangeComment
import dash.models
import dash.constants


class AutopilotCpcTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

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

    @patch('automation.autopilot_settings.AUTOPILOT_CPC_CHANGE_TABLE', (
        {'underspend_upper_limit': -1, 'underspend_lower_limit': -0.5,
            'bid_cpc_proc_increase': Decimal('0.1')},
        {'underspend_upper_limit': -0.5, 'underspend_lower_limit': -0.1,
            'bid_cpc_proc_increase': Decimal('0.5')},
        {'underspend_upper_limit': -0.1, 'underspend_lower_limit': 0,
            'bid_cpc_proc_increase': Decimal('-0.5')}
    ))
    @patch('automation.autopilot_settings.AUTOPILOT_CPC_CHANGE_PERFORMANCE_FACTOR_TABLE', (
        {'performance_upper_limit': 1.0, 'performance_lower_limit': 0.95, 'performance_factor': Decimal('1.0')},
        {'performance_upper_limit': 0.95, 'performance_lower_limit': 0.5, 'performance_factor': Decimal('0.5')},
        {'performance_upper_limit': 0.5, 'performance_lower_limit': 0.0, 'performance_factor': Decimal('0.1')},
    ))
    @patch('automation.autopilot_settings.AUTOPILOT_MIN_CPC', Decimal('0.01'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_CPC', Decimal('3'))
    @patch('automation.autopilot_settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE', Decimal('0.2'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE', Decimal('0.3'))
    @patch('automation.autopilot_settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE', Decimal('0.05'))
    @patch('automation.autopilot_settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE', Decimal('0.25'))
    def test_calculate_new_autopilot_cpc_automatic_mode_rtb(self):
        test_cases = (
            #  cpc, rtb_daily_budget, rtb_yesterday_spend, source_performance, new_cpc, comments
            ('0', '10', '5', 1.0, '0.01', [CpcChangeComment.CPC_NOT_SET,
                                           CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('0.5', '10', '8', 1.0, '0.75', []),
            ('2.5', '10', '8', 1.0, '2.75', []),
            ('0.5', '10', '10', 1.0, '0.25', []),
            ('0.5', '10', '2', 1.0, '0.55', []),
            ('0.5', '10', '0', 1.0, '0.55', []),  # no yesterday spend
            ('0.5', '10', '5', 1.0, '0.55', []),
            ('0.5', '-10', '5', 1.0, '0.5', [CpcChangeComment.BUDGET_NOT_SET]),
            ('0.5', '10', '-5', 1.0, '0.55', []),
            ('-0.5', '10', '5', 1.0, '0.01', [CpcChangeComment.CPC_NOT_SET,
                                              CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('0.35', '10', '9.96', 1.0, '0.15', []),
            ('2.8', '10', '9.96', 1.0, '2.5', []),
            ('3.5', '10', '1', 1.0, '3', [CpcChangeComment.CURRENT_CPC_TOO_HIGH]),
            ('0.005', '10', '1', 1.0, '0.01', [CpcChangeComment.CURRENT_CPC_TOO_LOW]),
            ('1.0', '10', '10', 0.2, '0.7', []),
            ('0.5', '10', '10', 0.7, '0.2', []),
            ('1.0', '10', '7', 0.2, '0.7', [])
        )
        for test_case in test_cases:
            new_cpc, comments = autopilot_cpc.calculate_new_autopilot_cpc_automatic_mode_rtb(
                Decimal(test_case[0]),
                Decimal(test_case[1]),
                Decimal(test_case[2]),
                test_case[3])
            self.assertEqual(
                (new_cpc, comments),
                (Decimal(test_case[4]), test_case[5]),
                msg=('Expected cpc: ' + test_case[4] + ' Actual: ' + str(new_cpc) +
                     ' | Expected Comments: "' + str(test_case[5]) + '" Actual: "' + str(comments) + '"'
                     ))

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
        ags_type = dash.models.AdGroupSource.objects.get(id=1).source.source_type
        ag_settings = dash.models.AdGroup.objects.get(id=1).get_current_settings()
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
                Decimal(test_case[0]), ags_type, ag_settings, comments, {'fee': Decimal('0.15'), 'margin': Decimal('0.3')}),
                Decimal(test_case[1]))
            self.assertEqual(comments, test_case[2])

    @patch('dash.models.SourceType.get_min_cpc')
    def test_get_source_type_min_max_cpc(self, mock_get_min_cpc):
        mock_get_min_cpc.return_value = Decimal('0.123')
        ags_type = dash.models.AdGroupSource.objects.get(id=1).source.source_type
        ags_type.max_cpc = Decimal('5.123')
        ags_type.save()
        ag_settings = dash.models.AdGroup.objects.get(id=1).get_current_settings()
        test_cases = (
            (ags_type, '0.123', '8.610'),
            (dash.constants.SourceAllRTB, '0.017', '11.764'),
        )

        bcm_modifiers = {'fee': Decimal('0.15'), 'margin': Decimal('0.3')}
        for test_case in test_cases:
            self.assertEqual(autopilot_cpc._get_source_type_min_max_cpc(test_case[0], ag_settings, bcm_modifiers),
                             (Decimal(test_case[1]), Decimal(test_case[2])))

    def test_threshold_cpc_constraints(self):
        s1 = dash.models.Source.objects.get(pk=1)
        s2 = dash.models.Source.objects.get(pk=2)
        b1 = dash.models.SourceType.objects.get(pk=3)
        s1.source_type = b1
        s1.save()
        s2.source_type = b1
        s2.save()
        rtb = dash.constants.SourceAllRTB
        dash.models.CpcConstraint.objects.create(
            ad_group_id=3,
            max_cpc=Decimal('1.5'),
        )
        dash.models.CpcConstraint.objects.create(
            ad_group_id=2,
            source=s1,
            min_cpc=Decimal('0.65'),
        )
        dash.models.CpcConstraint.objects.create(
            ad_group_id=3,
            source=s2,
            min_cpc=Decimal('0.5'),
        )
        dash.models.CpcConstraint.objects.create(
            account_id=1,
            source=s1,
            min_cpc=Decimal('0.65'),
            max_cpc=Decimal('1.65'),
        )

        test_cases = (
            (1, s2, '0.01', '1.5', '1.5', [], []),
            (1, s2, '0.01', '0.01', '0.01', [], []),
            (1, s1, '0.01', '0.01', '0.65', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], []),
            (1, s1, '0.01', '2.00', '1.65', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], []),
            (2, s1, '0.01', '0.1', '0.65', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], []),
            (2, s2, '0.01', '0.1', '0.1', [], []),
            (3, s1, '0.01', '0.5', '0.5', [], []),
            (3, s1, '0.01', '2.5', '1.5', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], []),
            (3, s1, '0.01', '0.1', '0.1', [], []),
            (3, s2, '0.01', '1.6', '1.5', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], []),
            (3, s2, '0.01', '0.1', '0.5', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], []),
            (1, rtb, '0.65', '1.0', '1.0', [], [rtb, s1, s2]),
            (1, rtb, '0.65', '2.0', '1.65', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], [rtb, s1, s2]),
            (1, rtb, '0.75', '0.1', '0.65', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], [rtb, s1, s2]),
            (3, rtb, '0.75', '3.1', '1.5', [CpcChangeComment.CPC_CONSTRAINT_APPLIED], [rtb, s1, s2]),
        )
        for ad_group_id, source, old_cpc, proposed_cpc, expected_cpc, expected_comment, sources in test_cases:
            comments = []
            adjusted_cpc = autopilot_cpc._threshold_cpc_constraints(
                dash.models.AdGroup.objects.get(pk=ad_group_id),
                source,
                Decimal(old_cpc),
                Decimal(proposed_cpc),
                comments,
                sources)

            self.assertEqual(adjusted_cpc, Decimal(expected_cpc))
            self.assertEqual(comments, expected_comment)

    def test_round_cpc(self):
        test_cases = (
            # cpc, rounded_cpc
            ('0.15', '0.15'),
            ('1.0', '1.0'),
            ('0.005', '0.01'),
            ('0.012', '0.01'),
            ('1.001', '1.0')
        )

        for test_case in test_cases:
            self.assertEqual(autopilot_cpc._round_cpc(
                Decimal(test_case[0]), decimal_places=2, rounding=decimal.ROUND_HALF_UP),
                Decimal(test_case[1]))

    @patch('automation.autopilot_settings.AUTOPILOT_CPC_MAX_DEC_PLACES', 3)
    def test_get_cpc_max_decimal_places(self):
        test_cases = (
            # source_dec_places, returned_max_decimal_places
            (1, 1),
            (4, 3),
            (3, 3),
            (None, 3),
        )

        for test_case in test_cases:
            self.assertEqual(autopilot_cpc._get_cpc_max_decimal_places(test_case[0]), test_case[1])

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
                Decimal(test_case[0]), adgroup, comments, 3),
                Decimal(test_case[1]))
            self.assertEqual(comments, test_case[2])
