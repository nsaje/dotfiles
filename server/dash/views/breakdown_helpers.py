"""
Helper functions that transform breakdown responses into what frontend expects.
"""

from dash import campaign_goals
from dash import constants


def format_report_rows_state_fields(rows):
    for row in rows:
        if 'status' in row:
            row['status'] = {'value': row['status']}
        if 'state' in row:
            row['state'] = {'value': row['state']}


def format_report_rows_performance_fields(rows, goals):
    primary_goal_key = 'performance_' + goals.primary_goal.get_view_key() if goals.primary_goal else None
    map_values = {x.campaign_goal_id: x for x in (goals.campaign_goal_values or [])}

    for row in rows:

        # user rights for performance were already checked in the stats module
        # here just add additional formatting if keys are present
        if any(x for x in row.keys() if x.startswith('performance_')):
            row.update({
                'performance': {
                    'overall': None,
                    'list': [],
                },
                'styles': {},
            })

            if primary_goal_key and primary_goal_key in row:
                row['performance']['overall'] = _get_campaign_goal_emoticon(row[primary_goal_key])

            goals_performances = []
            for goal in goals.campaign_goals:
                performance = row.get('performance_' + goal.get_view_key())
                metric = campaign_goals.get_goal_performance_metric(goal, goals.conversion_goals)
                metric_value = row.get(metric)

                goals_performances.append((
                    campaign_goals.get_goal_performance_category(performance),
                    metric_value,
                    map_values.get(goal.id) and map_values[goal.id].value,
                    goal
                ))

            set_row_goal_performance_meta(row, goals_performances, goals.conversion_goals)


def format_report_rows_ad_group_editable_fields(rows):
    for row in rows:
        row['editable_fields'] = get_ad_group_editable_fields(
            row, row['campaign_stop_inactive'], row['campaign_has_available_budget']
        )


def set_row_goal_performance_meta(row, goals_performances, conversion_goals):
    for goal_status, goal_metric, goal_value, goal in goals_performances:
        performance_item = {
            'emoticon': campaign_goals.STATUS_TO_EMOTICON_MAP[goal_status],
            'text': campaign_goals.format_campaign_goal(
                goal.type,
                goal_metric,
                goal.conversion_goal
            )
        }

        if goal_value:
            performance_item['text'] += ' (planned {})'.format(
                campaign_goals.format_value(goal.type, goal_value)
            )

        row['performance']['list'].append(performance_item)

        colored_column = campaign_goals.CAMPAIGN_GOAL_PRIMARY_METRIC_MAP.get(goal.type)
        if goal.type == constants.CampaignGoalKPI.CPA:
            colored_column = 'avg_cost_per_' + goal.conversion_goal.get_view_key(conversion_goals)
        if not colored_column:
            continue

        if goal_status == constants.CampaignGoalPerformance.SUPERPERFORMING:
            row['styles'][colored_column] = constants.Emoticon.HAPPY
        elif goal_status == constants.CampaignGoalPerformance.UNDERPERFORMING:
            row['styles'][colored_column] = constants.Emoticon.SAD


def get_ad_group_editable_fields(row, can_enable_ad_group, has_available_budget):
    state = {
        'enabled': True,
        'message': None
    }
    if not can_enable_ad_group:
        state['enabled'] = False
        state['message'] = 'Please add additional budget to your campaign to make changes.'
    elif row['state'] == constants.AdGroupSettingsState.INACTIVE \
            and not has_available_budget:
        state['enabled'] = False
        state['message'] = 'Cannot enable ad group without available budget.'

    return {'state': state}


def _get_campaign_goal_emoticon(performance):
    return campaign_goals.STATUS_TO_EMOTICON_MAP[
        campaign_goals.get_goal_performance_category(performance)
    ]


def clean_non_relevant_fields(rows):
    for row in rows:
        row.pop('campaign_stop_inactive', None)
        row.pop('campaign_has_available_budget', None)

        for key in row.keys():
            if key.startswith('performance_'):
                row.pop(key, None)
