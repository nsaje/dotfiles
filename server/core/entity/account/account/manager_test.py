from django.test import TestCase

import core.source
from .model import Account

from utils.magic_mixer import magic_mixer


class AccountManagerTestCase(TestCase):

    def test_create_add_allowed_sources(self):
        source_released = magic_mixer.blend(core.source.Source, released=True)
        source_unreleased = magic_mixer.blend(core.source.Source, released=False)

        request = magic_mixer.blend_request_user()
        account = Account.objects.create(
            request,
            name='Test',
            agency=None,
        )

        self.assertTrue(source_released in account.allowed_sources.all())
        self.assertFalse(source_unreleased in account.allowed_sources.all())
