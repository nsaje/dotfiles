from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Union

import core.models
import zemauth.features.entity_permission
from utils import zlogging
from zemauth.features.entity_permission import EntityPermission
from zemauth.features.entity_permission import Permission
from zemauth.models.user.entity_permission_validation import EntityPermissionValidationMixin
from zemauth.models.user.exceptions import EntityPermissionChangeNotAllowed

if TYPE_CHECKING:
    Entity = Union[core.models.Agency, core.models.Account, core.models.Campaign, core.models.AdGroup]

logger = zlogging.getLogger(__name__)

LOG_MESSAGE = "Detected entity permission access differences"


class EntityPermissionMixin(EntityPermissionValidationMixin):
    email: str
    has_perm: Callable[..., bool]
    entitypermission_set: Any

    def has_read_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.READ, entity)

    def has_write_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.WRITE, entity)

    def has_user_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.USER, entity)

    def has_budget_perm_on(
        self, entity: Entity, fallback_permission: str = None, negate_fallback_permission: bool = False
    ) -> bool:
        return self._has_perm_on_and_log_differences(
            zemauth.features.entity_permission.Permission.BUDGET,
            entity,
            fallback_permission=fallback_permission,
            negate_fallback_permission=negate_fallback_permission,
        )

    def has_budget_margin_perm_on(self, entity: Entity, fallback_permission: str = None) -> bool:
        return self._has_perm_on_and_log_differences(
            zemauth.features.entity_permission.Permission.BUDGET_MARGIN, entity, fallback_permission=fallback_permission
        )

    def has_agency_spend_and_margin_perm_on(self, entity: Entity, fallback_permission: str = None) -> bool:
        return self._has_perm_on_and_log_differences(
            zemauth.features.entity_permission.Permission.AGENCY_SPEND_MARGIN,
            entity,
            fallback_permission=fallback_permission,
        )

    def has_media_cost_data_cost_and_licence_fee_perm_on(self, entity: Entity, fallback_permission: str = None) -> bool:
        return self._has_perm_on_and_log_differences(
            zemauth.features.entity_permission.Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
            entity,
            fallback_permission=fallback_permission,
        )

    def has_base_costs_and_service_fee_perm_on(self, entity: Entity, fallback_permission: str = None) -> bool:
        return self._has_perm_on_and_log_differences(
            zemauth.features.entity_permission.Permission.BASE_COSTS_SERVICE_FEE,
            entity,
            fallback_permission=fallback_permission,
        )

    def has_rest_api_perm_on(self, entity: Entity) -> bool:
        return self._has_perm_on(zemauth.features.entity_permission.Permission.RESTAPI, entity)

    def has_perm_on_all_entities(self, permission: str) -> bool:
        if permission is None or permission not in zemauth.features.entity_permission.Permission.get_all():
            return False
        return self.entitypermission_set.filter(permission=permission, agency=None, account=None).exists()

    def refresh_entity_permissions(self):
        zemauth.features.entity_permission.refresh_entity_permissions_for_user(self)

    def get_entity_permissions(self, request, account, agency):
        calling_user = request.user

        if account is None and agency is None and calling_user.has_perm_on_all_entities(Permission.USER):
            return self.entitypermission_set

        requested_agency = account.agency if account else agency

        callers_accounts = zemauth.access.get_accounts(calling_user, Permission.USER)
        callers_accounts_on_agency = callers_accounts.filter(agency=requested_agency)

        return (
            self.entitypermission_set.filter_by_accounts(callers_accounts_on_agency)
            | self.entitypermission_set.filter_by_agency(requested_agency)
            | self.entitypermission_set.filter_by_internal()
        )

    def set_entity_permissions(self, new_entity_permissions, request, account, agency):
        calling_user = request.user
        self.validate_entity_permissions(new_entity_permissions)

        has_internal_permission = any(
            filter(
                lambda permission: not permission.get("account") and not permission.get("agency"),
                new_entity_permissions,
            )
        )

        if has_internal_permission and calling_user.has_perm_on_all_entities(Permission.USER):
            self.delete_entity_permissions(request, None, None)
        else:
            self.delete_entity_permissions(request, account, agency)

        if new_entity_permissions is not None:
            for permission in new_entity_permissions:
                if permission.get("account"):
                    if calling_user.has_user_perm_on(permission["account"]):
                        EntityPermission.objects.create(self, permission["permission"], account=permission["account"])
                    else:
                        raise EntityPermissionChangeNotAllowed("No USER permission on account")
                elif permission.get("agency"):
                    if calling_user.has_user_perm_on(permission["agency"]):
                        EntityPermission.objects.create(self, permission["permission"], agency=permission["agency"])
                    else:
                        raise EntityPermissionChangeNotAllowed("No USER permission on agency")
                else:
                    if calling_user.has_perm_on_all_entities(Permission.USER):
                        EntityPermission.objects.create(self, permission["permission"])
                    else:
                        raise EntityPermissionChangeNotAllowed("No internal USER permission")

    def delete_entity_permissions(self, request, account, agency):
        self.get_entity_permissions(request, account, agency).all().delete()

    def _has_perm_on_and_log_differences(
        self, permission: str, entity: Entity, fallback_permission: str = None, negate_fallback_permission: bool = False
    ) -> bool:
        has_entity_permission = self._has_perm_on(permission, entity)
        if fallback_permission is not None:
            has_fallback_permission = self.has_perm(fallback_permission)
            if negate_fallback_permission:
                has_fallback_permission = not has_fallback_permission
            if has_entity_permission != has_fallback_permission:
                logger.warning(
                    LOG_MESSAGE,
                    user_email=self.email,
                    entity_id=entity.id,
                    entity_class_name=type(entity).__name__,
                    fallback_permission=fallback_permission,
                    has_user_permission=has_fallback_permission,
                    entity_permission=permission,
                    has_entity_permission=has_entity_permission,
                )
            return (
                has_entity_permission if self.has_perm("zemauth.fea_use_entity_permission") else has_fallback_permission
            )
        return has_entity_permission

    def _has_perm_on(self, permission: str, entity: Entity) -> bool:
        if entity is None:
            return False

        if isinstance(entity, core.models.Agency):
            if self.entitypermission_set.filter(permission=permission).filter_by_agency(entity).exists():
                return True
            return self.has_perm_on_all_entities(permission)
        elif isinstance(entity, core.models.Account):
            if self.entitypermission_set.filter(permission=permission).filter_by_account(entity).exists():
                return True
            return self.has_perm_on_all_entities(permission)
        elif isinstance(entity, core.models.Campaign):
            if self.entitypermission_set.filter(permission=permission).filter_by_campaign(entity).exists():
                return True
            return self.has_perm_on_all_entities(permission)
        elif isinstance(entity, core.models.AdGroup):
            if self.entitypermission_set.filter(permission=permission).filter_by_adgroup(entity).exists():
                return True
            return self.has_perm_on_all_entities(permission)
        else:
            agency_full_name = f"{core.models.Agency.__module__}.{core.models.Agency.__name__}"
            account_full_name = f"{core.models.Account.__module__}.{core.models.Account.__name__}"
            campaign_full_name = f"{core.models.Campaign.__module__}.{core.models.Campaign.__name__}"
            ad_group_full_name = f"{core.models.AdGroup.__module__}.{core.models.AdGroup.__name__}"
            raise TypeError(
                f"Entity must be of types: {agency_full_name}, {account_full_name}, {campaign_full_name}, {ad_group_full_name}."
            )
