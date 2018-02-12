from django.db import transaction

from dash import constants
import core.common
import utils.exc

from . import model
from . import validator


class ConversionGoalManager(core.common.BaseManager):

    @transaction.atomic
    def create(self, request, campaign, conversion_goal_type, goal_id, conversion_window=None):
        goals_count = model.ConversionGoal.objects.filter(campaign=campaign).count()
        if goals_count >= constants.MAX_CONVERSION_GOALS_PER_CAMPAIGN:
            raise utils.exc.ValidationError(message='Max conversion goals per campaign exceeded')

        conversion_goal = model.ConversionGoal(campaign=campaign, type=conversion_goal_type)

        if conversion_goal_type == constants.ConversionGoalType.PIXEL:
            pixel = validator.ConversionGoalValidator.get_pixel(campaign, goal_id)
            name = '{} {}'.format(
                pixel.name,
                constants.ConversionWindows.get_text(conversion_window)
            )
            conversion_goal.name = name
            conversion_goal.pixel = pixel
            conversion_goal.conversion_window = conversion_window
        else:
            conversion_goal.name = goal_id
            conversion_goal.goal_id = goal_id

        conversion_goal.save()

        campaign.write_history(
            'Added conversion goal with name "{}" of type {}'.format(
                conversion_goal.name,
                constants.ConversionGoalType.get_text(conversion_goal.type)
            ),
            action_type=constants.HistoryActionType.GOAL_CHANGE,
            user=request.user
        )

        return conversion_goal
