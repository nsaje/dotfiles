import datetime
from decimal import Decimal, ROUND_DOWN
from functools import partial

from django.db import transaction
from django.db.models import Prefetch

from dash import models, constants
import dash.history_helpers

import stats.api_breakdowns
import stats.constraints_helper

from utils import exc
import utils.lc_helper


CAMPAIGN_GOAL_NAME_FORMAT = {
    constants.CampaignGoalKPI.TIME_ON_SITE: '{} Time on Site - Seconds',
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: '{} Max Bounce Rate',
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: '{} New Users',
    constants.CampaignGoalKPI.PAGES_PER_SESSION: '{} Pageviews per Visit',
    constants.CampaignGoalKPI.CPA: '{} CPA',
    constants.CampaignGoalKPI.CPC: '{} CPC',
    constants.CampaignGoalKPI.CPV: '{} Cost Per Visit',
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: '{} Cost Per Non-Bounced Visit',
    constants.CampaignGoalKPI.CP_NEW_VISITOR: '{} Cost Per New Visitor',
    constants.CampaignGoalKPI.CP_PAGE_VIEW: '{} Cost Per Pageview',
    constants.CampaignGoalKPI.CPCV: '{} Cost Per Completed Video View',
}

NR_DECIMALS = {
    constants.CampaignGoalKPI.TIME_ON_SITE: 2,
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: 2,
    constants.CampaignGoalKPI.PAGES_PER_SESSION: 2,
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: 2,
    constants.CampaignGoalKPI.CPA: 2,
    constants.CampaignGoalKPI.CPC: 3,
    constants.CampaignGoalKPI.CPV: 2,
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: 2,
    constants.CampaignGoalKPI.CP_NEW_VISITOR: 2,
    constants.CampaignGoalKPI.CP_PAGE_VIEW: 2,
    constants.CampaignGoalKPI.CPCV: 2,
}

CAMPAIGN_GOAL_VALUE_FORMAT = {
    constants.CampaignGoalKPI.TIME_ON_SITE:
    lambda x: ('{:.' + str(NR_DECIMALS[constants.CampaignGoalKPI.TIME_ON_SITE]) + 'f}').format(x),

    constants.CampaignGoalKPI.MAX_BOUNCE_RATE:
    lambda x: ('{:.' + str(NR_DECIMALS[constants.CampaignGoalKPI.MAX_BOUNCE_RATE]) + 'f}').format(x),

    constants.CampaignGoalKPI.PAGES_PER_SESSION:
    lambda x: ('{:.' + str(NR_DECIMALS[constants.CampaignGoalKPI.PAGES_PER_SESSION]) + 'f}').format(x),

    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS:
    lambda x: ('{:.' + str(NR_DECIMALS[constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS]) + 'f}').format(x),

    constants.CampaignGoalKPI.CPA:
    partial(utils.lc_helper.default_currency, places=NR_DECIMALS[constants.CampaignGoalKPI.CPA]),

    constants.CampaignGoalKPI.CPC:
    partial(utils.lc_helper.default_currency, places=NR_DECIMALS[constants.CampaignGoalKPI.CPC]),

    constants.CampaignGoalKPI.CPV:
    partial(utils.lc_helper.default_currency, places=NR_DECIMALS[constants.CampaignGoalKPI.CPV]),

    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT:
    partial(utils.lc_helper.default_currency, places=NR_DECIMALS[constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT]),

    constants.CampaignGoalKPI.CP_NEW_VISITOR:
    partial(utils.lc_helper.default_currency, places=NR_DECIMALS[constants.CampaignGoalKPI.CP_NEW_VISITOR]),

    constants.CampaignGoalKPI.CP_PAGE_VIEW:
    partial(utils.lc_helper.default_currency, places=NR_DECIMALS[constants.CampaignGoalKPI.CP_PAGE_VIEW]),

    constants.CampaignGoalKPI.CPCV:
    partial(utils.lc_helper.default_currency, places=NR_DECIMALS[constants.CampaignGoalKPI.CPCV]),

}


