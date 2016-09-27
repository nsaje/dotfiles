import collections

import dash.campaign_goals
from dash import constants

"""
Helper functions that transform breakdown responses into what frontend expects.
"""


def format_report_rows_state_fields(rows):
    for row in rows:
        if 'status' in row:
            row['status'] = {'value': row['status']}
        if 'state' in row:
            row['state'] = {'value': row['state']}


def format_report_rows_performance_fields(rows, goals):
    map_values = {x.campaign_goal_id: x for x in (goals.campaign_goal_values or [])}

    campaign_goals_by_campaign_id = collections.defaultdict(list)
    for campaign_goal in goals.campaign_goals:
        campaign_goals_by_campaign_id[campaign_goal.campaign_id].append(campaign_goal)

    conversion_goals_by_campaign_id = collections.defaultdict(list)
    for conversion_goal in goals.conversion_goals:
        conversion_goals_by_campaign_id[conversion_goal.campaign_id].append(conversion_goal)

    rows_by_campaign_id = collections.defaultdict(list)
    for row in rows:
        if row.get('campaign_id'):
            rows_by_campaign_id[row['campaign_id']].append(row)

    if len(campaign_goals_by_campaign_id.keys()) > 1 and len(rows_by_campaign_id.keys()) <= 1:
        # in case we have data for multiple campaigns but we couldn't separate rows by campaigns
        # then don't add performance info
        return

    for campaign_id, campaign_goals in campaign_goals_by_campaign_id.items():
        primary_goal = next((x for x in goals.primary_goals if x.campaign_id == campaign_id), None)
        primary_goal_key = 'performance_' + primary_goal.get_view_key() if primary_goal else None
        conversion_goals = conversion_goals_by_campaign_id[campaign_id]

        for row in rows_by_campaign_id[campaign_id] if rows_by_campaign_id else rows:

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
                for goal in campaign_goals:
                    performance = row.get('performance_' + goal.get_view_key())
                    metric = dash.campaign_goals.get_goal_performance_metric(goal, conversion_goals_by_campaign_id[campaign_id])
                    metric_value = row.get(metric)

                    goals_performances.append((
                        dash.campaign_goals.get_goal_performance_category(performance),
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


def format_report_rows_content_ad_editable_fields(rows):
    for row in rows:
        submission_states = []

        for _, source_status in row.get('status_per_source', {}).items():

            source_status_text = ''
            if ('source_status' in source_status and
               source_status['source_status'] != constants.AdGroupSourceSettingsState.ACTIVE):
                source_status_text = '(paused)'

            submission_status = source_status['submission_status']
            submission_errors = source_status['submission_errors']

            text = constants.ContentAdSubmissionStatus.get_text(submission_status)
            if (submission_status == constants.ContentAdSubmissionStatus.REJECTED and submission_errors is not None):
                text = '{} ({})'.format(text, submission_errors)

            submission_states.append({
                'name': source_status['source_name'],
                'status': source_status['submission_status'],
                'source_state': source_status_text,
                'text': text,
            })

        row.update({
            'id': row['content_ad_id'],
            'submission_status': submission_states,
            'editable_fields': {
                'state': {
                    'enabled': True,
                    'message': None,
                },
            }
        })


def set_row_goal_performance_meta(row, goals_performances, conversion_goals):
    for goal_status, goal_metric, goal_value, goal in goals_performances:
        performance_item = {
            'emoticon': dash.campaign_goals.STATUS_TO_EMOTICON_MAP[goal_status],
            'text': dash.campaign_goals.format_campaign_goal(
                goal.type,
                goal_metric,
                goal.conversion_goal
            )
        }

        if goal_value:
            performance_item['text'] += ' (planned {})'.format(
                dash.campaign_goals.format_value(goal.type, goal_value)
            )

        row['performance']['list'].append(performance_item)

        colored_column = dash.campaign_goals.CAMPAIGN_GOAL_PRIMARY_METRIC_MAP.get(goal.type)
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
    return dash.campaign_goals.STATUS_TO_EMOTICON_MAP[
        dash.campaign_goals.get_goal_performance_category(performance)
    ]


def clean_non_relevant_fields(rows):
    for row in rows:
        row.pop('campaign_stop_inactive', None)
        row.pop('campaign_has_available_budget', None)
        row.pop('status_per_source', None)

        for key in row.keys():
            if key.startswith('performance_'):
                row.pop(key, None)


def get_upload_batches_response_list(upload_batches):
    upload_batches = upload_batches.order_by('-created_dt')
    return list(upload_batches.values('id', 'name'))
