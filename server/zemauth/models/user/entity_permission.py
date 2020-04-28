from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Union

import core.models
import zemauth.features.entity_permission

if TYPE_CHECKING:
    Entity = Union[core.models.Agency, core.models.Account, core.models.Campaign, core.models.AdGroup]


class EntityPermissionMixin(object):
    entitypermission_set: Any

    def has_read_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.READ, entity)

    def has_write_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.WRITE, entity)

    def has_user_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.USER, entity)

    def has_budget_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.BUDGET, entity)

    def has_budget_margin_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.BUDGET_MARGIN, entity)

    def has_agency_spend_and_margin_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.AGENCY_SPEND_MARGIN, entity)

    def has_media_cost_data_cost_and_licence_fee_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.MEDIA_COST_DATA_COST_LICENCE_FEE, entity)

    def has_rest_api_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.RESTAPI, entity)

    def refresh_entity_permissions(self):
        zemauth.features.entity_permission.refresh_entity_permissions_for_user(self)

    def _has_perm_on(self, permission: str, entity: Entity) -> bool:
        if entity is None:
            return False

        if isinstance(entity, core.models.Agency):
            if self.entitypermission_set.filter(permission=permission).filter_by_agency(entity).exists():
                return True
            return self._has_perm_on_wildcard(permission)
        elif isinstance(entity, core.models.Account):
            if self.entitypermission_set.filter(permission=permission).filter_by_account(entity).exists():
                return True
            return self._has_perm_on_wildcard(permission)
        elif isinstance(entity, core.models.Campaign):
            if self.entitypermission_set.filter(permission=permission).filter_by_campaign(entity).exists():
                return True
            return self._has_perm_on_wildcard(permission)
        elif isinstance(entity, core.models.AdGroup):
            if self.entitypermission_set.filter(permission=permission).filter_by_adgroup(entity).exists():
                return True
            return self._has_perm_on_wildcard(permission)
        else:
            agency_full_name = f"{core.models.Agency.__module__}.{core.models.Agency.__name__}"
            account_full_name = f"{core.models.Account.__module__}.{core.models.Account.__name__}"
            campaign_full_name = f"{core.models.Campaign.__module__}.{core.models.Campaign.__name__}"
            ad_group_full_name = f"{core.models.AdGroup.__module__}.{core.models.AdGroup.__name__}"
            raise TypeError(
                f"Entity must be of types: {agency_full_name}, {account_full_name}, {campaign_full_name}, {ad_group_full_name}."
            )

    def _has_perm_on_wildcard(self, permission: str) -> bool:
        return self.entitypermission_set.filter(permission=permission, agency=None, account=None).exists()
