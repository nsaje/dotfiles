from django.db import models

import zemauth.features.entity_permission.shortcuts
import zemauth.models


class AgencyQuerySet(zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(users__id=user.id)
            | models.Q(sales_representative__id=user.id)
            | models.Q(cs_representative__id=user.id)
        ).distinct()

    def _get_query_path_to_account(self) -> str:
        pass

    def _filter_by_entity_permission(self, user: zemauth.models.User, permission: str) -> models.QuerySet:
        return self.filter(models.Q(entitypermission__user=user) & models.Q(entitypermission__permission=permission))
