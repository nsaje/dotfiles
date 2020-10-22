import random

import django.contrib.auth.models
from django.db.models import Q
from django.test import TestCase

import core.models
import zemauth.models
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from ...models.user.exceptions import MissingRequiredPermission
from .constants import Permission
from .exceptions import EntityPermissionChangeNotAllowed
from .service import refresh_entity_permissions_for_user
from .service import set_entity_permissions_on_user

DEFAULT_PERMISSIONS = [Permission.READ, Permission.USER, Permission.AGENCY_SPEND_MARGIN]


class EntityPermissionServiceTestCase(TestCase):
    def setUp(self) -> None:
        self.can_see_basic_cost_breakdown_group = magic_mixer.blend(django.contrib.auth.models.Group, id=58)
        self.disable_margins_and_budgets_group = magic_mixer.blend(django.contrib.auth.models.Group, id=39)
        self.enable_margins_and_budgets_group = magic_mixer.blend(django.contrib.auth.models.Group, id=55)
        self.enable_margin_and_budgets_and_hide_licence_fee_group = magic_mixer.blend(
            django.contrib.auth.models.Group, id=59
        )
        self.external_rest_api_group = magic_mixer.blend(django.contrib.auth.models.Group, id=33)

    def test_account_manager_full_access(self):
        user = magic_mixer.blend(
            zemauth.models.User,
            groups=[
                self.can_see_basic_cost_breakdown_group,
                self.enable_margins_and_budgets_group,
                self.external_rest_api_group,
            ],
        )
        account = magic_mixer.blend(core.models.Account, users=[user])

        self.assertEqual(len(user.entitypermission_set.all()), 0)

        refresh_entity_permissions_for_user(user)
        entity_permissions = list(user.entitypermission_set.all())

        self.assertEqual(len(entity_permissions), 7)
        for entity_permission in entity_permissions:
            self.assertIsNone(entity_permission.agency_id)
            self.assertEqual(entity_permission.account_id, account.id)

        permissions = list(entity_permission.permission for entity_permission in entity_permissions)

        self.assertIn(Permission.READ, permissions)
        self.assertIn(Permission.WRITE, permissions)
        self.assertIn(Permission.BUDGET, permissions)
        self.assertIn(Permission.BUDGET_MARGIN, permissions)
        self.assertIn(Permission.AGENCY_SPEND_MARGIN, permissions)
        self.assertIn(Permission.MEDIA_COST_DATA_COST_LICENCE_FEE, permissions)
        self.assertIn(Permission.RESTAPI, permissions)

    def test_account_manager_limited_access(self):
        user = magic_mixer.blend(
            zemauth.models.User,
            groups=[
                self.can_see_basic_cost_breakdown_group,
                self.disable_margins_and_budgets_group,
                self.enable_margins_and_budgets_group,
                self.enable_margin_and_budgets_and_hide_licence_fee_group,
                self.external_rest_api_group,
            ],
        )
        account = magic_mixer.blend(core.models.Account, users=[user])

        self.assertEqual(len(user.entitypermission_set.all()), 0)

        refresh_entity_permissions_for_user(user)
        entity_permissions = list(user.entitypermission_set.all())

        self.assertEqual(len(entity_permissions), 4)
        for entity_permission in entity_permissions:
            self.assertIsNone(entity_permission.agency_id)
            self.assertEqual(entity_permission.account_id, account.id)

        permissions = list(entity_permission.permission for entity_permission in entity_permissions)

        self.assertIn(Permission.READ, permissions)
        self.assertIn(Permission.WRITE, permissions)
        self.assertIn(Permission.AGENCY_SPEND_MARGIN, permissions)
        self.assertIn(Permission.RESTAPI, permissions)

    def test_agency_manager_full_access(self):
        user = magic_mixer.blend(zemauth.models.User, groups=[self.external_rest_api_group])
        agency = magic_mixer.blend(core.models.Agency, users=[user])

        self.assertEqual(len(user.entitypermission_set.all()), 0)

        refresh_entity_permissions_for_user(user)
        entity_permissions = list(user.entitypermission_set.all())

        self.assertEqual(len(entity_permissions), 8)
        for entity_permission in entity_permissions:
            self.assertEqual(entity_permission.agency_id, agency.id)
            self.assertIsNone(entity_permission.account_id)

        permissions = list(entity_permission.permission for entity_permission in entity_permissions)

        self.assertIn(Permission.READ, permissions)
        self.assertIn(Permission.WRITE, permissions)
        self.assertIn(Permission.USER, permissions)
        self.assertIn(Permission.BUDGET, permissions)
        self.assertIn(Permission.BUDGET_MARGIN, permissions)
        self.assertIn(Permission.AGENCY_SPEND_MARGIN, permissions)
        self.assertIn(Permission.MEDIA_COST_DATA_COST_LICENCE_FEE, permissions)
        self.assertIn(Permission.RESTAPI, permissions)

    def test_agency_manager_limited_access(self):
        user = magic_mixer.blend(
            zemauth.models.User, groups=[self.disable_margins_and_budgets_group, self.external_rest_api_group]
        )
        agency = magic_mixer.blend(core.models.Agency, users=[user])

        self.assertEqual(len(user.entitypermission_set.all()), 0)

        refresh_entity_permissions_for_user(user)
        entity_permissions = list(user.entitypermission_set.all())

        self.assertEqual(len(entity_permissions), 4)
        for entity_permission in entity_permissions:
            self.assertEqual(entity_permission.agency_id, agency.id)
            self.assertIsNone(entity_permission.account_id)

        permissions = list(entity_permission.permission for entity_permission in entity_permissions)

        self.assertIn(Permission.READ, permissions)
        self.assertIn(Permission.WRITE, permissions)
        self.assertIn(Permission.USER, permissions)
        self.assertIn(Permission.RESTAPI, permissions)

    def test_internal_user(self):
        user = magic_mixer.blend_user(is_superuser=True)

        self.assertEqual(len(user.entitypermission_set.all()), 0)

        refresh_entity_permissions_for_user(user)
        entity_permissions = list(user.entitypermission_set.all())

        self.assertEqual(len(entity_permissions), 9)
        for entity_permission in entity_permissions:
            self.assertIsNone(entity_permission.agency_id)
            self.assertIsNone(entity_permission.account_id)

        permissions = list(entity_permission.permission for entity_permission in entity_permissions)

        self.assertIn(Permission.READ, permissions)
        self.assertIn(Permission.WRITE, permissions)
        self.assertIn(Permission.USER, permissions)
        self.assertIn(Permission.BUDGET, permissions)
        self.assertIn(Permission.BUDGET_MARGIN, permissions)
        self.assertIn(Permission.AGENCY_SPEND_MARGIN, permissions)
        self.assertIn(Permission.MEDIA_COST_DATA_COST_LICENCE_FEE, permissions)
        self.assertIn(Permission.BASE_COSTS_SERVICE_FEE, permissions)
        self.assertIn(Permission.RESTAPI, permissions)

    def test_agency_manager_and_account_manager_full_access(self):
        user = magic_mixer.blend(
            zemauth.models.User,
            groups=[
                self.can_see_basic_cost_breakdown_group,
                self.enable_margins_and_budgets_group,
                self.external_rest_api_group,
            ],
        )

        # user is agency manager on agency_one and also account manager on connected accounts
        agency_one = magic_mixer.blend(core.models.Agency, users=[user])  # user is agency manager
        magic_mixer.cycle(5).blend(core.models.Account, agency=agency_one, users=[user])  # user is account manager

        # use is account manager on account connected to agency_two
        agency_two = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency_two, users=[user])  # use is account manager

        self.assertEqual(len(user.entitypermission_set.all()), 0)

        refresh_entity_permissions_for_user(user)
        entity_permissions = list(user.entitypermission_set.all())

        self.assertEqual(len(entity_permissions), 15)

        ageny_entity_permissions = [
            entity_permission for entity_permission in entity_permissions if entity_permission.agency_id is not None
        ]
        self.assertEqual(len(ageny_entity_permissions), 8)

        for entity_permission in ageny_entity_permissions:
            self.assertEqual(entity_permission.agency_id, agency_one.id)
            self.assertIsNone(entity_permission.account_id)

        agency_permissions = list(entity_permission.permission for entity_permission in ageny_entity_permissions)

        self.assertIn(Permission.READ, agency_permissions)
        self.assertIn(Permission.WRITE, agency_permissions)
        self.assertIn(Permission.USER, agency_permissions)
        self.assertIn(Permission.BUDGET, agency_permissions)
        self.assertIn(Permission.BUDGET_MARGIN, agency_permissions)
        self.assertIn(Permission.AGENCY_SPEND_MARGIN, agency_permissions)
        self.assertIn(Permission.MEDIA_COST_DATA_COST_LICENCE_FEE, agency_permissions)
        self.assertIn(Permission.RESTAPI, agency_permissions)

        account_entity_permissions = [
            entity_permission for entity_permission in entity_permissions if entity_permission.account_id is not None
        ]
        self.assertEqual(len(account_entity_permissions), 7)

        for entity_permission in account_entity_permissions:
            self.assertIsNone(entity_permission.agency_id)
            self.assertEqual(entity_permission.account_id, account.id)

        account_permissions = list(entity_permission.permission for entity_permission in account_entity_permissions)

        self.assertIn(Permission.READ, account_permissions)
        self.assertIn(Permission.WRITE, account_permissions)
        self.assertIn(Permission.BUDGET, account_permissions)
        self.assertIn(Permission.BUDGET_MARGIN, account_permissions)
        self.assertIn(Permission.AGENCY_SPEND_MARGIN, account_permissions)
        self.assertIn(Permission.MEDIA_COST_DATA_COST_LICENCE_FEE, account_permissions)
        self.assertIn(Permission.RESTAPI, account_permissions)


