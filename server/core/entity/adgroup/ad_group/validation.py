import core.entity

import dash.constants

from . import exceptions


class AdGroupValidatorMixin(object):
    def _validate_bidding_type(self, bidding_type):
        if self.bidding_type == bidding_type:
            return

        was_turned_on = core.entity.settings.AdGroupSettings.objects.filter(
            ad_group=self, state=dash.constants.AdGroupSettingsState.ACTIVE
        ).exists()

        if was_turned_on:
            raise exceptions.CannotChangeBiddingType(
                "Cannot set bidding type for an ad group that was already turned on."
            )
