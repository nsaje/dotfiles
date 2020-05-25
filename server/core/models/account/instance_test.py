from django.test import TestCase

import dash.constants
from utils.magic_mixer import magic_mixer

from .model import Account


class AccountInstanceTestCase(TestCase):
    def test_archive_restore(self):
        request = magic_mixer.blend_request_user()

        account = Account.objects.create(request, name="Test", agency=None, currency=dash.constants.Currency.EUR)
        self.assertFalse(account.archived)
        self.assertFalse(account.settings.archived)

        account.archive(request)
        self.assertTrue(account.archived)
        self.assertTrue(account.settings.archived)

        account.restore(request)
        self.assertFalse(account.archived)
        self.assertFalse(account.settings.archived)
