import core.common
import dash.constants
import utils.exc

from . import model


class ConversionGoalValidator(core.common.BaseValidator):

    def clean(self):
        if self.type == dash.constants.ConversionGoalType.PIXEL:
            if not self.conversion_window:
                raise utils.exc.ValidationError('Conversion window required')

            if self.pixel.archived:
                raise utils.exc.ValidationError(message='Invalid conversion pixel')
        else:
            if model.ConversionGoal.objects.filter(campaign=self.campaign,
                                                   type=self.type,
                                                   goal_id=self.goal_id).exists():
                raise utils.exc.ValidationError('Goal must be unique per campaign!')

    @staticmethod
    def get_pixel(campaign, goal_id):
        try:
            pixel = dash.models.ConversionPixel.objects.get(id=goal_id,
                                                            account=campaign.account)
            return pixel
        except dash.models.ConversionPixel.DoesNotExist:
            raise utils.exc.ValidationError(message='Invalid conversion pixel')
