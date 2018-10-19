from django import test
from django.test import RequestFactory

from zemauth import models
from zemauth import backends


class EmailOrUsernameModelBackendTestCase(test.TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get("/")

    def test_authenticate_email(self):
        email = "foo@bar.com"
        password = "123"

        user = models.User.objects.create_user(email, password=password)
        user.save()

        backend = backends.EmailOrUsernameModelBackend()

        result = backend.authenticate(self.request, email, password)
        self.assertEqual(result, user)

        result2 = backend.authenticate(self.request, "FOO@bar.com", password)
        self.assertEqual(result2, user)

    def test_authenticate_username(self):
        username = "foo"
        email = "foo@bar.com"
        password = "123"

        user = models.User.objects.create_user(email, username=username, password=password)
        user.save()

        backend = backends.EmailOrUsernameModelBackend()

        result = backend.authenticate(self.request, username, password)
        self.assertEqual(result, user)

        result2 = backend.authenticate(self.request, "FOO", password)
        self.assertIs(result2, None)

    def test_authenticate_wrong_password(self):
        email = "foo@bar.com"

        user = models.User.objects.create_user(email, password="123")
        user.save()

        backend = backends.EmailOrUsernameModelBackend()
        result = backend.authenticate(self.request, email, "456")

        self.assertIsNone(result)

    def test_authenticate_oauth(self):
        email = "test.user@zemanta.com"

        user = models.User.objects.create_user(email, password="123")
        user.save()

        oauth_data = {
            "family_name": "",
            "name": "",
            "picture": "",
            "email": "test.user@zemanta.com",
            "given_name": "",
            "id": "111111111111111111111",
            "hd": "zemanta.com",
            "verified_email": True,
        }

        with self.settings(GOOGLE_OAUTH_ENABLED=True):
            backend = backends.EmailOrUsernameModelBackend()
            result = backend.authenticate(self.request, oauth_data=oauth_data)
            self.assertEqual(result, user)

            unverified = oauth_data.copy()
            unverified["verified_email"] = False
            result = backend.authenticate(self.request, oauth_data=unverified)
            self.assertIs(result, None)

            wrong_email = oauth_data.copy()
            wrong_email["email"] = "non-existing@zemanta.com"
            result = backend.authenticate(self.request, oauth_data=wrong_email)
            self.assertIs(result, None)

            user.email = "user@not-zemanta.com"
            user.save()
            result = backend.authenticate(self.request, oauth_data=oauth_data)
            self.assertEqual(result, None)

    def test_authenticate_internal_user(self):
        email = "test.user@zemanta.com"

        user = models.User.objects.create_user(email, password="123")
        user.save()

        with self.settings(GOOGLE_OAUTH_ENABLED=True):
            backend = backends.EmailOrUsernameModelBackend()
            result = backend.authenticate(
                self.request, username="test.user@zemanta.com", password="123", oauth_data=None
            )
            self.assertEqual(result, None)

        with self.settings(GOOGLE_OAUTH_ENABLED=False):
            backend = backends.EmailOrUsernameModelBackend()
            result = backend.authenticate(
                self.request, username="test.user@zemanta.com", password="123", oauth_data=None
            )
            self.assertEqual(result, user)

    def test_authenticate_non_existing(self):
        backend = backends.EmailOrUsernameModelBackend()
        result = backend.authenticate(self.request, "foo@bar.com", "456")

        self.assertIsNone(result)

    def test_get_user(self):
        email = "foo@bar.com"
        password = "123"

        user = models.User.objects.create_user(email, password=password)

        user.save()

        backend = backends.EmailOrUsernameModelBackend()
        result = backend.get_user(user.pk)

        self.assertEqual(result, user)

    def test_get_user_non_existing(self):
        backend = backends.EmailOrUsernameModelBackend()
        result = backend.get_user(123)

        self.assertIsNone(result)
