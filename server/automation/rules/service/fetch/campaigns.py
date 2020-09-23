from typing import Sequence

from django.db.models import Prefetch

import core.features.goals
import core.models
import dash.constants


def prepare_cpa_goal_by_campaign_id(ad_groups: Sequence[core.models.AdGroup]):
    campaigns = core.models.Campaign.objects.filter(adgroup__in=ad_groups).prefetch_related(
        Prefetch(
            "campaigngoal_set",
            queryset=core.features.goals.CampaignGoal.objects.filter(type=dash.constants.CampaignGoalKPI.CPA)
            .order_by("-primary", "id")
            .select_related("conversion_goal__pixel"),
            to_attr="cpa_goals",
        )
    )
    cpa_goal_by_campaign_id = {
        campaign.id: campaign.cpa_goals[0] if campaign.cpa_goals else None for campaign in campaigns
    }
    return cpa_goal_by_campaign_id