_RELEVANT_GOAL_FIELDS_MAP = {
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: ['non_bounced_visits', 'avg_cost_per_non_bounced_visit'],
    constants.CampaignGoalKPI.PAGES_PER_SESSION: ['total_pageviews', 'avg_cost_per_pageview'],
    constants.CampaignGoalKPI.TIME_ON_SITE: ['total_seconds', 'avg_cost_per_minute'],
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: ['avg_cost_for_new_visitor'],
    constants.CampaignGoalKPI.CPA: [],
    constants.CampaignGoalKPI.CPC: ['cpc'],
    constants.CampaignGoalKPI.CPV: ['avg_cost_per_visit'],
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: ['avg_cost_per_non_bounced_visit', 'non_bounced_visits'],
    constants.CampaignGoalKPI.CP_NEW_VISITOR: ['avg_cost_for_new_visitor'],
    constants.CampaignGoalKPI.CP_PAGE_VIEW: ['avg_cost_per_pageview'],
    constants.CampaignGoalKPI.CPCV: ['video_cpcv'],
}


_RELEVANT_GOAL_ETFM_FIELDS_MAP = {
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: ['non_bounced_visits', 'avg_etfm_cost_per_non_bounced_visit'],
    constants.CampaignGoalKPI.PAGES_PER_SESSION: ['total_pageviews', 'avg_etfm_cost_per_pageview'],
    constants.CampaignGoalKPI.TIME_ON_SITE: ['total_seconds', 'avg_etfm_cost_per_minute'],
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: ['avg_etfm_cost_for_new_visitor'],
    constants.CampaignGoalKPI.CPA: [],
    constants.CampaignGoalKPI.CPC: ['etfm_cpc'],
    constants.CampaignGoalKPI.CPV: ['avg_etfm_cost_per_visit'],
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: ['avg_etfm_cost_per_non_bounced_visit', 'non_bounced_visits'],
    constants.CampaignGoalKPI.CP_NEW_VISITOR: ['avg_etfm_cost_for_new_visitor'],
    constants.CampaignGoalKPI.CP_PAGE_VIEW: ['avg_etfm_cost_per_pageview'],
    constants.CampaignGoalKPI.CPCV: ['video_etfm_cpcv'],
}


def get_relevant_goal_fields_map(uses_bcm_v2):
    if uses_bcm_v2:
        return _RELEVANT_GOAL_ETFM_FIELDS_MAP
    return _RELEVANT_GOAL_FIELDS_MAP


_CAMPAIGN_GOAL_PRIMARY_METRIC = {
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: 'bounce_rate',
    constants.CampaignGoalKPI.PAGES_PER_SESSION: 'pv_per_visit',
    constants.CampaignGoalKPI.TIME_ON_SITE: 'avg_tos',
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: 'percent_new_users',
    constants.CampaignGoalKPI.CPC: 'cpc',
    constants.CampaignGoalKPI.CPV: 'avg_cost_per_visit',
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: 'avg_cost_per_non_bounced_visit',
    constants.CampaignGoalKPI.CP_NEW_VISITOR: 'avg_cost_for_new_visitor',
    constants.CampaignGoalKPI.CP_PAGE_VIEW: 'avg_cost_per_pageview',
    constants.CampaignGoalKPI.CPCV: 'video_cpcv',
}


_CAMPAIGN_GOAL_PRIMARY_ETFM_METRIC = {
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: 'bounce_rate',
    constants.CampaignGoalKPI.PAGES_PER_SESSION: 'pv_per_visit',
    constants.CampaignGoalKPI.TIME_ON_SITE: 'avg_tos',
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: 'percent_new_users',
    constants.CampaignGoalKPI.CPC: 'etfm_cpc',
    constants.CampaignGoalKPI.CPV: 'avg_etfm_cost_per_visit',
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: 'avg_etfm_cost_per_non_bounced_visit',
    constants.CampaignGoalKPI.CP_NEW_VISITOR: 'avg_etfm_cost_for_new_visitor',
    constants.CampaignGoalKPI.CP_PAGE_VIEW: 'avg_etfm_cost_per_pageview',
    constants.CampaignGoalKPI.CPCV: 'video_etfm_cpcv',
}


