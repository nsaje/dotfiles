import operator
from decimal import Decimal

from django import test
from mock import patch

import core.features.bcm
import dash
import dash.constants
import dash.models
from utils.magic_mixer import magic_mixer

from .. import constants
from .. import settings
from . import budgets


class AutopilotBudgetsTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    def test_uniformly_redistribute_remaining_budget(self):
        ad_groups = magic_mixer.cycle(4).blend(dash.models.AdGroup)

        test_cases = (
            # min_new_budgets, returned_budgets, returned_comments
            (
                {ad_groups[0]: "0.0", ad_groups[1]: "0.0", ad_groups[2]: "0.0", ad_groups[3]: "17.0"},
                6,
                {ad_groups[0]: "2.0", ad_groups[1]: "2.0", ad_groups[2]: "1.0", ad_groups[3]: "18.0"},
            ),
            (
                {ad_groups[0]: "5.0", ad_groups[1]: "3.0", ad_groups[2]: "0.0", ad_groups[3]: "17.0"},
                6,
                {ad_groups[0]: "7.0", ad_groups[1]: "5.0", ad_groups[2]: "1.0", ad_groups[3]: "18.0"},
            ),
            (
                {ad_groups[0]: "2.0", ad_groups[1]: "2.0", ad_groups[2]: "2.0", ad_groups[3]: "17.0"},
                0,
                {ad_groups[0]: "2.0", ad_groups[1]: "2.0", ad_groups[2]: "2.0", ad_groups[3]: "17.0"},
            ),
            (
                {ad_groups[0]: "1.0", ad_groups[1]: "1.0", ad_groups[2]: "1.0", ad_groups[3]: "17.0"},
                2,
                {ad_groups[0]: "2.0", ad_groups[1]: "2.0", ad_groups[2]: "1.0", ad_groups[3]: "17.0"},
            ),
        )

        for test_case in test_cases:
            self.assertEqual(
                budgets._uniformly_redistribute_remaining_budget(
                    {k: Decimal(v) for k, v in list(test_case[0].items())}, Decimal(test_case[1])
                ),
                {k: Decimal(v) for k, v in list(test_case[2].items())},
            )

    @patch("automation.autopilot.settings.AUTOPILOT_MIN_SPEND_PERC", 0.2)
    def test_get_active_ad_groups_with_spend(self):
        ad_groups = magic_mixer.cycle(2).blend(dash.models.AdGroup)
        test_cases = (
            # spends, returned_ad_groups
            (
                {ad_groups[0]: {"yesterdays_spend": 0.6}, ad_groups[1]: {"yesterdays_spend": 0.6}},
                [ad_groups[0], ad_groups[1]],
            ),
            ({ad_groups[0]: {"yesterdays_spend": 0.6}, ad_groups[1]: {"yesterdays_spend": 0.1}}, [ad_groups[0]]),
            ({ad_groups[0]: {"yesterdays_spend": 0.1}, ad_groups[1]: {"yesterdays_spend": 0.6}}, [ad_groups[1]]),
            ({ad_groups[0]: {"yesterdays_spend": 0.1}, ad_groups[1]: {"yesterdays_spend": 0.1}}, []),
            (
                {ad_groups[0]: {"yesterdays_spend": 0.2}, ad_groups[1]: {"yesterdays_spend": 0.2}},
                [ad_groups[0], ad_groups[1]],
            ),
        )
        spends = {ad_groups[0]: 1.0, ad_groups[1]: 1.0}
        for test_case in test_cases:
            self.assertEqual(budgets._get_active_ad_groups_with_spend(test_case[0], spends), test_case[1])

    @patch("automation.autopilot.service.budgets._get_minimum_autopilot_budget_constraints")
    @patch("automation.autopilot.service.budgets._get_optimistic_autopilot_budget_constraints")
    def test_get_autopilot_budget_constraints(self, mock_opt_constr, mock_min_constr):
        ad_groups = [0, 1]
        daily_budget = Decimal(100)
        mock_opt_constr.return_value = ({0: Decimal(20), 1: Decimal(20)}, None)
        bcm_modifiers = {"service_fee": Decimal("0.10"), "fee": Decimal("0.15"), "margin": Decimal("0.3")}
        autopilot_min_daily_budget = core.features.bcm.calculations.calculate_min_daily_budget(
            settings.BUDGET_AP_MIN_BUDGET, bcm_modifiers
        )
        budgets._get_autopilot_budget_constraints(ad_groups, daily_budget, bcm_modifiers)
        mock_opt_constr.assert_called_with(ad_groups, autopilot_min_daily_budget)
        self.assertEqual(mock_min_constr.called, False)

        mock_min_constr.return_value = None
        mock_opt_constr.return_value = ({0: Decimal(200), 1: Decimal(200)}, None)
        budgets._get_autopilot_budget_constraints(ad_groups, daily_budget, bcm_modifiers)
        mock_opt_constr.assert_called_with(ad_groups, autopilot_min_daily_budget)
        mock_min_constr.assert_called_with(ad_groups, bcm_modifiers, autopilot_min_daily_budget)

    @patch("automation.autopilot.settings.BUDGET_AP_MIN_BUDGET", Decimal("7"))
    def test_get_minimum_autopilot_budget_constraints(self):
        ad_groups = magic_mixer.cycle(2).blend(dash.models.AdGroup)
        min_budgets = budgets._get_minimum_autopilot_budget_constraints(
            {ag: {} for ag in ad_groups},
            {"service_fee": Decimal("0.10"), "fee": Decimal("0.15"), "margin": Decimal("0.3")},
        )
        self.assertEqual(min_budgets, {ad_groups[0]: Decimal("14"), ad_groups[1]: Decimal("14")})

    @patch("automation.autopilot.settings.BUDGET_AP_MIN_BUDGET", Decimal("20"))
    @patch("automation.autopilot.settings.MAX_BUDGET_LOSS", Decimal("0.5"))
    @patch("core.models.all_rtb.AllRTBSourceType.max_daily_budget", Decimal("100"))
    def test_get_optimistic_autopilot_budget_constraints(self):
        ad_groups = magic_mixer.cycle(2).blend(dash.models.AdGroup)
        data = {ad_groups[0]: {"old_budget": 60}, ad_groups[1]: {"old_budget": 50}}
        bcm_modifiers = {"service_fee": Decimal("0.10"), "fee": Decimal("0.15"), "margin": Decimal("0.3")}
        autopilot_min_daily_budget = core.features.bcm.calculations.calculate_min_daily_budget(
            settings.BUDGET_AP_MIN_BUDGET, bcm_modifiers
        )
        min_new_budgets, old_budgets = budgets._get_optimistic_autopilot_budget_constraints(
            data, autopilot_min_daily_budget
        )
        self.assertEqual(min_new_budgets, {ad_groups[0]: Decimal("38"), ad_groups[1]: Decimal("38")})
        self.assertEqual(old_budgets, {ad_groups[0]: Decimal("60"), ad_groups[1]: Decimal("50")})

    def test_ignore_budget_loss_when_no_ags_with_spend(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ad_groups = magic_mixer.cycle(2).blend(dash.models.AdGroup, campaign=campaign)
        data = {
            ad_groups[0]: {"old_budget": Decimal("500"), "yesterdays_spend": 0},
            ad_groups[1]: {"old_budget": Decimal("10"), "yesterdays_spend": 0},
        }
        result = budgets.get_autopilot_daily_budget_recommendations(
            campaign, Decimal("500"), data, campaign.get_bcm_modifiers()
        )
        self.assertEqual(
            result,
            {
                ad_groups[0]: {
                    "old_budget": Decimal("500"),
                    "new_budget": Decimal("250"),
                    "budget_comments": [constants.DailyBudgetChangeComment.NO_ACTIVE_AD_GROUPS_WITH_SPEND],
                },
                ad_groups[1]: {
                    "old_budget": Decimal("10"),
                    "new_budget": Decimal("250"),
                    "budget_comments": [constants.DailyBudgetChangeComment.NO_ACTIVE_AD_GROUPS_WITH_SPEND],
                },
            },
        )


class BetaBanditTestCase(test.TestCase):
    def test_naiive(self):
        ad_groups = magic_mixer.cycle(4).blend(dash.models.AdGroup)
        self.assertEqual(len(ad_groups), 4)

        bandit = budgets.BetaBandit([ag for ag in ad_groups])

        for i in range(100):
            bandit.add_result(ad_groups[0], True)

        recommendations = {ag: 0 for ag in ad_groups}
        for i in range(100):
            recommendations[bandit.get_recommendation()] += 1

        most_recommended = max(iter(recommendations.items()), key=operator.itemgetter(1))[0]
        self.assertEqual(most_recommended, ad_groups[0])
