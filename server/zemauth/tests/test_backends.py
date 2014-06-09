import unittest

from zemauth import models
from zemauth import backends


class EmailOrUsernameModelBackendTestCase(unittest.TestCase):
    def test_authenticate(self):
        email = 'foo@bar.com'
        password = '123'

        user = models.User.objects.create_user(email, password=password)
        user.save()

        backend = backends.EmailOrUsernameModelBackend()

        result = backend.authenticate(email, password)

        self.assertEqual(result, user)
