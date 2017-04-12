import datetime
from decimal import Decimal, ROUND_DOWN

from django.db import transaction
from django.db.models import Prefetch

from dash import models, constants, forms
import dash.history_helpers

import stats.api_breakdowns
import stats.constraints_helper

from utils import exc
import utils.lc_helper


CAMPAIGN_GOAL_NAME_FORMAT = {
    constants.CampaignGoalKPI.TIME_ON_SITE: '{} Time on Site - Seconds',
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: '{} Max Bounce Rate',
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: '{} New Unique Visitors',
    constants.CampaignGoalKPI.PAGES_PER_SESSION: '{} Pageviews per Visit',
    constants.CampaignGoalKPI.CPA: '{} CPA',
    constants.CampaignGoalKPI.CPC: '{} CPC',
    constants.CampaignGoalKPI.CPV: '{} Cost Per Visit',
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: '{} Cost Per Non-Bounced Visit',
}

CAMPAIGN_GOAL_VALUE_FORMAT = {
    constants.CampaignGoalKPI.TIME_ON_SITE: lambda x: '{:.2f}'.format(x),
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: lambda x: '{:.2f} %'.format(x),
    constants.CampaignGoalKPI.PAGES_PER_SESSION: lambda x: '{:.2f}'.format(x),
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: lambda x: '{:.2f} %'.format(x),
    constants.CampaignGoalKPI.CPA: utils.lc_helper.default_currency,
    constants.CampaignGoalKPI.CPC: lambda x: utils.lc_helper.default_currency(x, places=3),
    constants.CampaignGoalKPI.CPV: utils.lc_helper.default_currency,
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: utils.lc_helper.default_currency,
}

CAMPAIGN_GOAL_MAP = {
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: [
        'non_bounced_visits',
        'avg_cost_per_non_bounced_visit',
    ],
    constants.CampaignGoalKPI.PAGES_PER_SESSION: [
        'total_pageviews',
        'avg_cost_per_pageview',
    ],
    constants.CampaignGoalKPI.TIME_ON_SITE: [
        'total_seconds',
        'avg_cost_per_minute',
    ],
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: [
        'avg_cost_for_new_visitor',
    ],
    constants.CampaignGoalKPI.CPA: [],
    constants.CampaignGoalKPI.CPC: ['cpc'],
    constants.CampaignGoalKPI.CPV: ['avg_cost_per_visit'],
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: [
        'avg_cost_per_non_bounced_visit',
        'non_bounced_visits',
    ],
}

CAMPAIGN_GOAL_PRIMARY_METRIC_MAP = {
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: 'bounce_rate',
    constants.CampaignGoalKPI.PAGES_PER_SESSION: 'pv_per_visit',
    constants.CampaignGoalKPI.TIME_ON_SITE: 'avg_tos',
    constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS: 'percent_new_users',
    constants.CampaignGoalKPI.CPC: 'cpc',
    constants.CampaignGoalKPI.CPV: 'avg_cost_per_visit',
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT: 'avg_cost_per_non_bounced_visit',
}

INVERSE_PERFORMANCE_CAMPAIGN_GOALS = (
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE,
    constants.CampaignGoalKPI.CPA,
    constants.CampaignGoalKPI.CPC,
    constants.CampaignGoalKPI.CPV,
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
)

STATUS_TO_EMOTICON_MAP = {
    constants.CampaignGoalPerformance.SUPERPERFORMING: constants.Emoticon.HAPPY,
    constants.CampaignGoalPerformance.UNDERPERFORMING: constants.Emoticon.SAD,
    constants.CampaignGoalPerformance.AVERAGE: constants.Emoticon.NEUTRAL,
}

EXISTING_COLUMNS_FOR_GOALS = ('cpc', )

E_MEDIA_COST_COLUMN = 'e_media_cost'

COST_DEPENDANT_GOALS = (
    constants.CampaignGoalKPI.CPA,
    constants.CampaignGoalKPI.CPC,
    constants.CampaignGoalKPI.CPV,
    constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
)

ROUNDING = ROUND_DOWN


def get_performance_value(goal_type, metric_value, target_value):
    rounded_metric_value = metric_value.quantize(Decimal('.01'), rounding=ROUNDING)
    if goal_type in INVERSE_PERFORMANCE_CAMPAIGN_GOALS:
        performance = (2 * target_value - rounded_metric_value) / target_value
    else:
        performance = rounded_metric_value / target_value
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


