from django.test import TestCase

import core
import zemauth
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission
from zemauth.models.user.exceptions import InvalidUser
from zemauth.models.user.exceptions import MissingReadPermission
from zemauth.models.user.exceptions import MissingRequiredPermission
from zemauth.models.user.exceptions import MixedPermissionLevels


class EntityPermissionValidationMixinTestCase(TestCase):
    def test_validate_entity_permissions_agency(self):
        agency = magic_mixer.blend(core.models.Agency)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [
            self._prepare_entity_permission(None, agency, Permission.READ),
            self._prepare_entity_permission(None, agency, Permission.BUDGET),
        ]

        requested_user.validate_entity_permissions(entity_permissions)

    def test_validate_entity_permissions_account(self):
        account = magic_mixer.blend(core.models.Account)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [
            self._prepare_entity_permission(account, None, Permission.READ),
            self._prepare_entity_permission(account, None, Permission.BUDGET),
        ]

        requested_user.validate_entity_permissions(entity_permissions)

    def test_validate_entity_permissions_internal_nonoutbrain(self):
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [self._prepare_entity_permission(None, None, Permission.READ)]

        self.assertRaises(
            InvalidUser, requested_user.validate_entity_permissions, entity_permissions=entity_permissions
        )

    def test_validate_entity_permissions_agency_and_account(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [
            self._prepare_entity_permission(account, None, Permission.READ),
            self._prepare_entity_permission(None, agency, Permission.BUDGET),
        ]

        self.assertRaises(
            MixedPermissionLevels, requested_user.validate_entity_permissions, entity_permissions=entity_permissions
        )

    def test_validate_entity_permissions_agency_and_internal(self):
        agency = magic_mixer.blend(core.models.Agency)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User, email="test@outbrain.com")

        entity_permissions = [
            self._prepare_entity_permission(None, None, Permission.READ),
            self._prepare_entity_permission(None, agency, Permission.READ),
        ]

        self.assertRaises(
            MixedPermissionLevels, requested_user.validate_entity_permissions, entity_permissions=entity_permissions
        )

    def test_validate_entity_permissions_agency_and_account2(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [self._prepare_entity_permission(account, agency, Permission.READ)]

        self.assertRaises(
            MixedPermissionLevels, requested_user.validate_entity_permissions, entity_permissions=entity_permissions
        )

    def test_validate_entity_permissions_no_read(self):
        agency = magic_mixer.blend(core.models.Agency)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [self._prepare_entity_permission(None, agency, Permission.BUDGET)]

        self.assertRaises(
            MissingReadPermission, requested_user.validate_entity_permissions, entity_permissions=entity_permissions
        )

    def test_validate_entity_permissions_no_agency_spend(self):
        agency = magic_mixer.blend(core.models.Agency)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [
            self._prepare_entity_permission(None, agency, Permission.READ),
            self._prepare_entity_permission(None, agency, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE),
        ]

        self.assertRaises(
            MissingRequiredPermission, requested_user.validate_entity_permissions, entity_permissions=entity_permissions
        )

    def test_validate_entity_permissions_no_media_cost(self):
        agency = magic_mixer.blend(core.models.Agency)
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [
            self._prepare_entity_permission(None, agency, Permission.READ),
            self._prepare_entity_permission(None, agency, Permission.BASE_COSTS_SERVICE_FEE),
        ]

        self.assertRaises(
            MissingRequiredPermission, requested_user.validate_entity_permissions, entity_permissions=entity_permissions
        )

    def _prepare_entity_permission(self, account, agency, permission):
        return zemauth.models.EntityPermission(account=account, agency=agency, permission=permission)
