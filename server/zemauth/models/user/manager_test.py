# -*- coding: utf-8 -*-

from django.test import TestCase

from .model import User


class UserManagerTestCase(TestCase):
    def test_create_user(self):
        email_lowercase = "normal@normal.com"
        user = User.objects.create_user(email_lowercase, password="123")
        self.assertEqual(user.email, email_lowercase)
        self.assertIs(user.username, None)
        self.assertTrue(user.has_usable_password())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        email_lowercase = "normal@normal.com"
        user = User.objects.create_superuser(email_lowercase, password="123")
        self.assertEqual(user.email, email_lowercase)
        self.assertIs(user.username, None)
        self.assertTrue(user.has_usable_password())

    def test_get_or_create_service_user(self):
        user = User.objects.get_or_create_service_user("test-service")
        self.assertEqual(user.username, "test-service")
        self.assertEqual(user.email, "test-service@service.zemanta.com")
        self.assertTrue(user.has_usable_password())
        self.assertEqual(user.password, "")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_service)

    def test_create_user_email_domain_normalize_rfc3696(self):
        # According to  http://tools.ietf.org/html/rfc3696#section-3
        # the "@" symbol can be part of the local part of an email address
        returned = User.objects.normalize_email(r"Abc\@DEF@EXAMPLE.com")
        self.assertEqual(returned, r"Abc\@DEF@example.com")

    def test_create_user_email_domain_normalize(self):
        returned = User.objects.normalize_email("normal@DOMAIN.COM")
        self.assertEqual(returned, "normal@domain.com")

    def test_create_user_email_domain_normalize_with_whitespace(self):
        returned = User.objects.normalize_email("email with_whitespace@D.COM")
        self.assertEqual(returned, "email with_whitespace@d.com")

    def test_empty_email(self):
        self.assertRaises(ValueError, User.objects.create_user, email="")

    def test_no_password(self):
        email_lowercase = "normal@normal.com"
        user = User.objects.create_user(email_lowercase)
        self.assertFalse(user.has_usable_password())

        self.assertRaises(TypeError, User.objects.create_superuser, email=email_lowercase)
