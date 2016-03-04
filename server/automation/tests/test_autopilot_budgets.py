from decimal import Decimal
import dash
from mock import patch

from django import test

from automation import autopilot_budgets
import dash.models
from reports import refresh


class AutopilotBudgetsTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    def test_uniformly_redistribute_remaining_budget(self):
        sources = [0, 1, 2]

        test_cases = (
            # min_budgets, returned_budgets, returned_comments
            (['0.0', '0.0', '0.0'], 6, ['2.0', '2.0', '2.0']),
            (['5.0', '3.0', '0.0'], 6, ['7.0', '5.0', '2.0']),
            (['2.0', '2.0', '2.0'], 0, ['2.0', '2.0', '2.0']),
            (['1.0', '1.0', '1.0'], 2, ['2.0', '2.0', '1.0'])
        )

        for test_case in test_cases:
            self.assertEqual(autopilot_budgets._uniformly_redistribute_remaining_budget(
                sources, Decimal(test_case[1]), [Decimal(b) for b in test_case[0]]),
                [Decimal(b) for b in test_case[2]])

    @patch('automation.autopilot_settings.AUTOPILOT_MIN_SPEND_PERC', 0.2)
    def test_get_active_sources_with_spend(self):
        sources = [0, 1]
        test_cases = (
            # spends, returned_sources
            ({0: {'spend_perc': 0.6}, 1: {'spend_perc': 0.6}}, [0, 1]),
            ({0: {'spend_perc': 0.6}, 1: {'spend_perc': 0.1}}, [0]),
            ({0: {'spend_perc': 0.1}, 1: {'spend_perc': 0.6}}, [1]),
            ({0: {'spend_perc': 0.1}, 1: {'spend_perc': 0.1}}, []),
            ({0: {'spend_perc': 0.2}, 1: {'spend_perc': 0.2}}, [0, 1])
        )
        for test_case in test_cases:
            self.assertEqual(autopilot_budgets._get_active_sources_with_spend(sources, test_case[0]), test_case[1])

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
    @patch('automation.autopilot_settings.MIN_SOURCE_BUDGET', Decimal('3'))
    def test_get_minimum_autopilot_budget_constraints(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        max_budgets, min_budgets = autopilot_budgets._get_minimum_autopilot_budget_constraints(sources)
        self.assertEqual(max_budgets, {
            sources.get(id=1): Decimal('30'),
            sources.get(id=5): Decimal('50')
        })
        self.assertEqual(min_budgets, {
            sources.get(id=1): Decimal('3'),
            sources.get(id=5): Decimal('5')
        })

    @patch('automation.autopilot_settings.MAX_BUDGET_GAIN', Decimal('10'))
    @patch('automation.autopilot_settings.MIN_SOURCE_BUDGET', Decimal('3'))
    @patch('automation.autopilot_settings.MAX_BUDGET_LOSS', Decimal('0.5'))
    def test_get_optimistic_autopilot_budget_constraints(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        max_budgets, min_budgets, old_budgets = autopilot_budgets._get_optimistic_autopilot_budget_constraints(sources)
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
