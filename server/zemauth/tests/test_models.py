from django import test

from django.core import mail
from django.db import IntegrityError, transaction

from zemauth import models


class UserManagerTestCase(test.TestCase):
    def test_create_user(self):
        email_lowercase = 'normal@normal.com'
        user = models.User.objects.create_user(email_lowercase, password='123')
        self.assertEqual(user.email, email_lowercase)
        self.assertIs(user.username, u'')
        self.assertTrue(user.has_usable_password())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        email_lowercase = 'normal@normal.com'
        user = models.User.objects.create_superuser(email_lowercase, password='123')
        self.assertEqual(user.email, email_lowercase)
        self.assertIs(user.username, u'')
        self.assertTrue(user.has_usable_password())

    def test_create_user_email_domain_normalize_rfc3696(self):
        # According to  http://tools.ietf.org/html/rfc3696#section-3
        # the "@" symbol can be part of the local part of an email address
        returned = models.UserManager.normalize_email(r'Abc\@DEF@EXAMPLE.com')
        self.assertEqual(returned, r'Abc\@DEF@example.com')

    def test_create_user_email_domain_normalize(self):
        returned = models.UserManager.normalize_email('normal@DOMAIN.COM')
        self.assertEqual(returned, 'normal@domain.com')

    def test_create_user_email_domain_normalize_with_whitespace(self):
        returned = models.UserManager.normalize_email('email\ with_whitespace@D.COM')
        self.assertEqual(returned, 'email\ with_whitespace@d.com')

    def test_empty_email(self):
        self.assertRaises(ValueError, models.User.objects.create_user, email='')

    def test_no_password(self):
        email_lowercase = 'normal@normal.com'
        user = models.User.objects.create_user(email_lowercase)
        self.assertFalse(user.has_usable_password())

        self.assertRaises(
            TypeError,
            models.User.objects.create_superuser,
            email=email_lowercase
        )


class UserTestCase(test.TestCase):
    def test_email_user(self):
        kwargs = {
            "fail_silently": False,
            "auth_user": None,
            "auth_password": None,
            "connection": None,
            "html_message": None,
        }
        user = models.User(email='foo@bar.com')
        user.email_user(
            subject="Subject here",
            message="This is a message",
            from_email="from@domain.com",
            **kwargs
        )
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Subject here")
        self.assertEqual(message.body, "This is a message")
        self.assertEqual(message.from_email, "from@domain.com")
        self.assertEqual(message.to, [user.email])

    def test_get_full_name(self):
        user = models.User(email='test@test.com', first_name='John', last_name='Doe')
        self.assertEqual(user.get_full_name(), 'John Doe')

        user = models.User(email='test@test.com', last_name='Doe')
        self.assertEqual(user.get_full_name(), 'Doe')

    def test_get_short_name(self):
        user = models.User(email='test@test.com', first_name='John', last_name='Doe')
        self.assertEqual(user.get_short_name(), 'John')

    def test_unique_email(self):
        email = 'test@test.com'
        with transaction.atomic():
            user1 = models.User(email=email)
            user1.save()

        with transaction.atomic():
            self.assertEqual(len(models.User.objects.filter(email=email).all()), 1)

            user2 = models.User(email=email)
            self.assertRaises(IntegrityError, user2.save)

        with transaction.atomic():
            user2 = models.User(email='TEST@test.com')
            self.assertRaises(IntegrityError, user2.save)

    # def test_mandatory_email(self):
    #     user = models.User(first_name='Test')
    #     user.save()
