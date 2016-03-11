import dash.models


def create_goals(campaign, data):
    campaign_goals = get_campaign_goal_values(campaign)
    return {
        'total_seconds': 0,
        'unbounced_visits': 0,
        'total_pageviews': 0,
        'avg_cost_per_second': 0,
        'avg_cost_per_pageview': 0,
        'avg_cost_per_non_bounced_visitor': 0,
        'cpa': 0,
    }


def create_goal_totals(campaign, data):
    campaign_goals = get_campaign_goal_values(campaign)
    return {
        'total_seconds': 0,
        'unbounced_visits': 0,
        'total_pageviews': 0,
        'avg_cost_per_second': 0,
        'avg_cost_per_pageview': 0,
        'avg_cost_per_non_bounced_visitor': 0,
        'cpa': 0,
    }


def get_campaign_goal_values(campaign):
    return dash.models.CampaignGoalValue.objects.all().filter(
        campaign_goal__campaign=campaign
    ).select_related(
        'campaign_goal'
    ).order_by(
        '-created_dt'
    ).distinct('campaign_goal')
