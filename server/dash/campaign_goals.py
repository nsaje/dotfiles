from django.db import transaction

from utils import exc
from dash import models, constants, forms
from dash.views import helpers
import utils.lc_helper

CAMPAIGN_GOAL_NAME_FORMAT = {
    constants.CampaignGoalKPI.TIME_ON_SITE: '{} seconds on site',
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: '{} bounce rate',
    constants.CampaignGoalKPI.PAGES_PER_SESSION: '{} pages per session',
    constants.CampaignGoalKPI.CPA: '{} CPA',
    constants.CampaignGoalKPI.CPC: '{} CPC',
    constants.CampaignGoalKPI.CPM: '{} CPM',
}

CAMPAIGN_GOAL_VALUE_FORMAT = {
    constants.CampaignGoalKPI.TIME_ON_SITE: lambda x: '{:.2f} s'.format(x),
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: lambda x: '{:.2f} s'.format(x),
    constants.CampaignGoalKPI.PAGES_PER_SESSION: lambda x: '{:.2f} s'.format(x),
    constants.CampaignGoalKPI.CPA: utils.lc_helper.default_currency,
    constants.CampaignGoalKPI.CPC: utils.lc_helper.default_currency,
    constants.CampaignGoalKPI.CPM: utils.lc_helper.default_currency,
}

CAMPAIGN_GOAL_MAP = {
    constants.CampaignGoalKPI.MAX_BOUNCE_RATE: [
        'unbounced_visits',
        'avg_cost_per_non_bounced_visitor',
    ],
    constants.CampaignGoalKPI.PAGES_PER_SESSION: [
        'total_pageviews',
        'avg_cost_per_pageview',
    ],
    constants.CampaignGoalKPI.TIME_ON_SITE: [
        'total_seconds',
        'avg_cost_per_second',
    ],
    constants.CampaignGoalKPI.CPA: [],
    constants.CampaignGoalKPI.CPC: [],
    constants.CampaignGoalKPI.CPM: [],
}


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
        constants.UserActionType.CREATE_CAMPAIGN_GOAL,
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
        constants.UserActionType.DELETE_CAMPAIGN_GOAL,
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
            constants.UserActionType.CHANGE_CAMPAIGN_GOAL_VALUE,
            u'Changed campaign goal value: "{} {}"'.format(
                value,
                constants.CampaignGoalKPI.get_text(goal.type)
            )
        )


def set_campaign_goal_primary(request, campaign, goal_id):
    models.CampaignGoal.objects.filter(campaign=campaign).update(primary=False)
    goal = models.CampaignGoal.objects.get(pk=goal_id)
    goal.primary = True
    goal.save()

    _add_entry_to_history(
        request,
        campaign,
        constants.UserActionType.CHANGE_PRIMARY_CAMPAIGN_GOAL,
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
            constants.UserActionType.DELETE_CONVERSION_GOAL,
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
        constants.UserActionType.CREATE_CONVERSION_GOAL,
        u'Added conversion goal with name "{}" of type {}'.format(
            conversion_goal.name,
            constants.ConversionGoalType.get_text(conversion_goal.type)
        )
    )

    return conversion_goal, campaign_goal


def extract_cost(data):
    return data.get('media_cost', 0)


def create_goals(campaign, data):
    campaign_goal_values = get_campaign_goal_values(campaign)
    ret = []
    for row in data:
        new_row = dict(row)
        cost = extract_cost(row)
        if cost:
            for campaign_goal_value in campaign_goal_values:
                goal_type = campaign_goal_value.campaign_goal.type
                new_row.update(calculate_goal_values(row, goal_type, cost))
        ret.append(new_row)
    # TODO: CPA
    return ret


def create_goal_totals(campaign, data, cost):
    if not cost:
        return data

    ret = dict(data)
    campaign_goal_values = get_campaign_goal_values(campaign)
    for campaign_goal_value in campaign_goal_values:
        goal_type = campaign_goal_value.campaign_goal.type
        ret.update(calculate_goal_values(data, goal_type, cost))
    # TODO: CPA
    return ret


def get_campaign_goal_values(campaign):
    return models.CampaignGoalValue.objects.all().filter(
        campaign_goal__campaign=campaign
    ).order_by(
        'campaign_goal',
        '-created_dt'
    ).distinct('campaign_goal').select_related(
        'campaign_goal'
    )


def calculate_goal_values(row, goal_type, cost):
    ret = {}
    if goal_type == constants.CampaignGoalKPI.TIME_ON_SITE:
        total_seconds = (row.get('avg_tos') or 0) *\
            (row.get('visits') or 0)
        ret['total_seconds'] = total_seconds
        ret['avg_cost_per_second'] = float(cost) / total_seconds if\
            total_seconds != 0 else 0
    elif goal_type == constants.CampaignGoalKPI.MAX_BOUNCE_RATE:
        unbounced_rate = 100.0 - (row.get('bounce_rate') or 0)
        unbounced_visits = (unbounced_rate / 100.0) * (row.get('visits', 0) or 0)
        ret['unbounced_visits'] = unbounced_visits
        ret['avg_cost_per_non_bounced_visitor'] = float(cost) / unbounced_visits if\
            unbounced_visits != 0 else 0
    elif goal_type == constants.CampaignGoalKPI.PAGES_PER_SESSION:
        total_pageviews = (row.get('pv_per_visit') or 0) *\
            (row.get('visits') or 0)
        ret['total_pageviews'] = total_pageviews
        # avg. cost per pageview
        ret['avg_cost_per_pageview'] = float(cost) / total_pageviews if\
            total_pageviews != 0 else 0
    elif goal_type == constants.CampaignGoalKPI.CPA:
        goal_index = 1
        goal_name = ""
        while goal_index == 1 or goal_name in row:
            goal_name = 'conversion_goal_{}'.format(goal_index)
            if goal_name in row:
                ret['avg_cost_per_conversion_goal_{}'.format(goal_index)] =\
                    float(cost) / row[goal_name] if row[goal_name] != 0 else 0
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
            goal_name = 'Avg. cost per conversion'
            conversion_goal_name = cg_value.campaign_goal.conversion_goal.name
            fields = dict(('avg_cost_per_{}'.format(k['id']), True)
                          for k in conversion_goals if k['name'] == conversion_goal_name)

        ret.append({
            'name': goal_name,
            'conversion': conversion_goal_name,
            'value': float(cg_value.value),
            'fields': fields,
        })
    return ret


def _add_entry_to_history(request, campaign, action_type, changes_text):
    new_settings = campaign.get_current_settings().copy_settings()
    new_settings.changes_text = changes_text
    new_settings.save(request)

    helpers.log_useraction_if_necessary(
        request,
        action_type,
        campaign=campaign
    )