def get_goal_to_primary_metric_map(uses_bcm_v2):
    if uses_bcm_v2:
        return _CAMPAIGN_GOAL_PRIMARY_ETFM_METRIC
    return _CAMPAIGN_GOAL_PRIMARY_METRIC


INVERSE_PERFORMANCE_CAMPAIGN_GOALS = (
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE,
    constants.CampaignGoalKPI.CPA,
    constants.CampaignGoalKPI.CPC,
    constants.CampaignGoalKPI.CPV,
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
    constants.CampaignGoalKPI.CP_NEW_VISITOR,
    constants.CampaignGoalKPI.CP_PAGE_VIEW,
    constants.CampaignGoalKPI.CPCV,
)

STATUS_TO_EMOTICON_MAP = {
    constants.CampaignGoalPerformance.SUPERPERFORMING: constants.Emoticon.HAPPY,
    constants.CampaignGoalPerformance.UNDERPERFORMING: constants.Emoticon.SAD,
    constants.CampaignGoalPerformance.AVERAGE: constants.Emoticon.NEUTRAL,
}

EXISTING_COLUMNS_FOR_GOALS = ('cpc', )

COST_DEPENDANT_GOALS = (
    constants.CampaignGoalKPI.CPA,
    constants.CampaignGoalKPI.CPC,
    constants.CampaignGoalKPI.CPV,
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
    constants.CampaignGoalKPI.CP_NEW_VISITOR,
    constants.CampaignGoalKPI.CP_PAGE_VIEW,
    constants.CampaignGoalKPI.CPCV,
)

ROUNDING = ROUND_DOWN


def _get_performance_value(goal_type, metric_value, target_value):
    if goal_type in INVERSE_PERFORMANCE_CAMPAIGN_GOALS:
        performance = (2 * target_value - metric_value) / target_value
    else:
        performance = metric_value / target_value
    return max(Decimal('0'), min(performance, Decimal('2')))


def format_value(goal_type, value):
    return value and CAMPAIGN_GOAL_VALUE_FORMAT[goal_type](value) \
        or 'N/A'


def format_campaign_goal(goal_type, value, conversion_goal):
    description = CAMPAIGN_GOAL_NAME_FORMAT[goal_type].format(
        format_value(goal_type, value)
    )
    if conversion_goal is not None:
        description += ' - ' + conversion_goal.name
    return description


def delete_campaign_goal(request, goal_id, campaign):
    goal = models.CampaignGoal.objects.all().select_related('campaign').get(pk=goal_id)

    if goal.conversion_goal:
        delete_conversion_goal(request, goal.conversion_goal.pk, goal.campaign)
        return

    models.CampaignGoalValue.objects.filter(campaign_goal_id=goal_id).delete()
    goal.delete()

    _add_entry_to_history(
        request,
        campaign,
        constants.HistoryActionType.GOAL_CHANGE,
        'Deleted campaign goal "{}"'.format(
            constants.CampaignGoalKPI.get_text(goal.type)
        )
    )


def get_primary_campaign_goal(campaign):
    try:
        return models.CampaignGoal.objects.select_related('conversion_goal').get(
            campaign=campaign,
            primary=True
        )
    except models.CampaignGoal.DoesNotExist:
        return None


def get_primary_goals(campaigns):
    return {
        goal.campaign_id: goal for goal in
        models.CampaignGoal.objects.filter(campaign__in=campaigns, primary=True).select_related(
            'conversion_goal'
        )
    }


