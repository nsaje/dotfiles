import dash.models
import dash.constants
import logging

logger = logging.getLogger(__name__)


def create_goals(campaign, data):
    campaign_goal_values = get_campaign_goal_values(campaign)
    ret = {}
    for row in data:
        for campaign_goal_value in campaign_goal_values:
            goal_type = campaign_goal_value.campaign_goal.type
            ret.extend(calculate_goal_values(row, goal_type))
    # TODO: CPA
    return ret


def create_goal_totals(campaign, data):
    ret = {}
    campaign_goal_values = get_campaign_goal_values(campaign)
    for campaign_goal_value in campaign_goal_values:
        goal_type = campaign_goal_value.campaign_goal.type
        ret.extend(calculate_goal_values(data, goal_type))
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


def calculate_goal_values(row, goal_type):
    ret = {}
    if goal_type == dash.constants.CampaignGoalKPI.TIME_ON_SITE:
        # total seconds
        ret['total_seconds'] = (row.get('avg_tos') or 0) *\
            (row.get('visits') or 0)
        # avg cost for second
        ret['avg_cost_per_second'] = row.get('avg_tos') or 0
    elif goal_type == dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE:
        # unbounced visitors
        ret['unbounced_visits'] = 1.0 - (row.get('bounce_rate') or 0)
        # avg. cost for unbounced visitor
        ret['avg_cost_per_non_bounced_visitor'] =\
            (row.get('bounce_rate') or 0)
    elif goal_type == dash.constants.CampaignGoalKPI.PAGES_PER_SESSION:
        # total pageviews
        ret['total_pageviews'] = (row.get('pv_per_visit') or 0) *\
            (row.get('visits') or 0)
        # avg. cost per pageview
        ret['avg_cost_per_pageview'] = (row.get('pv_per_visit') or 0)
    return ret
