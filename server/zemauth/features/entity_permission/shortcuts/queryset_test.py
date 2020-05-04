from __future__ import annotations

import abc
from typing import Any

import core.models
import zemauth.features.entity_permission
import zemauth.models
from utils.magic_mixer import magic_mixer


class HasEntityPermissionQuerySetTestCaseMixin(metaclass=abc.ABCMeta):
    assertEqual: Any
    assertRaises: Any

    def test_filter_by_entity_permission(self):
        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)

        model_with_agency_scope: Any = self._get_model_with_agency_scope(agency)
        model_with_account_scope: Any = self._get_model_with_account_scope(account)

        user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)
        for permission in zemauth.features.entity_permission.Permission.get_all():
            if model_with_agency_scope is not None:
                has_agency_scope = True
                self._for_all_entities(user, model_with_agency_scope, permission)
                self._for_agency(user, model_with_agency_scope, agency, permission)
                self._for_account(user, model_with_agency_scope, account, permission, has_agency_scope)
                self._for_none(user, model_with_agency_scope, permission)
            if model_with_account_scope is not None:
                has_agency_scope = False
                self._for_all_entities(user, model_with_account_scope, permission)
                self._for_agency(user, model_with_account_scope, agency, permission)
                self._for_account(user, model_with_account_scope, account, permission, has_agency_scope)
                self._for_none(user, model_with_account_scope, permission)

    @abc.abstractmethod
    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        """
        Return model instance connected to agency in order to test queryset filtering
        based on entity permissions. Return None to skip tests.
        :param agency: core.models.Agency
        :return: model (with with agency scope)
        """
        raise NotImplementedError("Not implemented.")

    @abc.abstractmethod
    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        """
        Return model instance connected to account in order to test queryset filtering
        based on entity permissions. Return None to skip tests.
        :param account: core.models.Account
        :return: model (with account scope)
        """
        raise NotImplementedError("Not implemented.")

    def _for_all_entities(self, user: zemauth.models.User, model: Any, permission: str):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=user,
            agency=None,
            account=None,
            permission=permission,
        )

        qs = self._get_query_set(user, model, permission)
        self.assertEqual(model, qs.get())

    def _for_agency(self, user: zemauth.models.User, model: Any, agency: core.models.Agency, permission: str):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission, user=user, agency=agency, permission=permission
        )

        qs = self._get_query_set(user, model, permission)
        self.assertEqual(model, qs.get())

    def _for_account(
        self,
        user: zemauth.models.User,
        model: Any,
        account: core.models.Account,
        permission: str,
        has_agency_scope: bool,
    ):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission, user=user, account=account, permission=permission
        )

        if has_agency_scope:
            """
            If model has agency scope, having account
            permission is not enough. We must assert
            that we can't access it.
            """
            with self.assertRaises(type(model).DoesNotExist):
                qs = self._get_query_set(user, model, permission)
                qs.get()
        else:
            qs = self._get_query_set(user, model, permission)
            self.assertEqual(model, qs.get())

    def _for_none(self, user: zemauth.models.User, model: Any, permission: str):
        user.entitypermission_set.all().delete()
        with self.assertRaises(type(model).DoesNotExist):
            qs = self._get_query_set(user, model, permission)
            qs.get()

    @staticmethod
    def _get_query_set(user: zemauth.models.User, model: Any, permission: str):
        return type(model).objects.all().filter_by_entity_permission(user, permission).filter(id=int(model.id))
