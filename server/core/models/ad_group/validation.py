import core.models
import dash.constants

from . import exceptions


class AdGroupValidatorMixin(object):
    def validate(self, changes, request=None):
        self._validate_bidding_type(changes, request)

    def _validate_bidding_type(self, changes, request):
        if self.bidding_type == changes.get("bidding_type", self.bidding_type) or changes["bidding_type"] is None:
            return

        was_turned_on = core.models.settings.AdGroupSettings.objects.filter(
            ad_group=self, state=dash.constants.AdGroupSettingsState.ACTIVE
        ).exists()

        if was_turned_on:
            raise exceptions.CannotChangeBiddingType(
                "Cannot set bidding type for an ad group that was already turned on."
            )
