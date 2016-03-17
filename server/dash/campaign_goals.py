from django.db import transaction

from utils import exc
from dash import models, constants
from dash import forms
from dash.views import helpers


def create_campaign_goal(request, form, campaign, conversion_goal=None):
    if not form.is_valid():
        raise exc.ValidationError(errors=form.errors)

    return models.CampaignGoal.objects.create(
        type=form.cleaned_data['type'],
        primary=form.cleaned_data['primary'],
        campaign=campaign,
        conversion_goal=conversion_goal,
    )


def delete_campaign_goal(request, goal_id):
    goal = models.CampaignGoal.objects.all().select_related('campaign').get(pk=goal_id)

    if goal.conversion_goal:
        delete_conversion_goal(request, goal.conversion_goal.pk, goal.campaign)
        return

    models.CampaignGoalValue.objects.filter(campaign_goal_id=goal_id).delete()
    goal.delete()


def add_campaign_goal_value(request, goal_id, value):
    goal_value = models.CampaignGoalValue(
        campaign_goal_id=goal_id,
        value=value
    )
    goal_value.save(request)


def set_campaign_goal_primary(request, campaign, goal_id):
    models.CampaignGoal.objects.filter(campaign=campaign).update(primary=False)
    goal = models.CampaignGoal.objects.get(pk=goal_id)
    goal.primary = True
    goal.save()


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

        new_settings = campaign.get_current_settings().copy_settings()
        new_settings.changes_text = u'Deleted conversion goal "{}"'.format(
            conversion_goal.name,
            constants.ConversionGoalType.get_text(conversion_goal.type)
        )
        new_settings.save(request)

    helpers.log_useraction_if_necessary(
        request,
        constants.UserActionType.DELETE_CONVERSION_GOAL,
        campaign=campaign
    )


def create_conversion_goal(request, form, campaign):
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

        campaign_goal = create_campaign_goal(request, campaign_goal_form, campaign, conversion_goal=conversion_goal)

    new_settings = campaign.get_current_settings().copy_settings()
    new_settings.changes_text = u'Added conversion goal with name "{}" of type {}'.format(
        conversion_goal.name,
        constants.ConversionGoalType.get_text(conversion_goal.type)
    )
    new_settings.save(request)

    helpers.log_useraction_if_necessary(
        request,
        constants.UserActionType.CREATE_CONVERSION_GOAL,
        campaign=campaign
    )

    return conversion_goal, campaign_goal
