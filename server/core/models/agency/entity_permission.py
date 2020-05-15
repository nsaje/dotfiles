from django.db import models

import zemauth.features.entity_permission.shortcuts


class EntityPermissionMixin(zemauth.features.entity_permission.shortcuts.EntityPermissionMixin):
    def get_users_with(self, permission: str) -> models.QuerySet:
        return super()._get_agency_users_with(self, permission)

    def _get_account(self) -> models.Model:
        pass