def delete_conversion_goal(request, conversion_goal_id, campaign):
    try:
        conversion_goal = models.ConversionGoal.objects.get(
            id=conversion_goal_id, campaign_id=campaign.id
        )
    except models.ConversionGoal.DoesNotExist:
        raise exc.MissingDataError(message='Invalid conversion goal')

    with transaction.atomic():
        models.CampaignGoalValue.objects.filter(campaign_goal__conversion_goal=conversion_goal).delete()
        models.CampaignGoal.objects.filter(conversion_goal=conversion_goal).delete()
        conversion_goal.delete()

        _add_entry_to_history(
            request,
            campaign,
            constants.HistoryActionType.GOAL_CHANGE,
            'Deleted conversion goal "{}"'.format(
                conversion_goal.name,
                constants.ConversionGoalType.get_text(conversion_goal.type)
            )
        )


def get_campaign_goal_values(campaign):
    return get_campaigns_goal_values([campaign])


def get_campaigns_goal_values(campaigns):
    return models.CampaignGoalValue.objects.all().filter(
        campaign_goal__campaign__in=campaigns
    ).order_by(
        'campaign_goal',
        '-created_dt'
    ).distinct('campaign_goal').select_related(
        'campaign_goal',
        'campaign_goal__conversion_goal'
    )


def get_campaign_goals(campaign, conversion_goals):
    cg_values = get_campaign_goal_values(campaign)
    ret = []
    for cg_value in cg_values:
        goal_type = cg_value.campaign_goal.type
        goal_name = constants.CampaignGoalKPI.get_text(goal_type)

        # This gets overwritten if KPI is CPA
        fields = {k: True for k in get_relevant_goal_fields_map(campaign.account.uses_bcm_v2).get(goal_type, [])}

        conversion_goal_name = None
        if goal_type == constants.CampaignGoalKPI.CPA:
            goal_name = 'Avg. CPA'
            conversion_goal_name = cg_value.campaign_goal.conversion_goal.name
            fields = dict(('{}'.format(k['id']), True)
                          for k in conversion_goals if k['name'] == conversion_goal_name)

            if campaign.account.uses_bcm_v2:
                fields.update(
                    dict(('avg_etfm_cost_per_{}'.format(k['id']), True)
                         for k in conversion_goals if k['name'] == conversion_goal_name))
            else:
                fields.update(
                    dict(('avg_cost_per_{}'.format(k['id']), True)
                         for k in conversion_goals if k['name'] == conversion_goal_name))

        # TODO (jurebajt): Should local_values be returned here?
        ret.append({
            'name': goal_name,
            'primary': cg_value.campaign_goal.primary,
            'conversion': conversion_goal_name,
            'value': float(cg_value.value),
            'fields': fields,
        })

    return ret


def _add_entry_to_history(request, campaign, history_action_type, changes_text):
    campaign.write_history(
        changes_text,
        user=request.user,
        action_type=history_action_type
    )


def get_goal_performance_category(performance):
    if performance is None:
        return constants.CampaignGoalPerformance.AVERAGE

    if performance < Decimal('0.8'):
        return constants.CampaignGoalPerformance.UNDERPERFORMING
    if performance >= Decimal('1.0'):
        return constants.CampaignGoalPerformance.SUPERPERFORMING
    return constants.CampaignGoalPerformance.AVERAGE


def _round_by_goal_type(goal_type, value):
    zeros = '0' * (NR_DECIMALS[goal_type] - 1)
    return Decimal(value).quantize(Decimal('.{}1'.format(zeros)), rounding=ROUNDING)


def get_goal_performance_status(goal_type, metric_value, planned_value, cost=None):
    rounded_cost = (cost and Decimal(cost) or Decimal('0')).quantize(
        Decimal('.01'), rounding=ROUNDING
    )

    if goal_type in COST_DEPENDANT_GOALS and rounded_cost and not metric_value:
        return get_goal_performance_category(0)
    if planned_value is None or metric_value is None:
        return get_goal_performance_category(None)

    rounded_metric_value = _round_by_goal_type(goal_type, metric_value)
    performance = _get_performance_value(goal_type, rounded_metric_value, planned_value)

    return get_goal_performance_category(performance)