def create_campaign_goal(request, form, campaign, value=None, conversion_goal=None):
    if not form.is_valid():
        raise exc.ValidationError(errors=form.errors)

    goal = models.CampaignGoal.objects.create(
        type=form.cleaned_data['type'],
        primary=form.cleaned_data['primary'],
        campaign=campaign,
        conversion_goal=conversion_goal,
    )

    _add_entry_to_history(
        request,
        campaign,
        constants.HistoryActionType.GOAL_CHANGE,
        u'Added campaign goal "{}{}"'.format(
            (str(value) + ' ') if value else '',
            constants.CampaignGoalKPI.get_text(goal.type)
        )
    )

    return goal


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
        u'Deleted campaign goal "{}"'.format(
            constants.CampaignGoalKPI.get_text(goal.type)
        )
    )


def add_campaign_goal_value(request, goal, value, campaign, skip_history=False):
    goal_value = models.CampaignGoalValue(
        campaign_goal_id=goal.pk,
        value=value
    )
    goal_value.save(request)

    if not skip_history:
        _add_entry_to_history(
            request,
            campaign,
            constants.HistoryActionType.GOAL_CHANGE,
            u'Changed campaign goal value: "{}"'.format(
                CAMPAIGN_GOAL_NAME_FORMAT[goal.type].format(value)
            )
        )


def set_campaign_goal_primary(request, campaign, goal_id):
    goal = models.CampaignGoal.objects.get(pk=goal_id)

    models.CampaignGoal.objects.filter(campaign=campaign).update(primary=False)
    goal.primary = True
    goal.save()

    _add_entry_to_history(
        request,
        campaign,
        constants.HistoryActionType.GOAL_CHANGE,
        u'Campaign goal "{}" set as primary'.format(
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
            u'Deleted conversion goal "{}"'.format(
                conversion_goal.name,
                constants.ConversionGoalType.get_text(conversion_goal.type)
            )
        )


def create_conversion_goal(request, form, campaign, value=None):
    if not form.is_valid():
        raise exc.ValidationError(errors=form.errors)

    goals_count = models.ConversionGoal.objects.filter(campaign_id=campaign.id).count()
    if goals_count >= constants.MAX_CONVERSION_GOALS_PER_CAMPAIGN:
        raise exc.ValidationError(message='Max conversion goals per campaign exceeded')

    conversion_goal = models.ConversionGoal(campaign_id=campaign.id, type=form.cleaned_data['type'],
                                            name=form.cleaned_data['name'])

    if form.cleaned_data['type'] == constants.ConversionGoalType.PIXEL:
        try:
            pixel = models.ConversionPixel.objects.get(id=form.cleaned_data['goal_id'],
                                                       account_id=campaign.account_id)
        except models.ConversionPixel.DoesNotExist:
            raise exc.MissingDataError(message='Invalid conversion pixel')

        if pixel.archived:
            raise exc.MissingDataError(message='Invalid conversion pixel')

        conversion_goal.pixel = pixel
        conversion_goal.conversion_window = form.cleaned_data['conversion_window']
    else:
        conversion_goal.goal_id = form.cleaned_data['goal_id']

    with transaction.atomic():
        conversion_goal.save()

        campaign_goal_form = forms.CampaignGoalForm(dict(
            type=constants.CampaignGoalKPI.CPA,
            primary=False
        ), campaign_id=campaign.pk)

        campaign_goal = create_campaign_goal(
            request, campaign_goal_form, campaign, conversion_goal=conversion_goal, value=value
        )

    _add_entry_to_history(
        request,
        campaign,
        constants.HistoryActionType.GOAL_CHANGE,
        u'Added conversion goal with name "{}" of type {}'.format(
            conversion_goal.name,
            constants.ConversionGoalType.get_text(conversion_goal.type)
        )
    )

    return conversion_goal, campaign_goal


def extract_e_media_cost(data):
    return data.get(E_MEDIA_COST_COLUMN, 0)


def create_goals(campaign, data):
    campaign_goal_values = get_campaign_goal_values(campaign)
    ret = []
    for row in data:
        new_row = dict(row)
        e_media_cost = extract_e_media_cost(row)
        if e_media_cost:
            for campaign_goal_value in campaign_goal_values:
                goal_type = campaign_goal_value.campaign_goal.type
                new_row.update(calculate_goal_values(row, goal_type, e_media_cost))
        ret.append(new_row)
    return ret


def create_goal_totals(campaign, data):
    ret = dict(data)
    campaign_goal_values = get_campaign_goal_values(campaign)
    e_media_cost = extract_e_media_cost(data)
    if e_media_cost:
        for campaign_goal_value in campaign_goal_values:
            goal_type = campaign_goal_value.campaign_goal.type
            ret.update(calculate_goal_values(data, goal_type, e_media_cost))
    return ret


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


def calculate_goal_values(row, goal_type, e_media_cost):
    ret = {}
    if goal_type == constants.CampaignGoalKPI.CPA:
        goal_index = 1
        goal_name = ""
        while goal_index == 1 or goal_name in row:
            goal_name = 'conversion_goal_{}'.format(goal_index)
            if goal_name in row and row[goal_name]:
                ret['avg_cost_per_conversion_goal_{}'.format(goal_index)] = \
                    float(e_media_cost) / row[goal_name]
            goal_index += 1
    return ret


def get_campaign_goals(campaign, conversion_goals):
    cg_values = get_campaign_goal_values(campaign)
    ret = []
    for cg_value in cg_values:
        goal_type = cg_value.campaign_goal.type
        goal_name = constants.CampaignGoalKPI.get_text(
            goal_type
        )
        fields = {k: True for k in CAMPAIGN_GOAL_MAP.get(goal_type, [])}

        conversion_goal_name = None
        if goal_type == constants.CampaignGoalKPI.CPA:
            goal_name = 'Avg. CPA'
            conversion_goal_name = cg_value.campaign_goal.conversion_goal.name
            fields = dict(('{}'.format(k['id']), True)
                          for k in conversion_goals if k['name'] == conversion_goal_name)
            fields.update(
                dict(('avg_cost_per_{}'.format(k['id']), True)
                     for k in conversion_goals if k['name'] == conversion_goal_name)
            )

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


def get_goal_performance_status(goal_type, metric_value, planned_value, cost=None):
    rounded_cost = (cost and Decimal(cost) or Decimal('0')).quantize(
        Decimal('.01'), rounding=ROUNDING
    )
    if goal_type in COST_DEPENDANT_GOALS and rounded_cost and not metric_value:
        return get_goal_performance_category(0)
    if planned_value is None or metric_value is None:
        return get_goal_performance_category(None)
    performance = get_performance_value(goal_type, Decimal(metric_value), planned_value)
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


def _prepare_performance_output(campaign_goal, stats, conversion_goals):
    goal_values = campaign_goal.values.all()
    last_goal_value = goal_values and goal_values[0]
    planned_value = last_goal_value and last_goal_value.value or None
    e_media_cost = extract_e_media_cost(stats)
    if campaign_goal.type == constants.CampaignGoalKPI.CPA:
        conversion_column = campaign_goal.conversion_goal.get_view_key(conversion_goals)
        metric = stats.get(conversion_column, 0)
        metric_value = (float(e_media_cost) / metric) if (metric and e_media_cost is not None) else None
    else:
        metric_value = stats.get(CAMPAIGN_GOAL_PRIMARY_METRIC_MAP[campaign_goal.type])
    return (
        get_goal_performance_status(campaign_goal.type, metric_value, planned_value, cost=e_media_cost),
        metric_value,
        planned_value,
        campaign_goal,
    )


def get_goal_performance_metric(campaign_goal, conversion_goals):
    if campaign_goal.type == constants.CampaignGoalKPI.CPA:
        conversion_column = campaign_goal.conversion_goal.get_view_key(conversion_goals)
        return 'avg_cost_per_' + conversion_column
    return CAMPAIGN_GOAL_PRIMARY_METRIC_MAP[campaign_goal.type]


def get_goals_performance(user, campaign, start_date, end_date):
    constraints = stats.constraints_helper.prepare_campaign_constraints(
        user, campaign, [], start_date, end_date, models.Source.objects.all())
    stats_goals = stats.api_breakdowns.get_goals(constraints)
    query_results = stats.api_breakdowns.totals(user, constants.Level.CAMPAIGNS, [], constraints, stats_goals)

    performance = []
    for campaign_goal in stats_goals.campaign_goals:
        performance.append(_prepare_performance_output(
            campaign_goal,
            query_results,
            stats_goals.conversion_goals
        ))

    return performance


def get_campaign_goal_metrics(campaign, start_date, end_date):
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
        conversion_goals=None
    )


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
        conversion_goals=conversion_goals
    )


