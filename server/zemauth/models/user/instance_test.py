# -*- coding: utf-8 -*-

from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase

import zemauth
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import constants
from . import exceptions
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

    def test_update_name(self):
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)
        requested_user.update(first_name="Test", last_name="User")
        self.assertEqual(requested_user.first_name, "Test")
        self.assertEqual(requested_user.last_name, "User")

    def test_update_country(self):
        user = magic_mixer.blend_user()
        user.update(country="SI")
        self.assertEqual(user.country, "SI")
        with self.assertRaises(exceptions.InvalidCountry):
            user.update(country="Slovenia")

    def test_update_company_type(self):
        user = magic_mixer.blend_user()
        user.update(company_type=constants.CompanyType.AGENCY)
        self.assertEqual(user.company_type, constants.CompanyType.AGENCY)
        with self.assertRaises(exceptions.InvalidCompanyType):
            user.update(company_type="invalid")

    def test_update_start_year_of_experience(self):
        user = magic_mixer.blend_user()
        year = dates_helper.local_today().year - 1
        user.update(start_year_of_experience=year)
        self.assertEqual(user.start_year_of_experience, year)
        with self.assertRaises(exceptions.InvalidStartYearOfExperience):
            user.update(start_year_of_experience=constants.START_YEAR - 1)

    def test_update_status(self):
        user = magic_mixer.blend_user()
        user.update(status=constants.Status.ACTIVE)
        self.assertEqual(user.status, constants.Status.ACTIVE)
