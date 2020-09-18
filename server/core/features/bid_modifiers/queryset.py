from django.db import models

import zemauth.features.entity_permission.shortcuts
import zemauth.models

from . import constants


class BidModifierQuerySet(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet
):
    def filter_publisher_bid_modifiers(self):
        return self.filter(type=constants.BidModifierType.PUBLISHER)

    def filter_placement_bid_modifiers(self):
        return self.filter(type=constants.BidModifierType.PLACEMENT)

    def _get_query_path_to_account(self) -> str:
        return "ad_group__campaign__account"
