from decimal import Decimal
import dash
from mock import patch

from django import test

from automation import autopilot_budgets
import dash.models
import dash.constants
from reports import refresh


class AutopilotBudgetsTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    def test_uniformly_redistribute_remaining_budget(self):
        sources = [
            dash.models.AdGroupSource.objects.get(id=4),
            dash.models.AdGroupSource.objects.get(id=5),
            dash.models.AdGroupSource.objects.get(id=6),
            dash.models.AdGroupSource.objects.get(id=7),
        ]

        test_cases = (
            # min_budgets, returned_budgets, returned_comments
            ({sources[0]: '0.0', sources[1]: '0.0', sources[2]: '0.0', sources[3]: '10.0'}, 6,
             {sources[0]: '2.0', sources[1]: '2.0', sources[2]: '2.0', sources[3]: '10.0'}),
            ({sources[0]: '5.0', sources[1]: '3.0', sources[2]: '0.0', sources[3]: '10.0'}, 6,
             {sources[0]: '7.0', sources[1]: '5.0', sources[2]: '2.0', sources[3]: '10.0'}),
            ({sources[0]: '2.0', sources[1]: '2.0', sources[2]: '2.0', sources[3]: '10.0'}, 0,
             {sources[0]: '2.0', sources[1]: '2.0', sources[2]: '2.0', sources[3]: '10.0'}),
            ({sources[0]: '1.0', sources[1]: '1.0', sources[2]: '1.0', sources[3]: '10.0'}, 2,
             {sources[0]: '2.0', sources[1]: '2.0', sources[2]: '1.0', sources[3]: '10.0'})
        )

        for test_case in test_cases:
            self.assertEqual(
                autopilot_budgets._uniformly_redistribute_remaining_budget(
                    sources, Decimal(test_case[1]),
                    {k: Decimal(v) for k, v in test_case[0].items()}),
                {k: Decimal(v) for k, v in test_case[2].items()}
            )

    @patch('automation.autopilot_settings.AUTOPILOT_MIN_SPEND_PERC', 0.2)
    def test_get_active_sources_with_spend(self):
        s0 = dash.models.AdGroupSource.objects.get(id=5)
        s1 = dash.models.AdGroupSource.objects.get(id=1)
        test_cases = (
            # spends, returned_sources
            ({s0: {'yesterdays_spend_cc': 0.6}, s1: {'yesterdays_spend_cc': 0.6}}, [s0, s1]),
            ({s0: {'yesterdays_spend_cc': 0.6}, s1: {'yesterdays_spend_cc': 0.1}}, [s0]),
            ({s0: {'yesterdays_spend_cc': 0.1}, s1: {'yesterdays_spend_cc': 0.6}}, [s1]),
            ({s0: {'yesterdays_spend_cc': 0.1}, s1: {'yesterdays_spend_cc': 0.1}}, []),
            ({s0: {'yesterdays_spend_cc': 0.2}, s1: {'yesterdays_spend_cc': 0.2}}, [s0, s1])
        )
        spends = {s0: 1.0, s1: 1.0}
        for test_case in test_cases:
            self.assertEqual(autopilot_budgets._get_active_sources_with_spend(
                [s0, s1], test_case[0], spends), test_case[1])

    @patch('automation.autopilot_budgets._get_minimum_autopilot_budget_constraints')
    @patch('automation.autopilot_budgets._get_optimistic_autopilot_budget_constraints')
    def test_get_autopilot_budget_constraints(self, mock_opt_constr, mock_min_constr):
        sources = [0, 1]
        daily_budget = Decimal(100)
        mock_opt_constr.return_value = (None, {0: Decimal(20), 1: Decimal(20)}, None)
        autopilot_budgets._get_autopilot_budget_constraints(sources, daily_budget)
        mock_opt_constr.assert_called_with(sources)
        self.assertEqual(mock_min_constr.called, False)

        mock_min_constr.return_value = (None, None)
        mock_opt_constr.return_value = (None, {0: Decimal(200), 1: Decimal(200)}, None)
        autopilot_budgets._get_autopilot_budget_constraints(sources, daily_budget)
        mock_opt_constr.assert_called_with(sources)
        mock_min_constr.assert_called_with(sources)

    @patch('automation.autopilot_settings.MAX_BUDGET_GAIN', Decimal('10'))
    @patch('automation.autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET', Decimal('3'))
    def test_get_minimum_autopilot_budget_constraints(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        max_budgets, min_budgets = autopilot_budgets._get_minimum_autopilot_budget_constraints({s: {} for s in sources})
        self.assertEqual(max_budgets, {
            sources.get(id=1): Decimal('30'),
            sources.get(id=5): Decimal('50')
        })
        self.assertEqual(min_budgets, {
            sources.get(id=1): Decimal('3'),
            sources.get(id=5): Decimal('5')
        })

    @patch('dash.constants.SourceAllRTB.MIN_DAILY_BUDGET', Decimal('6'))
    @patch('automation.autopilot_settings.MAX_BUDGET_GAIN', Decimal('10'))
    @patch('automation.autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET', Decimal('3'))
    def test_get_minimum_autopilot_budget_constraints_rtb_as_one(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        data = {s: {} for s in sources}
        data[dash.constants.SourceAllRTB] = {'old_budget': Decimal(40.0)}
        max_budgets, min_budgets = autopilot_budgets._get_minimum_autopilot_budget_constraints(data)
        self.assertEqual(max_budgets, {
            sources.get(id=1): Decimal('30'),
            sources.get(id=5): Decimal('50'),
            dash.constants.SourceAllRTB: Decimal('60'),
        })
        self.assertEqual(min_budgets, {
            sources.get(id=1): Decimal('3'),
            sources.get(id=5): Decimal('5'),
            dash.constants.SourceAllRTB: Decimal('6'),
        })

    @patch('automation.autopilot_settings.MAX_BUDGET_GAIN', Decimal('10'))
    @patch('automation.autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET', Decimal('3'))
    @patch('automation.autopilot_settings.MAX_BUDGET_LOSS', Decimal('0.5'))
    def test_get_optimistic_autopilot_budget_constraints(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        data = {s: {} for s in sources}
        max_budgets, min_budgets, old_budgets = autopilot_budgets._get_optimistic_autopilot_budget_constraints(data)
        self.assertEqual(max_budgets, {
            sources.get(id=1): Decimal('600'),
            sources.get(id=5): Decimal('500')
        })
        self.assertEqual(min_budgets, {
            sources.get(id=1): Decimal('30'),
            sources.get(id=5): Decimal('25')
        })
        self.assertEqual(old_budgets, {
            sources.get(id=1): Decimal('60'),
            sources.get(id=5): Decimal('50')
        })

    @patch('automation.autopilot_settings.MAX_BUDGET_GAIN', Decimal('10'))
    @patch('automation.autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET', Decimal('3'))
    @patch('automation.autopilot_settings.MAX_BUDGET_LOSS', Decimal('0.5'))
    @patch('dash.constants.SourceAllRTB.MAX_DAILY_BUDGET', Decimal('100'))
    @patch('dash.constants.SourceAllRTB.MIN_DAILY_BUDGET', Decimal('10'))
    def test_get_optimistic_autopilot_budget_constraints_rtb_as_one(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        data = {s: {} for s in sources}
        data[dash.constants.SourceAllRTB] = {'old_budget': Decimal(40.0)}
        max_budgets, min_budgets, old_budgets = autopilot_budgets._get_optimistic_autopilot_budget_constraints(data)
        self.assertEqual(max_budgets, {
            sources.get(id=1): Decimal('600'),
            sources.get(id=5): Decimal('500'),
            dash.constants.SourceAllRTB: Decimal('400'),
        })
        self.assertEqual(min_budgets, {
            sources.get(id=1): Decimal('30'),
            sources.get(id=5): Decimal('25'),
            dash.constants.SourceAllRTB: Decimal('20'),
        })
        self.assertEqual(old_budgets, {
            sources.get(id=1): Decimal('60'),
            sources.get(id=5): Decimal('50'),
            dash.constants.SourceAllRTB: Decimal('40'),
        })
