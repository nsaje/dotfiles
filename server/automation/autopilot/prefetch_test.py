import itertools
from decimal import Decimal

from django.test import TestCase
from mock import patch

from core.models import all_rtb
from dash import constants
from dash import models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import prefetch


class AutopilotPrefetchTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.today = dates_helper.local_today()

        cls.ad_group_source = magic_mixer.blend(models.AdGroupSource, source__source_type__type=constants.SourceType.B1)
        cls.ad_group_source.settings.update_unsafe(None, daily_budget_cc=1000)
        cls.entities = {cls.ad_group_source.ad_group.campaign: {cls.ad_group_source.ad_group: [cls.ad_group_source]}}
        cls.all_rtb_ad_group_source = all_rtb.AllRTBAdGroupSource(cls.ad_group_source.ad_group)

        cls.conversion_goal = magic_mixer.blend(
            models.ConversionGoal,
            type=constants.ConversionGoalType.PIXEL,
            campaign=cls.ad_group_source.ad_group.campaign,
            conversion_window=30,
            pixel__account=cls.ad_group_source.ad_group.campaign.account,
        )
        cls.goal_value = magic_mixer.blend(
            models.CampaignGoalValue,
            campaign_goal__campaign=cls.ad_group_source.ad_group.campaign,
            campaign_goal__conversion_goal=cls.conversion_goal,
            campaign_goal__primary=True,
            value=20,
        )
        magic_mixer.blend(
            models.CampaignGoalValue,
            campaign_goal__campaign=cls.ad_group_source.ad_group.campaign,
            campaign_goal__primary=False,
            value=30,
        )

        magic_mixer.blend(
            models.BudgetLineItem,
            campaign=cls.ad_group_source.ad_group.campaign,
            credit__account=cls.ad_group_source.ad_group.campaign.account,
            credit__start_date=cls.today,
            credit__end_date=dates_helper.day_after(cls.today),
            credit__amount=100000,
            credit__status=constants.CreditLineItemStatus.SIGNED,
            credit__service_fee=Decimal("0.1"),
            credit__license_fee=Decimal("0.2"),
            amount=10000,
            start_date=cls.today,
            end_date=dates_helper.day_after(cls.today),
        )

    def setUp(self):
        pixel_key = "pixel_{id}_{window}".format(id=self.conversion_goal.pixel_id, window=30)
        redshift_patcher = patch("automation.autopilot.prefetch.redshiftapi.api_breakdowns.query")
        self.mock_rs = redshift_patcher.start()
        self.mock_rs.side_effect = itertools.cycle(
            [
                [
                    {
                        "ad_group_id": self.ad_group_source.ad_group_id,
                        "source_id": self.ad_group_source.source_id,
                        "clicks": 13,
                        "etfm_cost": 25,
                    }
                ],
                [
                    {
                        "ad_group_id": self.ad_group_source.ad_group_id,
                        "source_id": self.ad_group_source.source_id,
                        "avg_tos": 16,
                        "total_seconds": 32,
                        "visits": 2,
                    }
                ],
                [
                    {
                        "ad_group_id": self.ad_group_source.ad_group_id,
                        "source_id": self.ad_group_source.source_id,
                        pixel_key: 3,
                        "etfm_cost": 25,
                    }
                ],
            ]
        )
        self.addCleanup(redshift_patcher.stop)

    def test_other_goal(self):
        self.ad_group_source.ad_group.settings.update_unsafe(None, b1_sources_group_enabled=True)
        data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(self.entities)

        expected_data = {
            self.ad_group_source.ad_group: {
                self.ad_group_source: {
                    "avg_tos": 16,
                    "dividend": 32.0,
                    "divisor": 2.0,
                    "goal_optimal": Decimal("20"),
                    "goal_performance": 0.8,
                    "old_budget": 1000,
                    "old_bid": Decimal("0.15"),
                    "spend_perc": Decimal("0.025"),
                    "yesterdays_clicks": 13,
                    "yesterdays_spend_cc": Decimal("25"),
                },
                self.all_rtb_ad_group_source: {
                    "avg_tos": 16.0,
                    "dividend": 32.0,
                    "divisor": 2.0,
                    "goal_optimal": Decimal("20"),
                    "goal_performance": 0.8,
                    "old_budget": Decimal("50.00"),
                    "old_bid": Decimal("0.45"),
                    "spend_perc": Decimal("0.5"),
                    "yesterdays_clicks": 13,
                    "yesterdays_spend_cc": Decimal("25"),
                },
            }
        }
        expected_goals = {
            self.ad_group_source.ad_group.campaign: {
                "goal": self.goal_value.campaign_goal,
                "value": self.goal_value.value,
            }
        }
        expected_bcm = {
            self.ad_group_source.ad_group.campaign: {
                "service_fee": Decimal("0.1"),
                "fee": Decimal("0.2"),
                "margin": Decimal("0"),
            }
        }
        self.assertEqual(data, expected_data)
        self.assertEqual(campaign_goals, expected_goals)
        self.assertEqual(bcm_modifiers_map, expected_bcm)

    def test_cpa_goal(self):
        self.goal_value.campaign_goal.type = constants.CampaignGoalKPI.CPA
        self.goal_value.campaign_goal.save()

        self.ad_group_source.ad_group.settings.update_unsafe(None, b1_sources_group_enabled=True)
        data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(self.entities)

        expected_data = {
            self.ad_group_source.ad_group: {
                self.ad_group_source: {
                    "conversions": 0.12,
                    "dividend": 3.0,
                    "divisor": 25.0,
                    "goal_optimal": Decimal("0.05"),
                    "goal_performance": 1,
                    "old_budget": 1000,
                    "old_bid": Decimal("0.15"),
                    "spend_perc": Decimal("0.025"),
                    "yesterdays_clicks": 13,
                    "yesterdays_spend_cc": Decimal("25"),
                },
                self.all_rtb_ad_group_source: {
                    "conversions": 0.12,
                    "dividend": 3.0,
                    "divisor": 25.0,
                    "goal_optimal": Decimal("0.05"),
                    "goal_performance": 1,
                    "old_budget": Decimal("50.00"),
                    "old_bid": Decimal("0.45"),
                    "spend_perc": Decimal("0.5"),
                    "yesterdays_clicks": 13,
                    "yesterdays_spend_cc": Decimal("25"),
                },
            }
        }
        expected_goals = {
            self.ad_group_source.ad_group.campaign: {
                "goal": self.goal_value.campaign_goal,
                "value": Decimal("1") / self.goal_value.value,
            }
        }
        expected_bcm = {
            self.ad_group_source.ad_group.campaign: {
                "service_fee": Decimal("0.1"),
                "fee": Decimal("0.2"),
                "margin": Decimal("0"),
            }
        }
        self.assertEqual(data, expected_data)
        self.assertEqual(campaign_goals, expected_goals)
        self.assertEqual(bcm_modifiers_map, expected_bcm)

    def test_other_goal_cpm(self):
        self.ad_group_source.ad_group.settings.update_unsafe(None, b1_sources_group_enabled=True)
        self.ad_group_source.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group_source.ad_group.save(None)
        data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(self.entities)

        expected_data = {
            self.ad_group_source.ad_group: {
                self.ad_group_source: {
                    "avg_tos": 16,
                    "dividend": 32.0,
                    "divisor": 2.0,
                    "goal_optimal": Decimal("20"),
                    "goal_performance": 0.8,
                    "old_budget": 1000,
                    "old_bid": Decimal("1.00"),
                    "spend_perc": Decimal("0.025"),
                    "yesterdays_clicks": 13,
                    "yesterdays_spend_cc": Decimal("25"),
                },
                self.all_rtb_ad_group_source: {
                    "avg_tos": 16.0,
                    "dividend": 32.0,
                    "divisor": 2.0,
                    "goal_optimal": Decimal("20"),
                    "goal_performance": 0.8,
                    "old_budget": Decimal("50.00"),
                    "old_bid": Decimal("1.00"),
                    "spend_perc": Decimal("0.5"),
                    "yesterdays_clicks": 13,
                    "yesterdays_spend_cc": Decimal("25"),
                },
            }
        }
        expected_goals = {
            self.ad_group_source.ad_group.campaign: {
                "goal": self.goal_value.campaign_goal,
                "value": self.goal_value.value,
            }
        }
        expected_bcm = {
            self.ad_group_source.ad_group.campaign: {
                "service_fee": Decimal("0.1"),
                "fee": Decimal("0.2"),
                "margin": Decimal("0"),
            }
        }
        self.assertEqual(data, expected_data)
        self.assertEqual(campaign_goals, expected_goals)
        self.assertEqual(bcm_modifiers_map, expected_bcm)

    def test_no_allrtb(self):
        self.ad_group_source.ad_group.settings.update_unsafe(None, b1_sources_group_enabled=False)
        data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(self.entities)
        self.assertNotIn(self.all_rtb_ad_group_source, data[self.ad_group_source.ad_group])

        self.ad_group_source.ad_group.settings.update_unsafe(
            None, b1_sources_group_enabled=True, b1_sources_group_state=constants.AdGroupSourceSettingsState.INACTIVE
        )
        data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(self.entities)
        self.assertNotIn(self.all_rtb_ad_group_source, data[self.ad_group_source.ad_group])

        self.ad_group_source.ad_group.settings.update_unsafe(
            None, b1_sources_group_enabled=True, b1_sources_group_state=constants.AdGroupSourceSettingsState.ACTIVE
        )
        data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(self.entities)
        self.assertIn(self.all_rtb_ad_group_source, data[self.ad_group_source.ad_group])

    def test_multiple_allrtb(self):
        ad_group_source2 = magic_mixer.blend(models.AdGroupSource, source=self.ad_group_source.source)
        ad_group_source2.settings.update_unsafe(None, daily_budget_cc=1000)
        entities = {
            self.ad_group_source.ad_group.campaign: {self.ad_group_source.ad_group: [self.ad_group_source]},
            ad_group_source2.ad_group.campaign: {ad_group_source2.ad_group: [ad_group_source2]},
        }
        all_rtb_ad_group_source2 = all_rtb.AllRTBAdGroupSource(ad_group_source2.ad_group)

        data, campaign_goals, bcm_modifiers_map = prefetch.prefetch_autopilot_data(entities)

        self.assertIn(self.all_rtb_ad_group_source, data[self.ad_group_source.ad_group])
        self.assertNotIn(all_rtb_ad_group_source2, data[self.ad_group_source.ad_group])
        self.assertNotIn(self.all_rtb_ad_group_source, data[ad_group_source2.ad_group])
        self.assertIn(all_rtb_ad_group_source2, data[ad_group_source2.ad_group])
