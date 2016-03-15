import dash.models
import dash.constants


def create_goals(campaign, data):
    campaign_goal_values = get_campaign_goal_values(campaign)
    ret = {}
    for campaign_goal_value in campaign_goal_values:
        goal_type = campaign_goal_value.campaign_goal.type
        if goal_type == dash.constants.CampaignGoalKPI.TIME_ON_SITE:
            # total seconds
            ret['total_seconds'] = 0
            # avg cost for second
            ret['avg_cost_per_second'] = 0
        elif goal_type == dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE:
            # unbounced visitors
            ret['unbounced_visits'] = 0
            # avg. cost for unbounced visitor
            ret['avg_cost_per_non_bounced_visitor'] = 0
        elif goal_type == dash.constants.CampaignGoalKPI.PAGES_PER_SESSION:
            # total pageviews
            ret['total_pageviews'] = 0
            # avg. cost per pageview
            ret['avg_cost_per_pageview'] = 0
    # TODO: CPA
    return ret


def create_goal_totals(campaign, data):
    ret = {}
    campaign_goal_values = get_campaign_goal_values(campaign)
    for campaign_goal_value in campaign_goal_values:
        goal_type = campaign_goal_value.campaign_goal.type
        if goal_type == dash.constants.CampaignGoalKPI.TIME_ON_SITE:
            # total seconds
            ret['total_seconds'] = 0
            # avg cost for second
            ret['avg_cost_per_second'] = 0
        elif goal_type == dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE:
            # unbounced visitors
            ret['unbounced_visits'] = 0
            # avg. cost for unbounced visitor
            ret['avg_cost_per_non_bounced_visitor'] = 0
        elif goal_type == dash.constants.CampaignGoalKPI.PAGES_PER_SESSION:
            # total pageviews
            ret['total_pageviews'] = 0
            # avg. cost per pageview
            ret['avg_cost_per_pageview'] = 0
    # TODO: CPA
    return ret


def get_campaign_goal_values(campaign):
    return dash.models.CampaignGoalValue.objects.all().filter(
        campaign_goal__campaign=campaign
    ).select_related(
        'campaign_goal'
    ).order_by(
        'campaign_goal',
        '-created_dt'
    ).distinct('campaign_goal').select_related(
        'campaign_goal'
    )