def fetch_goals(campaign_ids, end_date):
    prefetch_values = Prefetch(
        'values',
        queryset=dash.models.CampaignGoalValue.objects.filter(
            created_dt__lt=datetime.datetime.combine(end_date + datetime.timedelta(1),
                                                     datetime.datetime.min.time()),
        ).order_by('-created_dt')
    )
    return dash.models.CampaignGoal.objects.filter(campaign_id__in=campaign_ids).prefetch_related(
        prefetch_values
    ).select_related('conversion_goal').order_by('campaign_id', '-primary', 'created_dt')


def _prepare_performance_output(campaign_goal, stats, conversion_goals, uses_bcm_v2):
    goal_values = campaign_goal.values.all().order_by('-created_dt')
    last_goal_value = goal_values and goal_values[0]
    planned_value = last_goal_value and last_goal_value.value or None

    cost = stats.get('etfm_cost') if uses_bcm_v2 else stats.get('e_media_cost')
    primary_metric_map = get_goal_to_primary_metric_map(uses_bcm_v2)

    if campaign_goal.type == constants.CampaignGoalKPI.CPA:
        conversion_column = campaign_goal.conversion_goal.get_view_key(conversion_goals)
        metric = stats.get(conversion_column, 0)
        metric_value = (float(cost) / metric) if (metric and cost is not None) else None
    else:
        metric_value = stats.get(primary_metric_map[campaign_goal.type])
    return (
        get_goal_performance_status(campaign_goal.type, metric_value, planned_value, cost=cost),
        metric_value,
        planned_value,
        campaign_goal,
    )


def get_goal_performance_metric(campaign_goal, conversion_goals, uses_bcm_v2):
    if campaign_goal.type == constants.CampaignGoalKPI.CPA:
        conversion_column = campaign_goal.conversion_goal.get_view_key(conversion_goals)
        if uses_bcm_v2:
            return 'avg_etfm_cost_per_' + conversion_column
        else:
            return 'avg_cost_per_' + conversion_column

    primary_metric_map = get_goal_to_primary_metric_map(uses_bcm_v2)
    return primary_metric_map[campaign_goal.type]


def get_goals_performance_campaign(user, campaign, start_date, end_date):
    stats_constraints = stats.constraints_helper.prepare_campaign_constraints(
        user, campaign, [], start_date, end_date,
        models.Source.objects.all())
    stats_goals = stats.api_breakdowns.get_goals(stats_constraints, [])
    query_results = stats.api_breakdowns.totals(
        user, constants.Level.CAMPAIGNS, [], stats_constraints, stats_goals)

    return _get_goals_performance_output(stats_goals, query_results, campaign.account.uses_bcm_v2)


def get_goals_performance_ad_group(user, ad_group, start_date, end_date):
    stats_constraints = stats.constraints_helper.prepare_ad_group_constraints(
        user, ad_group, [], start_date, end_date,
        models.Source.objects.all())
    stats_goals = stats.api_breakdowns.get_goals(stats_constraints, [])
    query_results = stats.api_breakdowns.totals(
        user, constants.Level.AD_GROUPS, [], stats_constraints, stats_goals)

    return _get_goals_performance_output(stats_goals, query_results, ad_group.campaign.account.uses_bcm_v2)


def _get_goals_performance_output(stats_goals, query_results, uses_bcm_v2):
    performance = []
    for campaign_goal in stats_goals.campaign_goals:
        performance.append(_prepare_performance_output(
            campaign_goal,
            query_results,
            stats_goals.conversion_goals,
            uses_bcm_v2=uses_bcm_v2
        ))

    return performance


