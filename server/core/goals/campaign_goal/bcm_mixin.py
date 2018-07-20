from django.db import transaction

import core.bcm
from utils import numbers


class CampaignGoalBCMMixin(object):
    @transaction.atomic
    def migrate_to_bcm_v2(self, request, fee, margin):
        from dash import campaign_goals

        if self.type in campaign_goals.COST_DEPENDANT_GOALS:
            current_value = self.get_current_value()
            if current_value:
                new_value = self._transform_campaign_goal_value(current_value.value, fee, margin)
                self.add_value(request, new_value)

    def _transform_campaign_goal_value(self, value, fee, margin):
        including_fee_and_margin = core.bcm.calculations.apply_fee_and_margin(value, fee, margin)
        return numbers.round_decimal_half_down(including_fee_and_margin, places=2)
