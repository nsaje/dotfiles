import core.common
import dash.constants

from . import exceptions
from . import model


class ConversionGoalValidator(core.common.BaseValidator):
    def clean(self):
        self.validate_goal_count()
        if self.type == dash.constants.ConversionGoalType.PIXEL:
            self.validate_pixel_goal()
        else:
            self.validate_non_pixel_goal()

    def validate_goal_count(self):
        goals_count = model.ConversionGoal.objects.filter(campaign=self.campaign).count()
        if goals_count >= dash.constants.MAX_CONVERSION_GOALS_PER_CAMPAIGN:
            raise exceptions.ConversionGoalLimitExceeded("Max conversion goals per campaign exceeded")

    def validate_pixel_goal(self):
        if not self.conversion_window:
            raise exceptions.ConversionWindowRequired("Conversion window required")

        if self.pixel.archived:
            raise exceptions.ConversionPixelInvalid("Invalid conversion pixel")

    def validate_non_pixel_goal(self):
        conversion_goals = model.ConversionGoal.objects.filter(
            campaign=self.campaign, type=self.type, goal_id=self.goal_id
        )
        if conversion_goals.exists():
            raise exceptions.ConversionGoalNotUnique("Goal must be unique per campaign!")

        if not self.goal_id:
            raise exceptions.GoalIDInvalid("Goal ID may not be blank or null.")

    @staticmethod
    def get_pixel(campaign, goal_id):
        try:
            pixel = dash.models.ConversionPixel.objects.get(id=goal_id, account=campaign.account)
            return pixel

        except ValueError:
            raise exceptions.GoalIDInvalid("Goal ID must be a number.")

        except dash.models.ConversionPixel.DoesNotExist:
            raise exceptions.ConversionPixelInvalid("Conversion pixel does not exist.")
