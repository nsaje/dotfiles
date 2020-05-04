from django.db import models

import zemauth.features.entity_permission.shortcuts
import zemauth.models


class BidModifierQuerySet(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet
):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(ad_group__campaign__account__users__id=user.id)
            | models.Q(ad_group__campaign__account__agency__users__id=user.id)
        ).distinct()

    def _get_query_path_to_account(self) -> str:
        return "ad_group__campaign__account"