def get_campaign_goal_metrics(campaign, start_date, end_date, local_values=False):
    campaign_goal_values = models.CampaignGoalValue.objects.all().\
        filter(
            campaign_goal__campaign=campaign,
            campaign_goal__conversion_goal__isnull=True,
            created_dt__gte=start_date,
            created_dt__lte=end_date,
    ).order_by(
            'campaign_goal__campaign',
            'created_dt',
    ).select_related('campaign_goal')

    pre_cg_vals = get_pre_campaign_goal_values(
        campaign,
        start_date,
        conversion_goals=False
    )
    return generate_series(
        eliminate_duplicates(campaign_goal_values),
        pre_cg_vals,
        start_date,
        end_date,
        uses_bcm_v2=campaign.account.uses_bcm_v2,
        local_values=local_values,
        conversion_goals=None)


def get_campaign_conversion_goal_metrics(campaign, start_date, end_date, conversion_goals):
    campaign_goal_values = models.CampaignGoalValue.objects.all().\
        filter(
            campaign_goal__campaign=campaign,
            campaign_goal__conversion_goal__isnull=False,
            created_dt__gte=start_date,
            created_dt__lte=end_date,
    ).order_by(
            'campaign_goal__campaign',
            'created_dt',
    ).select_related('campaign_goal')

    pre_cg_vals = get_pre_campaign_goal_values(
        campaign,
        start_date,
        conversion_goals=True
    )

    return generate_series(
        eliminate_duplicates(campaign_goal_values),
        pre_cg_vals,
        start_date,
        end_date,
        uses_bcm_v2=campaign.account.uses_bcm_v2,
        conversion_goals=conversion_goals)


def eliminate_duplicates(campaign_goal_values):
    date_hash = {}
    for campaign_goal_value in campaign_goal_values:
        cgv_type = campaign_goal_value.campaign_goal.type
        date_hash[cgv_type] = date_hash.get(cgv_type, {})
        date_hash[cgv_type][campaign_goal_value.created_dt.date()] = campaign_goal_value

    ret = []
    for campaign_goal_type, date_values in date_hash.items():
        if len(date_values) == 0:
            continue
        sorted_values = sorted(list(date_values.values()), key=lambda x: x.created_dt)
        ret.extend(sorted_values)
    return sorted(ret, key=lambda x: x.created_dt)


def generate_series(campaign_goal_values, pre_cg_vals, start_date, end_date, uses_bcm_v2, local_values=False,
                    conversion_goals=None):
    last_cg_vals = {}
    cg_series = {}
    for cg_value in campaign_goal_values:
        cg = cg_value.campaign_goal
        name = goal_name(cg, conversion_goals, uses_bcm_v2=uses_bcm_v2)
        last_cg_vals[name] = cg_value

        if not cg_series.get(name):
            cg_series[name] = []
        cg_series[name].append(campaign_goal_dp(cg_value, local_values=local_values))

    # if starting campaign goal was defined before current range
    # or if no values are defined within current range(but exist before)
    # make sure to insert campaign goal value datapoints
    for pre_cg_id, pre_cg_val in pre_cg_vals.items():
        pre_cg = pre_cg_val.campaign_goal
        pre_name = goal_name(pre_cg, conversion_goals, uses_bcm_v2=uses_bcm_v2)
        dp_to_preinsert = campaign_goal_dp(pre_cg_val, override_date=start_date, local_values=local_values)
        if pre_name not in cg_series:
            # in the case that the goal was set in distant past and never
            # updated create two points in current date range
            dp_to_postinsert = campaign_goal_dp(pre_cg_val, override_date=end_date, local_values=local_values)
            cg_series[pre_name] = [dp_to_preinsert, dp_to_postinsert]
        else:
            first = cg_series[pre_name][0]
            if first[0] > pre_cg_val.created_dt.date():
                cg_series[pre_name] = [dp_to_preinsert] +\
                    cg_series[pre_name]

    for name, last_cg_val in last_cg_vals.items():
        if last_cg_val.created_dt.date() >= end_date:
            continue
        # duplicate last data point with date set to end date
        cg_series[name].append(
            campaign_goal_dp(last_cg_val, override_date=end_date, local_values=local_values),
        )
    return generate_missing(create_line_series(cg_series))