def eliminate_duplicates(campaign_goal_values):
    date_hash = {}
    for campaign_goal_value in campaign_goal_values:
        cgv_type = campaign_goal_value.campaign_goal.type
        date_hash[cgv_type] = date_hash.get(cgv_type, {})
        date_hash[cgv_type][campaign_goal_value.created_dt.date()] = campaign_goal_value

    ret = []
    for campaign_goal_type, date_values in date_hash.iteritems():
        if len(date_values) == 0:
            continue
        sorted_values = sorted(date_values.values(), key=lambda x: x.created_dt)
        ret.extend(sorted_values)
    return sorted(ret, key=lambda x: x.created_dt)


def generate_series(campaign_goal_values, pre_cg_vals, start_date, end_date, conversion_goals=None):
    last_cg_vals = {}
    cg_series = {}
    for cg_value in campaign_goal_values:
        cg = cg_value.campaign_goal
        name = goal_name(cg, conversion_goals)
        last_cg_vals[name] = cg_value

        if not cg_series.get(name):
            cg_series[name] = []
        cg_series[name].append(campaign_goal_dp(cg_value))

    # if starting campaign goal was defined before current range
    # or if no values are defined within current range(but exist before)
    # make sure to insert campaign goal value datapoints
    for pre_cg_id, pre_cg_val in pre_cg_vals.iteritems():
        pre_cg = pre_cg_val.campaign_goal
        pre_name = goal_name(pre_cg, conversion_goals)
        dp_to_preinsert = campaign_goal_dp(pre_cg_val, override_date=start_date)
        if pre_name not in cg_series:
            # in the case that the goal was set in distant past and never
            # updated create two points in current date range
            dp_to_postinsert = campaign_goal_dp(pre_cg_val, override_date=end_date)
            cg_series[pre_name] = [dp_to_preinsert, dp_to_postinsert]
        else:
            first = cg_series[pre_name][0]
            if first[0] > pre_cg_val.created_dt.date():
                cg_series[pre_name] = [dp_to_preinsert] +\
                    cg_series[pre_name]

    for name, last_cg_val in last_cg_vals.iteritems():
        if last_cg_val.created_dt.date() >= end_date:
            continue
        # duplicate last data point with date set to end date
        cg_series[name].append(
            campaign_goal_dp(last_cg_val, override_date=end_date),
        )
    return generate_missing(create_line_series(cg_series))


