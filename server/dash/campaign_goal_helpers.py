import dash.models
import dash.constants
import logging

logger = logging.getLogger(__name__)

CAMPAIGN_GOAL_MAP = {
    dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE: [
        'unbounced_visits',
        'avg_cost_per_non_bounced_visitor',
    ],
    dash.constants.CampaignGoalKPI.PAGES_PER_SESSION: [
        'total_pageviews',
        'avg_cost_per_pageview',
    ],
    dash.constants.CampaignGoalKPI.TIME_ON_SITE: [
        'total_seconds',
        'avg_cost_per_second',
    ],
    dash.constants.CampaignGoalKPI.CPA: [],
    dash.constants.CampaignGoalKPI.CPC: [],
    dash.constants.CampaignGoalKPI.CPM: [],
}


def create_goals(campaign, data, cost):
    campaign_goal_values = get_campaign_goal_values(campaign)
    ret = []
    for row in data:
        new_row = dict(row)
        for campaign_goal_value in campaign_goal_values:
            goal_type = campaign_goal_value.campaign_goal.type
            new_row.update(calculate_goal_values(row, goal_type, cost))
        ret.append(new_row)
    # TODO: CPA
    return ret


def create_goal_totals(campaign, data, cost):
    ret = dict(data)
    campaign_goal_values = get_campaign_goal_values(campaign)
    for campaign_goal_value in campaign_goal_values:
        goal_type = campaign_goal_value.campaign_goal.type
        ret.update(calculate_goal_total_values(data, goal_type, cost))
    # TODO: CPA
    return ret


def get_campaign_goal_values(campaign):
    return dash.models.CampaignGoalValue.objects.all().filter(
        campaign_goal__campaign=campaign
    ).order_by(
        'campaign_goal',
        '-created_dt'
    ).distinct('campaign_goal').select_related(
        'campaign_goal'
    )


def calculate_goal_values(row, goal_type, cost):
    ret = {}
    logger.warning(row)
    visits_cost = float(cost) /\
        (row.get('visits') or 0) if row.get('visits') else 0

    if goal_type == dash.constants.CampaignGoalKPI.TIME_ON_SITE:
        total_seconds = (row.get('avg_tos') or 0) *\
            (row.get('visits') or 0)
        ret['total_seconds'] = total_seconds
        ret['avg_cost_per_second'] = visits_cost / total_seconds if\
            total_seconds != 0 else 0
    elif goal_type == dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE:
        unbounced_visits = 1.0 - (row.get('bounce_rate') or 0)
        ret['unbounced_visits'] = unbounced_visits
        ret['avg_cost_per_non_bounced_visitor'] = visits_cost * unbounced_visits if\
            unbounced_visits != 0 else 0
    elif goal_type == dash.constants.CampaignGoalKPI.PAGES_PER_SESSION:
        total_pageviews = (row.get('pv_per_visit') or 0) *\
            (row.get('visits') or 0)
        ret['total_pageviews'] = total_pageviews
        # avg. cost per pageview
        ret['avg_cost_per_pageview'] = visits_cost / total_pageviews if\
            total_pageviews != 0 else 0
    return ret


def calculate_goal_total_values(row, goal_type, cost):
    ret = {}
    logger.warning(row)
    if goal_type == dash.constants.CampaignGoalKPI.TIME_ON_SITE:
        total_seconds = (row.get('avg_tos') or 0) *\
            (row.get('visits') or 0)
        ret['total_seconds'] = total_seconds
        ret['avg_cost_per_second'] = float(cost) / total_seconds if\
            total_seconds != 0 else 0
    elif goal_type == dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE:
        unbounced_visits = 1.0 - (row.get('bounce_rate') or 0)
        ret['unbounced_visits'] = unbounced_visits
        ret['avg_cost_per_non_bounced_visitor'] = float(cost) * unbounced_visits if\
            unbounced_visits != 0 else 0
    elif goal_type == dash.constants.CampaignGoalKPI.PAGES_PER_SESSION:
        total_pageviews = (row.get('pv_per_visit') or 0) *\
            (row.get('visits') or 0)
        ret['total_pageviews'] = total_pageviews
        # avg. cost per pageview
        ret['avg_cost_per_pageview'] = float(cost) / total_pageviews if\
            total_pageviews != 0 else 0
    return ret


def get_campaign_goals(campaign):
    cg_values = get_campaign_goal_values(campaign)
    ret = []
    for cg_value in cg_values:
        goal_type = cg_value.campaign_goal.type
        goal_name = dash.constants.CampaignGoalKPI.get_text(
            goal_type
        )
        ret.append({
            'name': goal_name,
            'value': float(cg_value.value),
            'fields': {k: True for k in CAMPAIGN_GOAL_MAP.get(goal_type, [])}
        })
    return ret
