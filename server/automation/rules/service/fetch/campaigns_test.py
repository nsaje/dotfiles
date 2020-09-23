import core.features.goals
import core.models
import dash.constants
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from . import campaigns


class CampaignGoalsTest(BaseTestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)
        self.other_campaign = magic_mixer.blend(core.models.Campaign)
        magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=self.other_campaign,
            primary=True,
            type=dash.constants.CampaignGoalKPI.CPA,
        )  # campaign not queried, goal not expected to be returned in any function

        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)

    def test_prepare_primary_cpa_goal(self):
        primary_goal = magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=self.campaign,
            primary=True,
            type=dash.constants.CampaignGoalKPI.CPA,
        )
        magic_mixer.blend(
            core.features.goals.CampaignGoal, campaign=self.campaign, type=dash.constants.CampaignGoalKPI.CPA
        )  # non primary goal not returned
        goals_prepared = campaigns.prepare_cpa_goal_by_campaign_id([self.ad_group])
        self.assertCountEqual({self.campaign.id: primary_goal}, goals_prepared)

    def test_prepare_non_primary_cpa_goal(self):
        magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=self.campaign,
            primary=True,
            type=dash.constants.CampaignGoalKPI.CPC,
        )  # primary goal not returned because it's not a cpa goal
        non_primary_goal = magic_mixer.blend(
            core.features.goals.CampaignGoal, campaign=self.campaign, type=dash.constants.CampaignGoalKPI.CPA
        )
        goals_prepared = campaigns.prepare_cpa_goal_by_campaign_id([self.ad_group])
        self.assertCountEqual({self.campaign.id: non_primary_goal}, goals_prepared)

    def test_prepare_no_cpa_goal(self):
        magic_mixer.blend(
            core.features.goals.CampaignGoal,
            campaign=self.campaign,
            primary=True,
            type=dash.constants.CampaignGoalKPI.CPC,
        )
        magic_mixer.blend(
            core.features.goals.CampaignGoal, campaign=self.campaign, type=dash.constants.CampaignGoalKPI.CPV
        )
        goals_prepared = campaigns.prepare_cpa_goal_by_campaign_id([self.ad_group])
        self.assertCountEqual({self.campaign.id: None}, goals_prepared)
