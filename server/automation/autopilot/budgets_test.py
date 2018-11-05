import operator
from decimal import Decimal

from django import test
from mock import patch

import dash
import dash.constants
import dash.models

from . import budgets
from . import constants


class AutopilotBudgetsTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    def test_uniformly_redistribute_remaining_budget(self):
        sources = [
            dash.models.AdGroupSource.objects.get(id=4),
            dash.models.AdGroupSource.objects.get(id=5),
            dash.models.AdGroupSource.objects.get(id=6),
            dash.models.AdGroupSource.objects.get(id=7),
        ]

        test_cases = (
            # min_budgets, returned_budgets, returned_comments
            (
                {sources[0]: "0.0", sources[1]: "0.0", sources[2]: "0.0", sources[3]: "17.0"},
                6,
                {sources[0]: "2.0", sources[1]: "2.0", sources[2]: "2.0", sources[3]: "17.0"},
            ),
            (
                {sources[0]: "5.0", sources[1]: "3.0", sources[2]: "0.0", sources[3]: "17.0"},
                6,
                {sources[0]: "7.0", sources[1]: "5.0", sources[2]: "2.0", sources[3]: "17.0"},
            ),
            (
                {sources[0]: "2.0", sources[1]: "2.0", sources[2]: "2.0", sources[3]: "17.0"},
                0,
                {sources[0]: "2.0", sources[1]: "2.0", sources[2]: "2.0", sources[3]: "17.0"},
            ),
            (
                {sources[0]: "1.0", sources[1]: "1.0", sources[2]: "1.0", sources[3]: "17.0"},
                2,
                {sources[0]: "2.0", sources[1]: "2.0", sources[2]: "1.0", sources[3]: "17.0"},
            ),
        )

        for test_case in test_cases:
            self.assertEqual(
                budgets._uniformly_redistribute_remaining_budget(
                    sources,
                    Decimal(test_case[1]),
                    {k: Decimal(v) for k, v in list(test_case[0].items())},
                    {"fee": Decimal("0.15"), "margin": Decimal("0.3")},
                ),
                {k: Decimal(v) for k, v in list(test_case[2].items())},
            )

    @patch("automation.autopilot.settings.AUTOPILOT_MIN_SPEND_PERC", 0.2)
    def test_get_active_sources_with_spend(self):
        s0 = dash.models.AdGroupSource.objects.get(id=5)
        s1 = dash.models.AdGroupSource.objects.get(id=1)
        test_cases = (
            # spends, returned_sources
            ({s0: {"yesterdays_spend_cc": 0.6}, s1: {"yesterdays_spend_cc": 0.6}}, [s0, s1]),
            ({s0: {"yesterdays_spend_cc": 0.6}, s1: {"yesterdays_spend_cc": 0.1}}, [s0]),
            ({s0: {"yesterdays_spend_cc": 0.1}, s1: {"yesterdays_spend_cc": 0.6}}, [s1]),
            ({s0: {"yesterdays_spend_cc": 0.1}, s1: {"yesterdays_spend_cc": 0.1}}, []),
            ({s0: {"yesterdays_spend_cc": 0.2}, s1: {"yesterdays_spend_cc": 0.2}}, [s0, s1]),
        )
        spends = {s0: 1.0, s1: 1.0}
        for test_case in test_cases:
            self.assertEqual(budgets._get_active_sources_with_spend([s0, s1], test_case[0], spends), test_case[1])

    @patch("automation.autopilot.budgets._get_minimum_autopilot_budget_constraints")
    @patch("automation.autopilot.budgets._get_optimistic_autopilot_budget_constraints")
    def test_get_autopilot_budget_constraints(self, mock_opt_constr, mock_min_constr):
        sources = [0, 1]
        daily_budget = Decimal(100)
        mock_opt_constr.return_value = (None, {0: Decimal(20), 1: Decimal(20)}, None)
        budgets._get_autopilot_budget_constraints(
            sources, daily_budget, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        mock_opt_constr.assert_called_with(sources, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")})
        self.assertEqual(mock_min_constr.called, False)

        mock_min_constr.return_value = (None, None)
        mock_opt_constr.return_value = (None, {0: Decimal(200), 1: Decimal(200)}, None)
        budgets._get_autopilot_budget_constraints(
            sources, daily_budget, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        mock_opt_constr.assert_called_with(sources, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")})
        mock_min_constr.assert_called_with(sources, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")})

    @patch("automation.autopilot.settings.MAX_BUDGET_GAIN", Decimal("10"))
    @patch("automation.autopilot.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("3"))
    def test_get_minimum_autopilot_budget_constraints(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        max_budgets, min_budgets = budgets._get_minimum_autopilot_budget_constraints(
            {s: {} for s in sources}, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        self.assertEqual(max_budgets, {sources.get(id=1): Decimal("60"), sources.get(id=5): Decimal("90")})
        self.assertEqual(min_budgets, {sources.get(id=1): Decimal("6"), sources.get(id=5): Decimal("9")})

    @patch("core.models.all_rtb.AllRTBSourceType.min_daily_budget", Decimal("6"))
    @patch("automation.autopilot.settings.MAX_BUDGET_GAIN", Decimal("10"))
    @patch("automation.autopilot.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("3"))
    def test_get_minimum_autopilot_budget_constraints_rtb_as_one(self):
        all_rtb_ad_group_source = dash.models.AllRTBAdGroupSource(dash.models.AdGroup.objects.get(pk=1))
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        data = {s: {} for s in sources}
        data[all_rtb_ad_group_source] = {"old_budget": Decimal(40.0)}
        max_budgets, min_budgets = budgets._get_minimum_autopilot_budget_constraints(
            data, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        self.assertEqual(
            min_budgets,
            {sources.get(id=1): Decimal("6"), sources.get(id=5): Decimal("9"), all_rtb_ad_group_source: Decimal("11")},
        )
        self.assertEqual(
            max_budgets,
            {
                sources.get(id=1): Decimal("60"),
                sources.get(id=5): Decimal("90"),
                all_rtb_ad_group_source: Decimal("110"),
            },
        )

    @patch("automation.autopilot.settings.MAX_BUDGET_GAIN", Decimal("10"))
    @patch("automation.autopilot.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("3"))
    @patch("automation.autopilot.settings.MAX_BUDGET_LOSS", Decimal("0.5"))
    def test_get_optimistic_autopilot_budget_constraints(self):
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        data = {s: {"old_budget": s.settings.daily_budget_cc} for s in sources}
        max_budgets, min_budgets, old_budgets = budgets._get_optimistic_autopilot_budget_constraints(
            data, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        self.assertEqual(max_budgets, {sources.get(id=1): Decimal("600"), sources.get(id=5): Decimal("500")})
        self.assertEqual(min_budgets, {sources.get(id=1): Decimal("30"), sources.get(id=5): Decimal("25")})
        self.assertEqual(old_budgets, {sources.get(id=1): Decimal("60"), sources.get(id=5): Decimal("50")})

    @patch("automation.autopilot.settings.MAX_BUDGET_GAIN", Decimal("10"))
    @patch("automation.autopilot.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("3"))
    @patch("automation.autopilot.settings.MAX_BUDGET_LOSS", Decimal("0.5"))
    @patch("core.models.all_rtb.AllRTBSourceType.max_daily_budget", Decimal("100"))
    @patch("core.models.all_rtb.AllRTBSourceType.min_daily_budget", Decimal("10"))
    def test_get_optimistic_autopilot_budget_constraints_rtb_as_one(self):
        all_rtb_ad_group_source = dash.models.AllRTBAdGroupSource(dash.models.AdGroup.objects.get(pk=1))
        sources = dash.models.AdGroupSource.objects.filter(id__in=[1, 5])
        data = {s: {"old_budget": s.settings.daily_budget_cc} for s in sources}
        data[all_rtb_ad_group_source] = {"old_budget": Decimal(40.0)}
        max_budgets, min_budgets, old_budgets = budgets._get_optimistic_autopilot_budget_constraints(
            data, True, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        self.assertEqual(
            max_budgets,
            {
                sources.get(id=1): Decimal("600"),
                sources.get(id=5): Decimal("500"),
                all_rtb_ad_group_source: Decimal("400"),
            },
        )
        self.assertEqual(
            min_budgets,
            {
                sources.get(id=1): Decimal("30"),
                sources.get(id=5): Decimal("25"),
                all_rtb_ad_group_source: Decimal("20"),
            },
        )
        self.assertEqual(
            old_budgets,
            {
                sources.get(id=1): Decimal("60"),
                sources.get(id=5): Decimal("50"),
                all_rtb_ad_group_source: Decimal("40"),
            },
        )

    def test_ignore_budget_loss_when_no_ags_with_spend(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ags1 = dash.models.AllRTBAdGroupSource(dash.models.AdGroup.objects.get(pk=1))
        ags2 = dash.models.AllRTBAdGroupSource(dash.models.AdGroup.objects.get(pk=2))
        data = {
            ags1: {"old_budget": Decimal("500"), "yesterdays_spend_cc": 0},
            ags2: {"old_budget": Decimal("10"), "yesterdays_spend_cc": 0},
        }
        result = budgets.get_autopilot_daily_budget_recommendations(
            campaign, Decimal("500"), data, campaign.get_bcm_modifiers()
        )
        self.assertEqual(
            result,
            {
                ags1: {
                    "old_budget": Decimal("500"),
                    "new_budget": Decimal("250"),
                    "budget_comments": [constants.DailyBudgetChangeComment.NO_ACTIVE_SOURCES_WITH_SPEND],
                },
                ags2: {
                    "old_budget": Decimal("10"),
                    "new_budget": Decimal("250"),
                    "budget_comments": [constants.DailyBudgetChangeComment.NO_ACTIVE_SOURCES_WITH_SPEND],
                },
            },
        )


class BetaBanditTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    def test_naiive(self):
        ags = dash.models.AdGroupSource.objects.filter(ad_group=4)
        self.assertEqual(ags.count(), 4)

        bandit = budgets.BetaBandit([a for a in ags])

        for i in range(100):
            bandit.add_result(ags[0], True)

        recommendations = {s: 0 for s in ags}
        for i in range(100):
            recommendations[bandit.get_recommendation()] += 1

        most_recommended = max(iter(recommendations.items()), key=operator.itemgetter(1))[0]
        self.assertEqual(most_recommended, ags[0])
