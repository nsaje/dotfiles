# -*- coding: utf-8 -*-

from django.db import transaction

from .constants import Permission
from .model import EntityPermission

CAN_SEE_BASIC_COST_BREAKDOWN_GROUP_ID = 58
DISABLE_MARGINS_AND_BUDGETS_GROUP_ID = 39
ENABLE_MARGINS_AND_BUDGETS_GROUP_ID = 55
ENABLE_MARGIN_AND_BUDGETS_AND_HIDE_LICENCE_FEE_GROUP_ID = 59
EXTERNAL_REST_API_GROUP_ID = 33


@transaction.atomic
def refresh_entity_permissions_for_user(user):
    user.entitypermission_set.all().delete()
    _handle_account_manager(user)
    _handle_agency_manager(user)
    _handle_internal_user(user)


def _handle_account_manager(user):
    accounts = user.account_set.all()
    if len(accounts) == 0:
        return

    for account in accounts:
        _add_entity_permission(user, None, account, Permission.READ)
        _add_entity_permission(user, None, account, Permission.WRITE)

        if not user.groups.filter(pk=DISABLE_MARGINS_AND_BUDGETS_GROUP_ID).exists():
            _add_entity_permission(user, None, account, Permission.BUDGET)
            if user.groups.filter(pk=ENABLE_MARGINS_AND_BUDGETS_GROUP_ID).exists():
                _add_entity_permission(user, None, account, Permission.BUDGET_MARGIN)

        if user.groups.filter(
            pk__in=[ENABLE_MARGINS_AND_BUDGETS_GROUP_ID, CAN_SEE_BASIC_COST_BREAKDOWN_GROUP_ID]
        ).exists():
            _add_entity_permission(user, None, account, Permission.AGENCY_SPEND_MARGIN)
            if not user.groups.filter(pk=ENABLE_MARGIN_AND_BUDGETS_AND_HIDE_LICENCE_FEE_GROUP_ID).exists():
                _add_entity_permission(user, None, account, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE)

        if user.groups.filter(pk=EXTERNAL_REST_API_GROUP_ID).exists():
            _add_entity_permission(user, None, account, Permission.RESTAPI)


def _handle_agency_manager(user):
    agencies = user.agency_set.all()
    if len(agencies) == 0:
        return

    for agency in agencies:
        _add_entity_permission(user, agency, None, Permission.READ)
        _add_entity_permission(user, agency, None, Permission.WRITE)
        _add_entity_permission(user, agency, None, Permission.USER)

        if not user.groups.filter(pk=DISABLE_MARGINS_AND_BUDGETS_GROUP_ID).exists():
            _add_entity_permission(user, agency, None, Permission.BUDGET)
            _add_entity_permission(user, agency, None, Permission.BUDGET_MARGIN)
            _add_entity_permission(user, agency, None, Permission.AGENCY_SPEND_MARGIN)
            _add_entity_permission(user, agency, None, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE)

        if user.groups.filter(pk=EXTERNAL_REST_API_GROUP_ID).exists():
            _add_entity_permission(user, agency, None, Permission.RESTAPI)


def _handle_internal_user(user):
    if not (user.is_superuser or user.has_perm("zemauth.can_see_all_accounts")):
        return

    _add_entity_permission(user, None, None, Permission.READ)
    _add_entity_permission(user, None, None, Permission.WRITE)
    _add_entity_permission(user, None, None, Permission.USER)
    _add_entity_permission(user, None, None, Permission.BUDGET)
    _add_entity_permission(user, None, None, Permission.BUDGET_MARGIN)
    _add_entity_permission(user, None, None, Permission.AGENCY_SPEND_MARGIN)
    _add_entity_permission(user, None, None, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE)
    _add_entity_permission(user, None, None, Permission.BASE_COSTS_SERVICE_FEE)
    _add_entity_permission(user, None, None, Permission.RESTAPI)


def _add_entity_permission(user, agency, account, permission):
    EntityPermission.objects.create(user, permission, agency=agency, account=account)
