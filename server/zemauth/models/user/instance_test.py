# -*- coding: utf-8 -*-

from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase

from .model import User


class InstanceTestCase(TestCase):
    fixtures = ["test_users.yaml"]

    def test_get_full_name(self):
        user = User(email="test@test.com", first_name="John", last_name="Doe")
        self.assertEqual(user.get_full_name(), "John Doe")

        user = User(email="test@test.com", last_name="Doe")
        self.assertEqual(user.get_full_name(), "Doe")

    def test_get_short_name(self):
        user = User(email="test@test.com", first_name="John", last_name="Doe")
        self.assertEqual(user.get_short_name(), "John")

    def test_unique_email(self):
        email = "test@test.com"
        with transaction.atomic():
            User.objects.create_user(email)

        with transaction.atomic():
            self.assertEqual(len(User.objects.filter(email=email).all()), 1)

            with self.assertRaises(IntegrityError):
                User.objects.create_user(email)

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                User.objects.create_user("TEST@test.com")

    def test_superuser_permissions(self):
        user = User.objects.get(pk=1)
        permissions = user.get_all_permissions_with_access_levels()

        self.assertFalse(permissions["test.internal_permission_1"])
        self.assertFalse(permissions["test.internal_permission_2"])
        self.assertTrue(permissions["test.public_permission_1"])
        self.assertTrue(permissions["test.public_permission_2"])

    def test_normal_user_permissions(self):
        user = User.objects.get(pk=2)
        permissions = user.get_all_permissions_with_access_levels()

        self.assertFalse("test.internal_permission_1" in permissions)
        self.assertFalse("test.internal_permission_2" in permissions)
        self.assertTrue(permissions["test.public_permission_1"])
        self.assertTrue(permissions["test.public_permission_2"])

    def test_inactive_user_permissions(self):
        user = User.objects.get(pk=2)
        user.is_active = False
        permissions = user.get_all_permissions_with_access_levels()

        self.assertEqual(permissions, {})

    def test_user_permissions_cache(self):
        user = User.objects.get(pk=1)
        permissions = user.get_all_permissions_with_access_levels()

        # Basic check that some permissions were returned
        self.assertFalse(permissions["test.internal_permission_1"])
        self.assertFalse(permissions["test.internal_permission_2"])
        self.assertTrue(permissions["test.public_permission_1"])
        self.assertTrue(permissions["test.public_permission_2"])

        permissions2 = user.get_all_permissions_with_access_levels()
        self.assertEqual(permissions2, permissions)
