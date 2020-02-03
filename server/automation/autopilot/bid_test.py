import decimal
from decimal import Decimal

from django import test
from mock import patch

import dash.constants
import dash.models

from . import bid
from .constants import BidChangeComment


class AutopilotBidTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    @patch(
        "automation.autopilot.settings.AUTOPILOT_CPC_CHANGE_TABLE",
        (
            {"underspend_upper_limit": -1, "underspend_lower_limit": -0.5, "bid_proc_increase": Decimal("0.1")},
            {"underspend_upper_limit": -0.5, "underspend_lower_limit": -0.1, "bid_proc_increase": Decimal("0.5")},
            {"underspend_upper_limit": -0.1, "underspend_lower_limit": 0, "bid_proc_increase": Decimal("-0.5")},
        ),
    )
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_CPC", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_CPC", Decimal("3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE", Decimal("0.2"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE", Decimal("0.3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE", Decimal("0.05"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE", Decimal("0.25"))
    @patch(
        "automation.autopilot.settings.AUTOPILOT_CPM_CHANGE_TABLE",
        (
            {"underspend_upper_limit": -1, "underspend_lower_limit": -0.5, "bid_proc_increase": Decimal("0.1")},
            {"underspend_upper_limit": -0.5, "underspend_lower_limit": -0.1, "bid_proc_increase": Decimal("0.5")},
            {"underspend_upper_limit": -0.1, "underspend_lower_limit": 0, "bid_proc_increase": Decimal("-0.5")},
        ),
    )
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_CPM", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_CPM", Decimal("3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_REDUCING_CPM_CHANGE", Decimal("0.2"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_REDUCING_CPM_CHANGE", Decimal("0.3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_INCREASING_CPM_CHANGE", Decimal("0.05"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_INCREASING_CPM_CHANGE", Decimal("0.25"))
    def test_calculate_new_autopilot_bid(self):
        test_cases = (
            #  bid, daily_budget, yesterday_spend, new_bid, comments
            ("0", "10", "5", "0.1", [BidChangeComment.BID_NOT_SET, BidChangeComment.CURRENT_BID_TOO_LOW]),
            ("0.5", "10", "8", "0.75", []),
            ("2.5", "10", "8", "2.75", []),
            ("0.5", "10", "10", "0.25", []),
            ("0.5", "10", "2", "0.55", []),
            ("0.5", "10", "0", "0.55", []),  # no yesterday spend
            ("0.5", "10", "5", "0.55", []),
            ("0.5", "-10", "5", "0.5", [BidChangeComment.BUDGET_NOT_SET]),
            ("0.5", "10", "-5", "0.5", []),
            ("-0.5", "10", "5", "0.1", [BidChangeComment.BID_NOT_SET, BidChangeComment.CURRENT_BID_TOO_LOW]),
            ("0.35", "10", "9.96", "0.15", []),
            ("2.8", "10", "9.96", "2.5", []),
            ("3.5", "10", "1", "3", [BidChangeComment.CURRENT_BID_TOO_HIGH]),
            ("0.05", "10", "1", "0.1", [BidChangeComment.CURRENT_BID_TOO_LOW]),
        )
        campaign_goal = {
            "goal": dash.models.CampaignGoal(type=dash.constants.CampaignGoalKPI.TIME_ON_SITE),
            "value": Decimal("30"),
        }
        for test_case in test_cases:
            self.assertEqual(
                bid.calculate_new_autopilot_bid(
                    Decimal(test_case[0]), Decimal(test_case[1]), Decimal(test_case[2]), campaign_goal
                ),
                (Decimal(test_case[3]), test_case[4]),
            )

        adgroup = dash.models.AdGroup.objects.get(id=1)
        adgroup.bidding_type = dash.constants.BiddingType.CPM
        adgroup.save(None)
        for test_case in test_cases:
            self.assertEqual(
                bid.calculate_new_autopilot_bid(
                    Decimal(test_case[0]),
                    Decimal(test_case[1]),
                    Decimal(test_case[2]),
                    campaign_goal,
                    adgroup.bidding_type,
                ),
                (Decimal(test_case[3]), test_case[4]),
            )

    def test_calculate_new_autopilot_bid_min_cpc_goal(self):
        test_case = ("0.12", "10", "9.96")
        campaign_goal = {
            "goal": dash.models.CampaignGoal(type=dash.constants.CampaignGoalKPI.TIME_ON_SITE),
            "value": Decimal("5"),
        }
        new_bid, bid_change_comments = bid.calculate_new_autopilot_bid(
            Decimal(test_case[0]), Decimal(test_case[1]), Decimal(test_case[2]), campaign_goal
        )
        self.assertEqual(Decimal("0.114"), new_bid)
        self.assertEqual([], bid_change_comments)

        campaign_goal = {
            "goal": dash.models.CampaignGoal(type=dash.constants.CampaignGoalKPI.CPC),
            "value": Decimal("5"),
        }
        new_bid, bid_change_comments = bid.calculate_new_autopilot_bid(
            Decimal(test_case[0]), Decimal(test_case[1]), Decimal(test_case[2]), campaign_goal
        )
        self.assertEqual(4, new_bid)
        self.assertEqual([BidChangeComment.UNDER_GOAL_BID], bid_change_comments)

    @patch("automation.autopilot.settings.AUTOPILOT_CPC_NO_SPEND_CHANGE", Decimal("0.4"))
    @patch(
        "automation.autopilot.settings.AUTOPILOT_CPC_CHANGE_TABLE",
        (
            {"underspend_upper_limit": -1, "underspend_lower_limit": -0.5, "bid_proc_increase": Decimal("0.1")},
            {"underspend_upper_limit": -0.5, "underspend_lower_limit": -0.1, "bid_proc_increase": Decimal("0.5")},
            {"underspend_upper_limit": -0.1, "underspend_lower_limit": 0, "bid_proc_increase": Decimal("-0.5")},
        ),
    )
    @patch(
        "automation.autopilot.settings.AUTOPILOT_CPC_CHANGE_PERFORMANCE_FACTOR_TABLE",
        (
            {"performance_upper_limit": 1.0, "performance_lower_limit": 0.95, "performance_factor": Decimal("1.0")},
            {"performance_upper_limit": 0.95, "performance_lower_limit": 0.5, "performance_factor": Decimal("0.5")},
            {"performance_upper_limit": 0.5, "performance_lower_limit": 0.0, "performance_factor": Decimal("0.1")},
        ),
    )
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_CPC", Decimal("0.01"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_CPC", Decimal("3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE", Decimal("0.2"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE", Decimal("0.3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE", Decimal("0.05"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE", Decimal("0.25"))
    @patch("automation.autopilot.settings.AUTOPILOT_CPM_NO_SPEND_CHANGE", Decimal("0.4"))
    @patch(
        "automation.autopilot.settings.AUTOPILOT_CPM_CHANGE_TABLE",
        (
            {"underspend_upper_limit": -1, "underspend_lower_limit": -0.5, "bid_proc_increase": Decimal("0.1")},
            {"underspend_upper_limit": -0.5, "underspend_lower_limit": -0.1, "bid_proc_increase": Decimal("0.5")},
            {"underspend_upper_limit": -0.1, "underspend_lower_limit": 0, "bid_proc_increase": Decimal("-0.5")},
        ),
    )
    @patch(
        "automation.autopilot.settings.AUTOPILOT_CPM_CHANGE_PERFORMANCE_FACTOR_TABLE",
        (
            {"performance_upper_limit": 1.0, "performance_lower_limit": 0.95, "performance_factor": Decimal("1.0")},
            {"performance_upper_limit": 0.95, "performance_lower_limit": 0.5, "performance_factor": Decimal("0.5")},
            {"performance_upper_limit": 0.5, "performance_lower_limit": 0.0, "performance_factor": Decimal("0.1")},
        ),
    )
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_CPM", Decimal("0.01"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_CPM", Decimal("3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_REDUCING_CPM_CHANGE", Decimal("0.2"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_REDUCING_CPM_CHANGE", Decimal("0.3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_INCREASING_CPM_CHANGE", Decimal("0.05"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_INCREASING_CPM_CHANGE", Decimal("0.25"))
    def test_calculate_new_autopilot_bid_automatic_mode_rtb(self):
        test_cases = (
            #  bid, rtb_daily_budget, rtb_yesterday_spend, source_yesterday_spend, source_performance, new_bid, comments
            ("0", "10", "5", "2", 1.0, "0.01", [BidChangeComment.BID_NOT_SET, BidChangeComment.CURRENT_BID_TOO_LOW]),
            ("0.5", "10", "8", "2", 1.0, "0.75", []),
            ("2.5", "10", "8", "2", 1.0, "2.75", []),
            ("0.5", "10", "10", "2", 1.0, "0.25", []),
            ("0.5", "10", "2", "2", 1.0, "0.55", []),
            ("0.5", "10", "0", "2", 1.0, "0.55", []),  # no yesterday spend
            ("0.5", "10", "5", "2", 1.0, "0.55", []),
            ("0.5", "-10", "5", "2", 1.0, "0.5", [BidChangeComment.BUDGET_NOT_SET]),
            ("0.5", "10", "-5", "2", 1.0, "0.55", []),
            ("-0.5", "10", "5", "2", 1.0, "0.01", [BidChangeComment.BID_NOT_SET, BidChangeComment.CURRENT_BID_TOO_LOW]),
            ("0.35", "10", "9.96", "2", 1.0, "0.15", []),
            ("2.8", "10", "9.96", "2", 1.0, "2.5", []),
            ("3.5", "10", "1", "2", 1.0, "3", [BidChangeComment.CURRENT_BID_TOO_HIGH]),
            ("0.005", "10", "1", "2", 1.0, "0.01", [BidChangeComment.CURRENT_BID_TOO_LOW]),
            ("1.0", "10", "10", "2", 0.2, "0.7", []),
            ("0.5", "10", "10", "2", 0.7, "0.2", []),
            ("1.0", "10", "7", "2", 0.2, "0.7", []),
            ("0.5", "10", "10", "0", 1.0, "0.7", []),  # source with no spend
            ("0.5", "10", "8", "0", 1.0, "0.75", []),  # higher budget_fulfillment_factor overrides source with no spend
        )
        campaign_goal = {
            "goal": dash.models.CampaignGoal(type=dash.constants.CampaignGoalKPI.TIME_ON_SITE),
            "value": Decimal("30"),
        }
        for test_case in test_cases:
            new_bid, comments = bid.calculate_new_autopilot_bid_automatic_mode_rtb(
                Decimal(test_case[0]),
                Decimal(test_case[1]),
                Decimal(test_case[2]),
                Decimal(test_case[3]),
                test_case[4],
                campaign_goal,
            )
            self.assertEqual(
                (new_bid, comments),
                (Decimal(test_case[5]), test_case[6]),
                msg=(
                    "Expected bid: "
                    + test_case[5]
                    + " Actual: "
                    + str(new_bid)
                    + ' | Expected Comments: "'
                    + str(test_case[6])
                    + '" Actual: "'
                    + str(comments)
                    + '"'
                ),
            )

        adgroup = dash.models.AdGroup.objects.get(id=1)
        adgroup.bidding_type = dash.constants.BiddingType.CPM
        adgroup.save(None)
        for test_case in test_cases:
            new_bid, comments = bid.calculate_new_autopilot_bid_automatic_mode_rtb(
                Decimal(test_case[0]),
                Decimal(test_case[1]),
                Decimal(test_case[2]),
                Decimal(test_case[3]),
                test_case[4],
                campaign_goal,
                adgroup.bidding_type,
            )
            self.assertEqual(
                (new_bid, comments),
                (Decimal(test_case[5]), test_case[6]),
                msg=(
                    "Expected bid: "
                    + test_case[5]
                    + " Actual: "
                    + str(new_bid)
                    + ' | Expected Comments: "'
                    + str(test_case[6])
                    + '" Actual: "'
                    + str(comments)
                    + '"'
                ),
            )

    def test_calculate_new_autopilot_bid_automatic_mode_rtb_min_cpc_goal(self):
        campaign_goal = {
            "goal": dash.models.CampaignGoal(type=dash.constants.CampaignGoalKPI.TIME_ON_SITE),
            "value": Decimal("5"),
        }
        test_case = ("0.12", "10", "9.96", "2.5", 0.7)
        new_bid, bid_change_comments = bid.calculate_new_autopilot_bid_automatic_mode_rtb(
            Decimal(test_case[0]),
            Decimal(test_case[1]),
            Decimal(test_case[2]),
            Decimal(test_case[3]),
            test_case[4],
            campaign_goal,
        )
        self.assertEqual(Decimal("0.113"), new_bid)
        self.assertEqual([], bid_change_comments)

        campaign_goal = {
            "goal": dash.models.CampaignGoal(type=dash.constants.CampaignGoalKPI.CPC),
            "value": Decimal("5"),
        }
        new_bid, bid_change_comments = bid.calculate_new_autopilot_bid_automatic_mode_rtb(
            Decimal(test_case[0]),
            Decimal(test_case[1]),
            Decimal(test_case[2]),
            Decimal(test_case[3]),
            test_case[4],
            campaign_goal,
        )
        self.assertEqual(4, new_bid)
        self.assertEqual([BidChangeComment.UNDER_GOAL_BID], bid_change_comments)

    @patch("automation.autopilot.settings.AUTOPILOT_MIN_CPC", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_CPC", Decimal("3"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_CPM", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_CPM", Decimal("3"))
    def test_get_calculate_bid_comments(self):
        adgroup = dash.models.AdGroup.objects.get(id=1)
        adgroup.bidding_type = dash.constants.BiddingType.CPC
        adgroup.save(None)
        test_cases = (
            #  bid, daily_budget, yesterday_spend, new_bid, comments
            ("0.5", "0", "5", "0.5", [BidChangeComment.BUDGET_NOT_SET]),
            ("0", "10", "5", "0.1", [BidChangeComment.BID_NOT_SET, BidChangeComment.CURRENT_BID_TOO_LOW]),
            ("-0.5", "10", "5", "0.1", [BidChangeComment.BID_NOT_SET, BidChangeComment.CURRENT_BID_TOO_LOW]),
            ("3.5", "10", "1", "3", [BidChangeComment.CURRENT_BID_TOO_HIGH]),
            ("0.5", "-10", "5", "0.5", [BidChangeComment.BUDGET_NOT_SET]),
            ("0.05", "10", "1", "0.1", [BidChangeComment.CURRENT_BID_TOO_LOW]),
        )
        for test_case in test_cases:
            self.assertEqual(
                bid._get_calculate_bid_comments(
                    Decimal(test_case[0]), Decimal(test_case[1]), Decimal(test_case[2]), adgroup.bidding_type
                ),
                (Decimal(test_case[3]), test_case[4]),
            )

        adgroup.bidding_type = dash.constants.BiddingType.CPM
        adgroup.save(None)
        for test_case in test_cases:
            self.assertEqual(
                bid._get_calculate_bid_comments(
                    Decimal(test_case[0]), Decimal(test_case[1]), Decimal(test_case[2]), adgroup.bidding_type
                ),
                (Decimal(test_case[3]), test_case[4]),
            )

    @patch("automation.autopilot.settings.AUTOPILOT_MIN_REDUCING_CPC_CHANGE", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_REDUCING_CPC_CHANGE", Decimal("0.5"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_REDUCING_CPM_CHANGE", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_REDUCING_CPM_CHANGE", Decimal("0.5"))
    def test_threshold_reducing_bid(self):
        adgroup = dash.models.AdGroup.objects.get(id=1)
        adgroup.bidding_type = dash.constants.BiddingType.CPC
        adgroup.save(None)
        test_cases = (
            # old, new, returned_new
            ("0.3", "0.1", "0.1"),
            ("0.6", "0.1", "0.1"),
            ("0.8", "0.1", "0.3"),
            ("0.3", "0.25", "0.2"),
            ("0.3", "0.2", "0.2"),
        )

        for test_case in test_cases:
            self.assertEqual(
                bid._threshold_reducing_bid(Decimal(test_case[0]), Decimal(test_case[1]), adgroup.bidding_type),
                Decimal(test_case[2]),
            )

        adgroup.bidding_type = dash.constants.BiddingType.CPM
        adgroup.save(None)
        for test_case in test_cases:
            self.assertEqual(
                bid._threshold_reducing_bid(Decimal(test_case[0]), Decimal(test_case[1]), adgroup.bidding_type),
                Decimal(test_case[2]),
            )

    @patch("automation.autopilot.settings.AUTOPILOT_MIN_INCREASING_CPC_CHANGE", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_INCREASING_CPC_CHANGE", Decimal("0.5"))
    @patch("automation.autopilot.settings.AUTOPILOT_MIN_INCREASING_CPM_CHANGE", Decimal("0.1"))
    @patch("automation.autopilot.settings.AUTOPILOT_MAX_INCREASING_CPM_CHANGE", Decimal("0.5"))
    def test_threshold_increasing_bid(self):
        adgroup = dash.models.AdGroup.objects.get(id=1)
        adgroup.bidding_type = dash.constants.BiddingType.CPC
        adgroup.save(None)
        test_cases = (
            # old, new, returned_new
            ("0.1", "0.3", "0.3"),
            ("0.1", "0.6", "0.6"),
            ("0.1", "0.7", "0.6"),
            ("0.1", "0.15", "0.2"),
        )

        for test_case in test_cases:
            self.assertEqual(
                bid._threshold_increasing_bid(Decimal(test_case[0]), Decimal(test_case[1]), adgroup.bidding_type),
                Decimal(test_case[2]),
            )

        adgroup.bidding_type = dash.constants.BiddingType.CPM
        adgroup.save(None)
        for test_case in test_cases:
            self.assertEqual(
                bid._threshold_increasing_bid(Decimal(test_case[0]), Decimal(test_case[1]), adgroup.bidding_type),
                Decimal(test_case[2]),
            )

    @patch("automation.autopilot.bid._get_source_type_min_max_bid")
    def test_threshold_source_constraints(self, mock_source_type_min_max_bid):
        mock_source_type_min_max_bid.return_value = (Decimal("0.1"), Decimal("1.0"))
        ags_type = dash.models.AdGroupSource.objects.get(id=1).source.source_type
        ag_settings = dash.models.AdGroup.objects.get(id=1).get_current_settings()
        test_cases = (
            # proposed_bid, returned_bid, returned_comments
            ("0.1", "0.1", []),
            ("1.0", "1.0", []),
            ("0.01", "0.1", [BidChangeComment.UNDER_SOURCE_MIN_BID]),
            ("1.1", "1.0", [BidChangeComment.OVER_SOURCE_MAX_BID]),
        )

        for test_case in test_cases:
            comments = []
            self.assertEqual(
                bid._threshold_source_constraints(
                    Decimal(test_case[0]),
                    ags_type,
                    ag_settings,
                    comments,
                    {"fee": Decimal("0.15"), "margin": Decimal("0.3")},
                ),
                Decimal(test_case[1]),
            )
            self.assertEqual(comments, test_case[2])

    def test_get_source_type_min_max_bid(self):
        ags_type = dash.models.AdGroupSource.objects.get(id=1).source.source_type
        ags_type.max_cpc = Decimal("5.123")
        ags_type.min_cpc = Decimal("0.123")
        ags_type.save()
        ag_settings = dash.models.AdGroup.objects.get(id=1).get_current_settings()
        test_cases = ((ags_type, "0.207", "8.610"), (dash.models.AllRTBSourceType, "0.009", "33.613"))

        bcm_modifiers = {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        for test_case in test_cases:
            self.assertEqual(
                bid._get_source_type_min_max_bid(test_case[0], ag_settings, bcm_modifiers),
                (Decimal(test_case[1]), Decimal(test_case[2])),
            )

        ags_type.max_cpm = Decimal("5.123")
        ags_type.min_cpm = Decimal("0.123")
        ags_type.save()
        ag_settings.ad_group.bidding_type = dash.constants.BiddingType.CPM
        ag_settings.ad_group.save(None)

        test_cases = ((ags_type, "0.207", "8.610"), (dash.models.AllRTBSourceType, "0.017", "42.016"))

        bcm_modifiers = {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        for test_case in test_cases:
            self.assertEqual(
                bid._get_source_type_min_max_bid(test_case[0], ag_settings, bcm_modifiers),
                (Decimal(test_case[1]), Decimal(test_case[2])),
            )

    def test_round_bid(self):
        test_cases = (
            # bid, rounded_bid
            ("0.15", "0.15"),
            ("1.0", "1.0"),
            ("0.005", "0.01"),
            ("0.012", "0.01"),
            ("1.001", "1.0"),
        )

        for test_case in test_cases:
            self.assertEqual(
                bid._round_bid(Decimal(test_case[0]), decimal_places=2, rounding=decimal.ROUND_HALF_UP),
                Decimal(test_case[1]),
            )

    @patch("automation.autopilot.settings.AUTOPILOT_BID_MAX_DEC_PLACES", 3)
    def test_get_bid_max_decimal_places(self):
        test_cases = (
            # source_dec_places, returned_max_decimal_places
            (1, 1),
            (4, 3),
            (3, 3),
            (None, 3),
        )

        for test_case in test_cases:
            self.assertEqual(bid._get_bid_max_decimal_places(test_case[0]), test_case[1])

    def test_threshold_ad_group_constraints(self):
        adgroup = dash.models.AdGroup.objects.get(id=1)
        test_cases = (
            # proposed_bid, returned_bid, returned_comments
            ("0.1", "0.1", []),
            ("0.150", "0.150", []),
            ("0.160", "0.160", []),
            ("10000.00", "0.180", [BidChangeComment.OVER_AD_GROUP_MAX_AUTOPILOT_BID]),
        )

        for test_case in test_cases:
            comments = []
            self.assertEqual(
                bid._threshold_ad_group_constraints(Decimal(test_case[0]), adgroup, comments, 3), Decimal(test_case[1])
            )
            self.assertEqual(comments, test_case[2])

        test_cases = (
            # proposed_bid, returned_bid, returned_comments
            ("0.1", "0.1", []),
            ("0.160", "0.160", []),
            ("0.170", "0.170", []),
            ("10000.00", "0.180", [BidChangeComment.OVER_AD_GROUP_MAX_AUTOPILOT_BID]),
        )

        adgroup.bidding_type = dash.constants.BiddingType.CPM
        adgroup.save(None)
        for test_case in test_cases:
            comments = []
            self.assertEqual(
                bid._threshold_ad_group_constraints(Decimal(test_case[0]), adgroup, comments, 3), Decimal(test_case[1])
            )
            self.assertEqual(comments, test_case[2])
