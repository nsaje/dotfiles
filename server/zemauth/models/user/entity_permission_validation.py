from zemauth.features.entity_permission import Permission
from zemauth.models.user.exceptions import MissingReadPermission
from zemauth.models.user.exceptions import MissingRequiredPermission
from zemauth.models.user.exceptions import MixedPermissionLevels


class EntityPermissionValidationMixin(object):
    def validate_entity_permissions(self, entity_permissions):
        has_account_permission = any(
            filter(lambda ep: ep.account is not None or ep.account_id is not None, entity_permissions)
        )
        has_agency_permission = any(
            filter(lambda ep: ep.agency is not None or ep.agency_id is not None, entity_permissions)
        )
        has_internal_permission = any(
            filter(
                lambda ep: ep.account is None and ep.account_id is None and ep.agency is None and ep.agency_id is None,
                entity_permissions,
            )
        )

        if has_account_permission and has_agency_permission:
            raise MixedPermissionLevels(
                "Setting both account and agency permissions on entities of the same agency is not allowed."
            )

        if has_internal_permission and (has_account_permission or has_agency_permission):
            raise MixedPermissionLevels("Setting both internal and non-internal permissions is not allowed.")

        if has_account_permission:
            account_ids = [self._get_account_id(ep) for ep in entity_permissions]

            for account_id in account_ids:
                account_permissions = list(
                    filter(lambda ep: self._get_account_id(ep) == account_id, entity_permissions)
                )
                self._validate_required_permissions(set(ep.permission for ep in account_permissions))
        else:
            self._validate_required_permissions(set(ep.permission for ep in entity_permissions))

    def _get_account_id(self, entity_permission):
        return entity_permission.account_id or entity_permission.account.id

    def _validate_required_permissions(self, permissions_for_entity):
        if Permission.READ not in permissions_for_entity:
            raise MissingReadPermission("All entities must have READ permission")

        if (
            Permission.MEDIA_COST_DATA_COST_LICENCE_FEE in permissions_for_entity
            and Permission.AGENCY_SPEND_MARGIN not in permissions_for_entity
        ):
            raise MissingRequiredPermission(
                "If an entity has MEDIA_COST_DATA_COST_LICENCE_FEE permission, it must also have AGENCY_SPEND_MARGIN permission."
            )

        if (
            Permission.BASE_COSTS_SERVICE_FEE in permissions_for_entity
            and Permission.MEDIA_COST_DATA_COST_LICENCE_FEE not in permissions_for_entity
        ):
            raise MissingRequiredPermission(
                "If an entity has BASE_COSTS_SERVICE_FEE permission, it must also have MEDIA_COST_DATA_COST_LICENCE_FEE permission."
            )
