import django.contrib.auth.models
from django.test import TestCase

import core.models
import zemauth.models
from utils.magic_mixer import magic_mixer

from .constants import Permission
from .service import refresh_entity_permissions_for_user


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
