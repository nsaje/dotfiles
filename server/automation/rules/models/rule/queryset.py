from django.db import models

import zemauth.features.entity_permission.shortcuts

from ... import constants


class RuleQuerySet(zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetMixin, models.QuerySet):
    def filter_enabled(self):
        return self.filter(state=constants.RuleState.ENABLED)

    def exclude_archived(self, show_archived=False):
        if show_archived:
            return self
        return self.exclude(archived=True)

    def _get_query_path_to_account(self) -> str:
        return "account"

    def _filter_by_entity_permission(self, user: zemauth.models.User, permission: str) -> models.QuerySet:
        query_set = super(RuleQuerySet, self)._filter_by_entity_permission(user, permission)
        query_set |= self.filter(
            models.Q(agency__entitypermission__user=user) & models.Q(agency__entitypermission__permission=permission)
        )
        return query_set
