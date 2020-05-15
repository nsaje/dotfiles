from __future__ import annotations

import abc
from typing import Any

import core.models
import zemauth.features.entity_permission
import zemauth.models
from utils import test_helper
from utils.magic_mixer import magic_mixer


class EntityPermissionTestCaseMixin(metaclass=abc.ABCMeta):
    def test_get_users_with(self):
        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)

        model_with_agency_scope: Any = self._get_model_with_agency_scope(agency)
        model_with_account_scope: Any = self._get_model_with_account_scope(account)

        users_with_access = magic_mixer.cycle(5).blend(zemauth.models.User)
        users_no_access = magic_mixer.cycle(5).blend(zemauth.models.User)

        users_ids_with_access = [x.id for x in users_with_access]
        users_ids_no_access = [x.id for x in users_no_access]

        for permission in zemauth.features.entity_permission.Permission.get_all():
            if model_with_agency_scope is not None:
                self._prepare(users_with_access, users_no_access, model_with_agency_scope, permission)
                queryset = model_with_agency_scope.get_users_with(permission)
                for user in queryset:
                    self.assertTrue(user.id in users_ids_with_access)
                    self.assertTrue(user.id not in users_ids_no_access)

            if model_with_account_scope is not None:
                self._prepare(users_with_access, users_no_access, model_with_account_scope, permission)
                queryset = model_with_account_scope.get_users_with(permission)
                for user in queryset:
                    self.assertTrue(user.id in users_ids_with_access)
                    self.assertTrue(user.id not in users_ids_no_access)

    @abc.abstractmethod
    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        """
        Return model instance connected to agency in order to test get_users_with queryset
        based on entity permissions. Return None to skip tests.
        :param agency: core.models.Agency
        :return: model (with with agency scope)
        """
        raise NotImplementedError("Not implemented.")

    @abc.abstractmethod
    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        """
        Return model instance connected to account in order to test get_users_with queryset
        based on entity permissions. Return None to skip tests.
        :param account: core.models.Account
        :return: model (with account scope)
        """
        raise NotImplementedError("Not implemented.")

    @staticmethod
    def _prepare(users_with_access, users_no_access, model, permission):
        for user in users_with_access:
            user.entitypermission_set.all().delete()
        for user in users_no_access:
            user.entitypermission_set.all().delete()
        for user in users_with_access:
            test_helper.add_entity_permissions(user, [permission], model)