def goal_name(goal, conversion_goals=None, uses_bcm_v2=False):
    if goal.conversion_goal is None:
        return constants.CampaignGoalKPI.get_text(goal.type)
    if uses_bcm_v2:
        return 'avg_etfm_cost_per_{}'.format(goal.conversion_goal.get_view_key(conversion_goals))

    return 'avg_cost_per_{}'.format(goal.conversion_goal.get_view_key(conversion_goals))


def create_line_series(cg_series):
    '''
    For a nice display we need a sequence of series where each serie are just
    duplicate points. This results in a sequence of horizontal lines
    '''
    new_series = {}
    for name, dps in cg_series.items():
        new_series[name] = []
        previous_dp = None
        value_differs = False
        for index, dp in enumerate(dps):
            if index > 0:
                current_dp = (dp[0], previous_dp[1])
                new_series[name].append([previous_dp, current_dp])
                value_differs = previous_dp[1] != dp[1]
            previous_dp = dp

        if value_differs:
            date = dps[-1][0]
            new_series[name].append([(date, dps[-1][1]), dps[-1]])
    return new_series


def generate_missing(cg_series):
    day_delta = datetime.timedelta(days=1)

    new_series = {}
    for name, line_list in cg_series.items():
        new_series[name] = []
        for point_pair in line_list:
            horizontal_series = []
            horizontal_series.append(point_pair[0])
            date = point_pair[0][0] + day_delta
            while date < point_pair[1][0]:
                horizontal_series.append((date, point_pair[0][1]))
                date += day_delta
            horizontal_series.append(point_pair[1])
            new_series[name].append(horizontal_series)
    return new_series


def get_pre_campaign_goal_values(campaign, date, conversion_goals=False):
    '''
    For each campaign goal get first value before given date.
    Returns a dict mapping from campaign goal id to campaign goal value.
    '''
    campaign_goal_values = models.CampaignGoalValue.objects.all().\
        filter(
            campaign_goal__campaign=campaign,
            created_dt__lt=date,
            campaign_goal__conversion_goal__isnull=not conversion_goals,
    ).order_by(
            'campaign_goal',
            '-created_dt',
    ).distinct(
            'campaign_goal',
    ).select_related('campaign_goal')
    return {
        cgv.campaign_goal.id: cgv for cgv in campaign_goal_values
    }


def campaign_goal_dp(campaign_goal_value, override_date=None, override_value=None, local_values=False):
    date = campaign_goal_value.created_dt.date()
    if override_date is not None:
        date = override_date
    if local_values:
        value = float(campaign_goal_value.local_value)
    else:
        value = float(campaign_goal_value.value)
    if override_value is not None:
        value = override_value
    return (date, value,)


def inverted_campaign_goal_map(conversion_goals, uses_bcm_v2):
    # map from particular fields to goals
    ret = {}

    primary_metric_map = get_goal_to_primary_metric_map(uses_bcm_v2)

    for goal_type in list(primary_metric_map.keys()):
        field = primary_metric_map[goal_type]
        ret[field] = {
            'id': constants.CampaignGoalKPI.get_text(goal_type),
            'name': constants.CampaignGoalKPI.get_text(goal_type),
        }

    cpa_text = constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.CPA)
    for cg in conversion_goals:
        vk = cg.get_view_key(conversion_goals)

        if uses_bcm_v2:
            field = 'avg_etfm_cost_per_{}'.format(vk)
            ret[field] = {
                'id': field,
                'name': '{prefix} - {conversion_goal_name}'.format(
                    prefix=cpa_text,
                    conversion_goal_name=cg.name),
            }
        else:
            field = 'avg_cost_per_{}'.format(vk)
            ret[field] = {
                'id': field,
                'name': '{prefix} - {conversion_goal_name}'.format(
                    prefix=cpa_text,
                    conversion_goal_name=cg.name),
            }
    return ret
