import unittest

from zemauth import models
from zemauth import backends


class EmailOrUsernameModelBackendTestCase(unittest.TestCase):
    def test_authenticate_email(self):
        email = 'foo@bar.com'
        password = '123'

        user = models.User.objects.create_user(email, password=password)
        user.save()

        backend = backends.EmailOrUsernameModelBackend()
        result = backend.authenticate(email, password)

        self.assertEqual(result, user)

        user.delete()

    def test_authenticate_username(self):
        username = 'foo'
        email = 'foo@bar.com'
        password = '123'

        user = models.User.objects.create_user(email, username=username, password=password)
        user.save()

        backend = backends.EmailOrUsernameModelBackend()
        result = backend.authenticate(username, password)

        self.assertEqual(result, user)

        user.delete()

    def test_authenticate_wrong_password(self):
        email = 'foo@bar.com'

        user = models.User.objects.create_user(email, password='123')
        user.save()

        backend = backends.EmailOrUsernameModelBackend()
        result = backend.authenticate(email, '456')

        self.assertIsNone(result)

        user.delete()

    def test_authenticate_non_existing(self):
        backend = backends.EmailOrUsernameModelBackend()
        result = backend.authenticate('foo@bar.com', '456')

        self.assertIsNone(result)

    def test_get_user(self):
        email = 'foo@bar.com'
        password = '123'

        user = models.User.objects.create_user(email, password=password)

        user.save()

        backend = backends.EmailOrUsernameModelBackend()
        result = backend.get_user(user.pk)

        self.assertEqual(result, user)

        user.delete()

    def test_get_user_non_existing(self):
        backend = backends.EmailOrUsernameModelBackend()
        result = backend.get_user(123)

        self.assertIsNone(result)