def goal_name(goal, conversion_goals=None):
    if goal.conversion_goal is None:
        return constants.CampaignGoalKPI.get_text(goal.type)
    return 'avg_cost_per_{}'.format(goal.conversion_goal.get_view_key(conversion_goals))


def create_line_series(cg_series):
    '''
    For a nice display we need a sequence of series where each serie are just
    duplicate points. This results in a sequence of horizontal lines
    '''
    new_series = {}
    for name, dps in cg_series.iteritems():
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
    for name, line_list in cg_series.iteritems():
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


def campaign_goal_dp(campaign_goal_value, override_date=None, override_value=None):
    date = campaign_goal_value.created_dt.date()
    if override_date is not None:
        date = override_date
    value = float(campaign_goal_value.value)
    if override_value is not None:
        value = override_value
    return (date, value,)


def inverted_campaign_goal_map(conversion_goals=None):
    # map from particular fields to goals
    ret = {}
    for goal, field in CAMPAIGN_GOAL_PRIMARY_METRIC_MAP.iteritems():
        ret[field] = {
            'id': constants.CampaignGoalKPI.get_text(goal),
            'name': constants.CampaignGoalKPI.get_text(goal),
        }

    cpa_text = constants.CampaignGoalKPI.get_text(constants.CampaignGoalKPI.CPA)
    for cg in conversion_goals:
        vk = cg.get_view_key(conversion_goals)

        ret['avg_cost_per_{}'.format(vk)] = {
            'id': 'avg_cost_per_{}'.format(vk),
            'name': '{prefix} - {conversion_goal_name}'.format(
                prefix=cpa_text,
                conversion_goal_name=cg.name
            ),
        }
    return ret


def get_allowed_campaign_goals_fields(user, campaign_goals, campaign_goal_values, conversion_goals):
    """
    Returns campaign goal field names that should be kept if user has
    proper permissions.
    """

    allowed_fields = []
    included_campaign_goals = []

    if user.has_perm('zemauth.campaign_goal_optimization'):
        included_campaign_goals = [x.campaign_goal.type for x in campaign_goal_values]

    for goal in included_campaign_goals:
        relevant_fields = CAMPAIGN_GOAL_MAP.get(goal, [])

        if goal == constants.CampaignGoalKPI.CPA:
            relevant_fields.extend([
                'avg_cost_per_{}'.format(cg.get_view_key(conversion_goals)) for cg in conversion_goals
            ])

        allowed_fields.extend(relevant_fields)

    if user.has_perm('zemauth.campaign_goal_performance'):
        allowed_fields.extend([
            'performance_' + x.get_view_key() for x in campaign_goals
        ])

    return allowed_fields


def get_allowed_conversion_goals_fields(user, conversion_goals):
    """
    Returns conversion goal column names that should be kept if user has
    proper permissions.
    """

    allowed = []
    if user.has_perm('zemauth.can_see_redshift_postclick_statistics'):
        allowed.extend([cg.get_view_key(conversion_goals) for cg in conversion_goals])

    return allowed


def get_allowed_pixels_fields(pixels):
    """
    Returns pixel column names and average costs column names that should be kept for all users.
    FIXME: This function should probably be in some other module.
    """
    allowed = []
    for pixel in pixels:
        for conversion_window in dash.constants.ConversionWindows.get_all():
            view_key = pixel.get_view_key(conversion_window)
            allowed.append(view_key)
            allowed.append('avg_cost_per_' + view_key)
    return allowed
