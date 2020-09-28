from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Union

import django.core.cache

import core.models
import zemauth.features.entity_permission
from utils import cache_helper
from utils import zlogging
from zemauth.features.entity_permission import EntityPermission
from zemauth.features.entity_permission import EntityPermissionChangeNotAllowed
from zemauth.features.entity_permission import Permission
from zemauth.models.user.entity_permission_validation import EntityPermissionValidationMixin

if TYPE_CHECKING:
    Entity = Union[core.models.Agency, core.models.Account, core.models.Campaign, core.models.AdGroup]

logger = zlogging.getLogger(__name__)

LOG_MESSAGE = "Detected entity permission access differences"
CACHE_NAME = "entity_permission_cache"


class EntityPermissionMixin(EntityPermissionValidationMixin):
    id: int
    email: str
    has_perm: Callable[..., bool]
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

    def has_base_costs_and_service_fee_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.BASE_COSTS_SERVICE_FEE, entity)

    def has_rest_api_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.RESTAPI, entity)

    def has_perm_on(self, permission: str, entity: Entity) -> bool:
        if permission is None or permission not in zemauth.features.entity_permission.Permission.get_all():
            return False

        return self._has_perm_on(permission, entity)

    def has_perm_on_all_entities(self, permission: str) -> bool:
        if permission is None or permission not in zemauth.features.entity_permission.Permission.get_all():
            return False

        return any(
            x.permission == permission and x.agency is None and x.account is None for x in self._entity_permission_cache
        )

    def has_greater_or_equal_permission(self, entity_permission: EntityPermission) -> bool:
        if entity_permission.agency is None and entity_permission.account is None:
            return self.has_perm_on_all_entities(entity_permission.permission)
        else:
            entity = entity_permission.agency or entity_permission.account
            return self._has_perm_on(entity_permission.permission, entity)

    def refresh_entity_permissions(self):
        zemauth.features.entity_permission.refresh_entity_permissions_for_user(self)

    def get_entity_permissions(
        self, request, account, agency, show_hidden_reporting_permissions=False
    ) -> Iterable[EntityPermission]:
        calling_user = request.user
        if account is None and agency is None and calling_user.has_perm_on_all_entities(Permission.USER):
            entity_permissions = self._entity_permission_cache
        else:
            requested_agency = account.agency if account else agency

            accounts_qs = zemauth.access.get_accounts(calling_user, Permission.USER)
            accounts = list(accounts_qs.filter(agency=requested_agency))

            entity_permissions = [
                x
                for x in self._entity_permission_cache
                if (x.account in accounts) or (x.agency == requested_agency) or (x.agency is None and x.account is None)
            ]

        if show_hidden_reporting_permissions:
            return entity_permissions
        else:
            return [
                x
                for x in entity_permissions
                if not x.is_reporting_permission() or calling_user.has_greater_or_equal_permission(x)
            ]

    def set_entity_permissions(self, request, account, agency, new_entity_permissions):
        zemauth.features.entity_permission.set_entity_permissions_on_user(
            self, request, account, agency, new_entity_permissions
        )

    def delete_entity_permissions(self, request, account, agency):
        calling_user = request.user
        if self.id == calling_user.id:
            raise EntityPermissionChangeNotAllowed("User cannot delete his/her own permissions")

        entity_permissions = self.get_entity_permissions(request, account, agency, True)
        for entity_permission in entity_permissions:
            entity_permission.delete()

    def invalidate_entity_permission_cache(self):
        cache_key = cache_helper.get_cache_key(self.id)
        cache = django.core.cache.caches[CACHE_NAME]
        cache.delete(cache_key)

    @property
    def all_entity_permissions(self):
        return self._entity_permission_cache

    @property
    def _entity_permission_cache(self) -> Iterable[EntityPermission]:
        cache_key = cache_helper.get_cache_key(self.id)
        cache = django.core.cache.caches[CACHE_NAME]

        cached = cache.get(cache_key, None)
        if cached is None:
            results = list(self.entitypermission_set.all().select_related("user", "agency", "account"))
            cache.set(cache_key, results)
            return results

        return cached

    def _has_perm_on(self, permission: str, entity: Entity) -> bool:
        if entity is None:
            return False

        if isinstance(entity, core.models.Agency):
            if self.has_perm_on_all_entities(permission):
                return True
            return any(x.permission == permission and x.agency == entity for x in self._entity_permission_cache)
        elif isinstance(entity, core.models.Account):
            if self.has_perm_on_all_entities(permission):
                return True
            return any(
                x.permission == permission and x.account == entity for x in self._entity_permission_cache
            ) or any(x.permission == permission and x.agency == entity.agency for x in self._entity_permission_cache)
        elif isinstance(entity, core.models.Campaign):
            if self.has_perm_on_all_entities(permission):
                return True
            return any(
                x.permission == permission and x.account == entity.account for x in self._entity_permission_cache
            ) or any(
                x.permission == permission and x.agency == entity.account.agency for x in self._entity_permission_cache
            )
        elif isinstance(entity, core.models.AdGroup):
            if self.has_perm_on_all_entities(permission):
                return True
            return any(
                x.permission == permission and x.account == entity.campaign.account
                for x in self._entity_permission_cache
            ) or any(
                x.permission == permission and x.agency == entity.campaign.account.agency
                for x in self._entity_permission_cache
            )
        else:
            agency_full_name = f"{core.models.Agency.__module__}.{core.models.Agency.__name__}"
            account_full_name = f"{core.models.Account.__module__}.{core.models.Account.__name__}"
            campaign_full_name = f"{core.models.Campaign.__module__}.{core.models.Campaign.__name__}"
            ad_group_full_name = f"{core.models.AdGroup.__module__}.{core.models.AdGroup.__name__}"
            raise TypeError(
                f"Entity must be of types: {agency_full_name}, {account_full_name}, {campaign_full_name}, {ad_group_full_name}."
            )
