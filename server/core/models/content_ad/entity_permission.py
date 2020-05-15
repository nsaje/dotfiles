from django.db import models

import zemauth.features.entity_permission.shortcuts


class EntityPermissionMixin(zemauth.features.entity_permission.shortcuts.EntityPermissionMixin):
    def _get_account(self) -> models.Model:
        return self.ad_group.campaign.account
