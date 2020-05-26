from typing import Any

from django.db import models
from rest_framework import pagination

import zemauth.models
from utils import zlogging

logger = zlogging.getLogger(__name__)

LOG_MESSAGE = "Detected entity permission access differences"


def log_differences_and_get_queryset(
    user: zemauth.models.User,
    permission: str,
    user_permission_queryset: models.QuerySet,
    entity_permission_queryset: models.QuerySet,
    entity_id: str = None,
) -> models.QuerySet:
    if entity_id is not None:
        _log_single(user, permission, user_permission_queryset, entity_permission_queryset, entity_id)
    else:
        _log_all(user, permission, user_permission_queryset, entity_permission_queryset)
    return (
        entity_permission_queryset if user.has_perm("zemauth.fea_use_entity_permission") else user_permission_queryset
    )


def log_paginated_differences_and_get_queryset(
    request: Any,
    paginator: pagination.BasePagination,
    permission: str,
    user_permission_queryset: models.QuerySet,
    entity_permission_queryset: models.QuerySet,
) -> models.QuerySet:
    _log_all_paginated(request, paginator, permission, user_permission_queryset, entity_permission_queryset)
    return (
        entity_permission_queryset
        if request.user.has_perm("zemauth.fea_use_entity_permission")
        else user_permission_queryset
    )


def _log_single(
    user: zemauth.models.User,
    permission: str,
    user_permission_queryset: models.QuerySet,
    entity_permission_queryset: models.QuerySet,
    entity_id: str,
):
    try:
        row_id_by_user_permission = user_permission_queryset.values_list("id", flat=True).get(id=int(entity_id))
    except user_permission_queryset.model.DoesNotExist:
        row_id_by_user_permission = None
    try:
        row_id_by_entity_permission = entity_permission_queryset.values_list("id", flat=True).get(id=int(entity_id))
    except entity_permission_queryset.model.DoesNotExist:
        row_id_by_entity_permission = None

    if row_id_by_user_permission != row_id_by_entity_permission:
        logger.warning(
            LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            row_id_by_user_permission=row_id_by_user_permission,
            row_id_by_entity_permission=row_id_by_entity_permission,
            user_permission_queryset_model_name=user_permission_queryset.model.__name__,
            entity_permission_queryset_model_name=entity_permission_queryset.model.__name__,
        )


def _log_all(
    user: zemauth.models.User,
    permission: str,
    user_permission_queryset: models.QuerySet,
    entity_permission_queryset: models.QuerySet,
):
    rows_ids_by_user_permission = set(user_permission_queryset.values_list("id", flat=True))
    rows_ids_by_entity_permission = set(entity_permission_queryset.values_list("id", flat=True))

    if rows_ids_by_user_permission != rows_ids_by_entity_permission:
        logger.warning(
            LOG_MESSAGE,
            user_email=user.email,
            permission=permission,
            rows_ids_by_user_permission=rows_ids_by_user_permission,
            rows_ids_by_entity_permission=rows_ids_by_entity_permission,
            user_permission_queryset_model_name=user_permission_queryset.model.__name__,
            entity_permission_queryset_model_name=entity_permission_queryset.model.__name__,
        )


def _log_all_paginated(
    request: Any,
    paginator: pagination.BasePagination,
    permission: str,
    user_permission_queryset: models.QuerySet,
    entity_permission_queryset: models.QuerySet,
):
    rows_ids_by_user_permission = paginator.paginate_queryset(user_permission_queryset.values("id"), request)
    rows_ids_by_entity_permission = paginator.paginate_queryset(entity_permission_queryset.values("id"), request)

    if rows_ids_by_user_permission != rows_ids_by_entity_permission:
        logger.warning(
            LOG_MESSAGE,
            user_email=request.user.email,
            permission=permission,
            rows_ids_by_user_permission=[x.get("id") for x in rows_ids_by_user_permission],
            rows_ids_by_entity_permission=[x.get("id") for x in rows_ids_by_entity_permission],
            user_permission_queryset_model_name=user_permission_queryset.model.__name__,
            entity_permission_queryset_model_name=entity_permission_queryset.model.__name__,
        )
