# -*- coding: utf-8 -*-

from django.test import TestCase

import core.models
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer

from .constants import Permission
from .model import EntityPermission


class EntityPermissionManagerTestCase(TestCase):
    def test_create(self):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency)
        permission = Permission.READ

        entity_permission = EntityPermission.objects.create(user, permission, agency=agency)

        self.assertIsNotNone(entity_permission.pk)
        self.assertEqual(entity_permission.agency_id, agency.id)
        self.assertIsNone(entity_permission.account_id)
        self.assertEqual(entity_permission.permission, permission)

    def test_create_with_agency_and_account(self):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account)
        permission = Permission.READ

        with self.assertRaises(ValidationError):
            EntityPermission.objects.create(user, permission, agency=agency, account=account)

    def test_get_or_create(self):
        user = magic_mixer.blend_user()
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account)
        permission = Permission.READ

        entity_permission = EntityPermission.objects.create(user, permission, agency=agency)
        entity_permission_duplicate = EntityPermission.objects.create(user, permission, agency=agency)
        self.assertEqual(entity_permission.id, entity_permission_duplicate.id)

        entity_permission = EntityPermission.objects.create(user, permission, account=account)
        entity_permission_duplicate = EntityPermission.objects.create(user, permission, account=account)
        self.assertEqual(entity_permission.id, entity_permission_duplicate.id)

        entity_permission = EntityPermission.objects.create(user, permission, agency=None, account=None)
        entity_permission_duplicate = EntityPermission.objects.create(user, permission, agency=None, account=None)
        self.assertEqual(entity_permission.id, entity_permission_duplicate.id)
