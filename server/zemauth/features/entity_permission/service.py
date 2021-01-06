# -*- coding: utf-8 -*-
from django.db import transaction

from .constants import AccessLevel
from .exceptions import EntityPermissionChangeNotAllowed
from .model import EntityPermission


@transaction.atomic
def set_entity_permissions_on_user(requested_user, request, account, agency, new_entity_permission_dicts):
    calling_user = request.user

    if requested_user.id == calling_user.id:
        return  # We ignore entity permission changes when a user is editing himself

    caller_entity_permissions = calling_user.get_entity_permissions(request, account, agency)
    old_entity_permissions = requested_user.get_entity_permissions(request, account, agency)
    new_entity_permissions = _map_dicts_to_entity_permissions(requested_user, new_entity_permission_dicts)

    requested_user.validate_entity_permissions(new_entity_permissions)

    caller_access_level = _get_access_level(caller_entity_permissions)
    old_access_level = _get_access_level(old_entity_permissions)
    new_access_level = _get_access_level(new_entity_permissions)

    if old_access_level > caller_access_level:
        raise EntityPermissionChangeNotAllowed("Can't change permissions of a user with a higher access level")

    if new_access_level > caller_access_level:
        raise EntityPermissionChangeNotAllowed("Can't promote user to higher access level than your own")

    if new_access_level != old_access_level:
        if new_access_level == AccessLevel.INTERNAL_USER or old_access_level == AccessLevel.INTERNAL_USER:
            requested_user.delete_entity_permissions(request, None, None)
        else:
            requested_user.delete_entity_permissions(request, account, agency)

        for new_permission in new_entity_permissions:
            _add_permission(calling_user, requested_user, new_permission)
    else:
        added_permissions = set(new_entity_permissions) - set(old_entity_permissions)
        removed_permissions = set(old_entity_permissions) - set(new_entity_permissions)

        if new_access_level == AccessLevel.ACCOUNT_MANAGER:
            for account_id in _get_distinct_account_ids(old_entity_permissions + new_entity_permissions):
                new_account_permissions = _get_permissions_for_account(new_entity_permissions, account_id)
                if len(list(new_account_permissions)) == 0:
                    _remove_all_permissions_on_account(requested_user, account_id)
                else:
                    removed_account_permissions = _get_permissions_for_account(removed_permissions, account_id)
                    added_account_permissions = _get_permissions_for_account(added_permissions, account_id)
                    _remove_and_add_permissions(
                        calling_user, requested_user, removed_account_permissions, added_account_permissions
                    )
        else:
            _remove_and_add_permissions(calling_user, requested_user, removed_permissions, added_permissions)

    #  Finally we check that we have left behind a consistent state
    final_entity_permissions = requested_user.get_entity_permissions(request, account, agency, True)
    requested_user.validate_entity_permissions(final_entity_permissions)


def add_entity_permissions(user, agency, account, permissions):
    for permission in permissions:
        _add_entity_permission(user, agency, account, permission)


def _map_dicts_to_entity_permissions(requested_user, entity_permission_dicts):
    for ep_dict in entity_permission_dicts:
        if "readonly" in ep_dict:
            del ep_dict["readonly"]

    entity_permissions = [EntityPermission(**ep_dict) for ep_dict in entity_permission_dicts]
    for ep in entity_permissions:
        ep.user_id = requested_user.id

    return entity_permissions


def _get_access_level(entity_permissions):
    if _is_internal_user(entity_permissions):
        return AccessLevel.INTERNAL_USER
    elif _is_account_manager(entity_permissions):
        return AccessLevel.ACCOUNT_MANAGER
    elif _is_agency_manager(entity_permissions):
        return AccessLevel.AGENCY_MANAGER
    else:
        return AccessLevel.NONE


def _is_internal_user(entity_permissions) -> bool:
    return any(
        filter(lambda permission: permission.account_id is None and permission.agency_id is None, entity_permissions)
    )


def _is_account_manager(entity_permissions) -> bool:
    return any(filter(lambda permission: permission.account_id is not None, entity_permissions))


def _is_agency_manager(entity_permissions) -> bool:
    return any(filter(lambda permission: permission.agency_id is not None, entity_permissions))


def _remove_all_permissions_on_account(user, account_id: int):
    account_permissions = user.entitypermission_set.filter(account_id=account_id)

    for account_permission in account_permissions:
        account_permission.delete()


def _add_permission(calling_user, requested_user, permission_to_add: EntityPermission):
    if calling_user.has_greater_or_equal_permission(permission_to_add):
        _add_entity_permission(
            requested_user, permission_to_add.agency, permission_to_add.account, permission_to_add.permission
        )
    else:
        requested_user.invalidate_entity_permission_cache()
        raise EntityPermissionChangeNotAllowed(f"You are not allowed to add {permission_to_add.__str__()}")


def _remove_permission(calling_user, requested_user, permission_to_remove: EntityPermission):
    if calling_user.has_greater_or_equal_permission(permission_to_remove):
        permission_to_remove.delete()
    else:
        requested_user.invalidate_entity_permission_cache()
        raise EntityPermissionChangeNotAllowed(f"You are not allowed to delete {permission_to_remove.__str__()}")


def _get_distinct_account_ids(entity_permissions):
    return {ep.account_id for ep in entity_permissions if ep.account_id is not None}


def _get_permissions_for_account(entity_permissions, account_id):
    return [ep for ep in entity_permissions if ep.account_id == account_id]


def _remove_and_add_permissions(calling_user, requested_user, removed_permissions, added_permissions):
    for removed_permission in removed_permissions:
        _remove_permission(calling_user, requested_user, removed_permission)
    for added_permission in added_permissions:
        _add_permission(calling_user, requested_user, added_permission)


def _add_entity_permission(user, agency, account, permission):
    EntityPermission.objects.create(user, permission, agency=agency, account=account)