class EntityPermissionServiceSetEntityPermissionsTestCase(BaseTestCase):
    def test_is_change_allowed(self):
        #  An account manager can only create or edit another account manager, but can't promote him
        self._test_is_change_allowed_case("account_mgr", None, "account_mgr")
        self._test_is_change_allowed_case("account_mgr", None, "agency_mgr", True)
        self._test_is_change_allowed_case("account_mgr", None, "internal_usr", True)
        self._test_is_change_allowed_case("account_mgr", "account_mgr", "account_mgr")
        self._test_is_change_allowed_case("account_mgr", "account_mgr", "agency_mgr", True)
        self._test_is_change_allowed_case("account_mgr", "account_mgr", "internal_usr", True)
        self._test_is_change_allowed_case("account_mgr", "agency_mgr", "account_mgr", True)
        self._test_is_change_allowed_case("account_mgr", "agency_mgr", "agency_mgr", True)
        self._test_is_change_allowed_case("account_mgr", "agency_mgr", "internal_usr", True)
        self._test_is_change_allowed_case("account_mgr", "internal_usr", "account_mgr", True)
        self._test_is_change_allowed_case("account_mgr", "internal_usr", "agency_mgr", True)
        self._test_is_change_allowed_case("account_mgr", "internal_usr", "internal_usr", True)
        #  An agency manager can create or edit account and agency managers, and also promote account managers or downgrade agency managers
        self._test_is_change_allowed_case("agency_mgr", None, "account_mgr")
        self._test_is_change_allowed_case("agency_mgr", None, "agency_mgr")
        self._test_is_change_allowed_case("agency_mgr", None, "internal_usr", True)
        self._test_is_change_allowed_case("agency_mgr", "account_mgr", "account_mgr")
        self._test_is_change_allowed_case("agency_mgr", "account_mgr", "agency_mgr")
        self._test_is_change_allowed_case("agency_mgr", "account_mgr", "internal_usr", True)
        self._test_is_change_allowed_case("agency_mgr", "agency_mgr", "account_mgr")
        self._test_is_change_allowed_case("agency_mgr", "agency_mgr", "agency_mgr")
        self._test_is_change_allowed_case("agency_mgr", "agency_mgr", "internal_usr", True)
        self._test_is_change_allowed_case("agency_mgr", "internal_usr", "account_mgr", True)
        self._test_is_change_allowed_case("agency_mgr", "internal_usr", "agency_mgr", True)
        self._test_is_change_allowed_case("agency_mgr", "internal_usr", "internal_usr", True)
        #  An internal user can do whatever he wants
        self._test_is_change_allowed_case("internal_usr", None, "account_mgr")
        self._test_is_change_allowed_case("internal_usr", None, "agency_mgr")
        self._test_is_change_allowed_case("internal_usr", None, "internal_usr")
        self._test_is_change_allowed_case("internal_usr", "account_mgr", "account_mgr")
        self._test_is_change_allowed_case("internal_usr", "account_mgr", "agency_mgr")
        self._test_is_change_allowed_case("internal_usr", "account_mgr", "internal_usr")
        self._test_is_change_allowed_case("internal_usr", "agency_mgr", "account_mgr")
        self._test_is_change_allowed_case("internal_usr", "agency_mgr", "agency_mgr")
        self._test_is_change_allowed_case("internal_usr", "agency_mgr", "internal_usr")
        self._test_is_change_allowed_case("internal_usr", "internal_usr", "account_mgr")
        self._test_is_change_allowed_case("internal_usr", "internal_usr", "agency_mgr")
        self._test_is_change_allowed_case("internal_usr", "internal_usr", "internal_usr")

    def test_create(self):
        self._test_create_case("account_mgr", "account_mgr")
        self._test_create_case("agency_mgr", "account_mgr")
        self._test_create_case("agency_mgr", "agency_mgr")
        self._test_create_case("internal_usr", "account_mgr")
        self._test_create_case("internal_usr", "agency_mgr")
        self._test_create_case("internal_usr", "internal_usr")

    def test_change_level_with_disallowed_permissions(self):
        #  Changing level with allowed permissions has already been tested by test_is_change_allowed
        self._test_change_level_with_disallowed_permissions_case("agency_mgr", "account_mgr", "agency_mgr")
        self._test_change_level_with_disallowed_permissions_case("agency_mgr", "agency_mgr", "account_mgr")
        self._test_change_level_with_disallowed_permissions_case("internal_usr", "account_mgr", "agency_mgr")
        self._test_change_level_with_disallowed_permissions_case("internal_usr", "account_mgr", "internal_usr")
        self._test_change_level_with_disallowed_permissions_case("internal_usr", "agency_mgr", "account_mgr")
        self._test_change_level_with_disallowed_permissions_case("internal_usr", "agency_mgr", "internal_usr")
        self._test_change_level_with_disallowed_permissions_case("internal_usr", "internal_usr", "account_mgr")
        self._test_change_level_with_disallowed_permissions_case("internal_usr", "internal_usr", "agency_mgr")

    def test_add_permission(self):
        self._test_add_permission_case("account_mgr", "account_mgr")
        self._test_add_permission_case("agency_mgr", "account_mgr")
        self._test_add_permission_case("agency_mgr", "agency_mgr")
        self._test_add_permission_case("internal_usr", "account_mgr")
        self._test_add_permission_case("internal_usr", "agency_mgr")
        self._test_add_permission_case("internal_usr", "internal_usr")

    def test_remove_permission(self):
        self._test_remove_permission_case("account_mgr", "account_mgr")
        self._test_remove_permission_case("agency_mgr", "account_mgr")
        self._test_remove_permission_case("agency_mgr", "agency_mgr")
        self._test_remove_permission_case("internal_usr", "account_mgr")
        self._test_remove_permission_case("internal_usr", "agency_mgr")
        self._test_remove_permission_case("internal_usr", "internal_usr")

    def _test_create_case(self, calling_user_role, requested_user_role):
        #  These changes are allowed
        self._test_set_entity_permissions_on_user(
            calling_user_role, None, requested_user_role, new_requested_user_permissions=[Permission.READ]
        )
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            None,
            requested_user_role,
            new_requested_user_permissions=[Permission.READ, Permission.USER],
        )
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            None,
            requested_user_role,
            new_requested_user_permissions=[Permission.READ, Permission.AGENCY_SPEND_MARGIN],
        )

        #  This is not allowed because calling_user hasn't got BUDGET permission
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            None,
            requested_user_role,
            new_requested_user_permissions=DEFAULT_PERMISSIONS + [Permission.BUDGET],
            expect_failure=True,
        )
        #  This is not allowed because calling_user hasn't got MEDIA_COST_DATA_COST_LICENCE_FEE permission
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            None,
            requested_user_role,
            new_requested_user_permissions=DEFAULT_PERMISSIONS + [Permission.MEDIA_COST_DATA_COST_LICENCE_FEE],
            expect_failure=True,
        )

    def _test_is_change_allowed_case(
        self, calling_user_role, old_requested_user_role, new_requested_user_role, expect_failure=False
    ):
        self._test_set_entity_permissions_on_user(
            calling_user_role, old_requested_user_role, new_requested_user_role, expect_failure=expect_failure
        )

    def _test_change_level_with_disallowed_permissions_case(
        self, calling_user_role, old_requested_user_role, new_requested_user_role
    ):
        #  This is ok, the calling_user can change the level of requested_user, even if requested_user has some permission that calling_user hasn't got
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            old_requested_user_role,
            new_requested_user_role,
            old_requested_user_permissions=DEFAULT_PERMISSIONS + [Permission.BUDGET],
            expect_failure=False,
        )
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            old_requested_user_role,
            new_requested_user_role,
            old_requested_user_permissions=DEFAULT_PERMISSIONS + [Permission.MEDIA_COST_DATA_COST_LICENCE_FEE],
            expect_failure=False,
        )
        #  This is not ok, because the calling_user can't assign to requested_user some permission that he does not have
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            old_requested_user_role,
            new_requested_user_role,
            new_requested_user_permissions=DEFAULT_PERMISSIONS + [Permission.BUDGET],
            expect_failure=True,
        )
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            old_requested_user_role,
            new_requested_user_role,
            new_requested_user_permissions=DEFAULT_PERMISSIONS + [Permission.MEDIA_COST_DATA_COST_LICENCE_FEE],
            expect_failure=True,
        )

    def _test_add_permission_case(self, calling_user_role, requested_user_role):
        #  Ok, calling_user can add a permission that he has to requested_user
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[Permission.READ, Permission.WRITE],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE, Permission.USER],
            expect_failure=False,
        )
        #  Ok, calling_user can add a reporting permission that he has to requested_user
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[Permission.READ, Permission.WRITE],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE, Permission.AGENCY_SPEND_MARGIN],
            expect_failure=False,
        )
        #  calling_user can't add a permission that he hasn't got to requested_user
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[Permission.READ, Permission.WRITE],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE, Permission.BUDGET_MARGIN],
            expect_failure=True,
        )
        #  calling_user can't add a reporting permission that he hasn't got to requested_user
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[Permission.READ, Permission.WRITE],
            new_requested_user_permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
            ],
            expect_failure=True,
        )

    def _test_remove_permission_case(self, calling_user_role, requested_user_role):
        #  Ok, calling_user can remove a permission that he has from requested_user
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[Permission.READ, Permission.WRITE, Permission.USER],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE],
            expect_failure=False,
        )
        #  Ok, calling_user can remove a reporting permission that he has from requested_user
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[Permission.READ, Permission.WRITE, Permission.AGENCY_SPEND_MARGIN],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE],
            expect_failure=False,
        )
        #  calling_user can't remove a permission that he hasn't got from requested_user
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[Permission.READ, Permission.WRITE, Permission.BUDGET_MARGIN],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE],
            expect_failure=True,
        )

        #  This is a complicated case. calling_user can't remove MEDIA_COST_DATA_COST_LICENCE_FEE from requested_user
        #  But when he retrieves requested_user's data, he doesn't even see this permission
        #  So when he posts the changed data without this permission, this doesn't mean this is a removal
        #  So the result should be that there is no error, and requested_user still has MEDIA_COST_DATA_COST_LICENCE_FEE
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
            ],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE, Permission.AGENCY_SPEND_MARGIN],
            actual_new_requested_user_permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
            ],
            expect_failure=False,
        )

        #  calling_user can't remove AGENCY_SPEND_MARGIN from requested_user, because requested_user also has
        #  MEDIA_COST_DATA_COST_LICENCE_FEE, which the calling_user can't see and removing AGENCY_SPEND_MARGIN would
        #  cause an illegal state
        self._test_set_entity_permissions_on_user(
            calling_user_role,
            requested_user_role,
            requested_user_role,
            old_requested_user_permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
            ],
            new_requested_user_permissions=[Permission.READ, Permission.WRITE],
            expect_failure=True,
        )

    def _test_set_entity_permissions_on_user(
        self,
        calling_user_role,
        old_requested_user_role,
        new_requested_user_role,
        calling_user_permissions=DEFAULT_PERMISSIONS,
        old_requested_user_permissions=DEFAULT_PERMISSIONS,
        new_requested_user_permissions=DEFAULT_PERMISSIONS,
        actual_new_requested_user_permissions=None,
        expect_failure=False,
    ):
        #  new_requested_user_permissions = what the user posted
        #  actual_new_requested_user_permissions = All of the permissions that we expect to be in the DB afterwards
        #  The difference can come from the requested_user having some hidden reporting permission that
        #  the calling_user can't see
        if actual_new_requested_user_permissions is None:
            actual_new_requested_user_permissions = new_requested_user_permissions

        calling_user, requested_user = self._setup_test_users(old_requested_user_role, new_requested_user_role)
        account, agency = self._prepare_callers_permissions(calling_user, calling_user_role, calling_user_permissions)

        self._grant_access(requested_user, old_requested_user_role, account, agency, old_requested_user_permissions)

        #  If the requested_user is not an internal user, we give him some extra permissions on some other agencies
        #  If the user is promoted to an internal user, all of these permissions must be deleted
        #  Otherwise, they must remain as they were
        if old_requested_user_role != "internal_usr":
            other_agency_1 = self.mix_agency(user=requested_user)
            other_agency_1_account = self.mix_account(user=requested_user, agency=other_agency_1)
            self._grant_access(requested_user, "account_mgr", other_agency_1_account, other_agency_1)
            other_agency_2 = self.mix_agency(user=requested_user)
            self._grant_access(requested_user, "agency_mgr", None, other_agency_2)

        new_permissions = self._prepare_new_permissions(
            new_requested_user_role, account, agency, new_requested_user_permissions
        )
        request = magic_mixer.blend_request_user()
        request.user = calling_user

        if not expect_failure:
            set_entity_permissions_on_user(requested_user, request, account, agency, new_permissions)
            self._validate_permissions(
                requested_user,
                old_requested_user_role,
                new_requested_user_role,
                account,
                agency,
                actual_new_requested_user_permissions,
            )
        else:
            with self.assertRaises((EntityPermissionChangeNotAllowed, MissingRequiredPermission)):
                set_entity_permissions_on_user(requested_user, request, account, agency, new_permissions)

    def _setup_test_users(self, old_requested_user_role, new_requested_user_role):
        calling_user: zemauth.models.User = self.user
        if old_requested_user_role == "internal_usr" or new_requested_user_role == "internal_usr":
            requested_user = magic_mixer.blend(
                zemauth.models.User, email=str(random.randint(0, 100000)) + "@outbrain.com"
            )
        else:
            requested_user = magic_mixer.blend(zemauth.models.User)

        return calling_user, requested_user

    def _prepare_callers_permissions(self, user, role, permissions=DEFAULT_PERMISSIONS):
        agency = self.mix_agency(user=user)
        account = self.mix_account(user=user, agency=agency)

        self._grant_access(user, role, account, agency, permissions)
        return account, agency

    def _grant_access(self, user, role, account, agency, permissions=DEFAULT_PERMISSIONS):
        if role is None:
            return []

        permission_account, permission_agency = self._prepare_permission_attributes(account, agency, role)

        return [
            magic_mixer.blend(
                zemauth.models.EntityPermission,
                user=user,
                agency=permission_agency,
                account=permission_account,
                permission=permission,
            )
            for permission in permissions
        ]

    def _prepare_permission_attributes(self, account, agency, role):
        permission_agency = None
        permission_account = None
        if role == "agency_mgr":
            if agency is None:
                raise Exception("agency_mgr test set up incorrectly")
            permission_agency = agency
        elif role == "account_mgr":
            if account is None:
                raise Exception("account_mgr test set up incorrectly")
            permission_account = account
        return permission_account, permission_agency

    def _prepare_new_permissions(self, role, account, agency, permissions=DEFAULT_PERMISSIONS):
        permission_account, permission_agency = self._prepare_permission_attributes(account, agency, role)

        return [
            {"agency": permission_agency, "account": permission_account, "permission": permission}
            for permission in permissions
        ]

    def _validate_permissions(self, user, old_role, new_role, account, agency, permissions=DEFAULT_PERMISSIONS):
        permission_account, permission_agency = self._prepare_permission_attributes(account, agency, new_role)
        expected_permissions = [
            zemauth.models.EntityPermission(
                user=user, agency=permission_agency, account=permission_account, permission=permission
            )
            for permission in permissions
        ]

        this_scope_query_conditions = (Q(agency=None) & Q(account=None)) | Q(agency=agency) | Q(account__agency=agency)
        this_scope_permissions = list(user.entitypermission_set.filter(this_scope_query_conditions))
        self.assertCountEqual(this_scope_permissions, expected_permissions)

        if old_role != "internal_usr":
            other_permissions_count = len(user.entitypermission_set.filter(~Q(this_scope_query_conditions)))
            if new_role == "internal_usr":
                self.assertEqual(other_permissions_count, 0)
            else:
                #  We added 3 permissions to other_agency_1_account and 3 permissions to other_agency_2
                #  Here we make sure they are still there
                self.assertEqual(other_permissions_count, len(DEFAULT_PERMISSIONS) * 2)
