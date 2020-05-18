from __future__ import annotations

import abc

from django.db import models

import zemauth.models


class HasEntityPermissionQuerySetMixin(metaclass=abc.ABCMeta):
    def filter_by_entity_permission(self, user: zemauth.models.User, permission: str) -> models.QuerySet:
        if user.has_perm_on_all_entities(permission):
            return self

        return self._filter_by_entity_permission(user, permission).distinct()

    @abc.abstractmethod
    def _get_query_path_to_account(self) -> str:
        """
        Return query path to account.
        Return empty string if model is account.
        :return: query path to account
        """
        raise NotImplementedError("Not implemented.")

    def _filter_by_entity_permission(self, user: zemauth.models.User, permission: str) -> models.QuerySet:
        query_path_to_account = self._get_query_path_to_account()
        if query_path_to_account is None:
            raise ValueError("Query path to account must be provided.")

        query_path_to_account = f"{query_path_to_account}__" if query_path_to_account != "" else query_path_to_account
        query_set = self.filter(
            models.Q(**{f"{query_path_to_account}entitypermission__user": user})
            & models.Q(**{f"{query_path_to_account}entitypermission__permission": permission})
        )
        query_set |= self.filter(
            models.Q(**{f"{query_path_to_account}agency__entitypermission__user": user})
            & models.Q(**{f"{query_path_to_account}agency__entitypermission__permission": permission})
        )

        return query_set
