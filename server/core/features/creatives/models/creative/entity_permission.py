from django.db import models

import zemauth.features.entity_permission.shortcuts


class EntityPermissionMixin(zemauth.features.entity_permission.shortcuts.EntityPermissionMixin):
    def get_users_with(self, permission: str) -> models.QuerySet:
        if self.account is not None:
            return super().get_users_with(permission)
        else:
            return super()._get_agency_users_with(self.agency, permission)

    def _get_account(self) -> models.Model:
        return self.account
