import abc

from django.db import models

import zemauth.models


class EntityPermissionMixin(object):
    @abc.abstractmethod
    def _get_account(self) -> models.Model:
        raise NotImplementedError("Not implemented.")

    def get_users_with(self, permission: str) -> models.QuerySet:
        account = self._get_account()
        if account is None:
            raise ValueError("Account must be provided.")

        queryset = zemauth.models.User.objects.filter(
            entitypermission__account=account, entitypermission__permission=permission
        )
        if account.agency is not None:
            queryset |= zemauth.models.User.objects.filter(
                entitypermission__agency=account.agency, entitypermission__permission=permission
            )

        return queryset

    @staticmethod
    def _get_agency_users_with(agency: models.Model, permission: str) -> models.QuerySet:
        """
        Helper function to be used on models with agency scope.
        """
        return zemauth.models.User.objects.filter(
            entitypermission__agency=agency, entitypermission__permission=permission
        )
