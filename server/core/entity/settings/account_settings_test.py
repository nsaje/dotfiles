from mock import patch

from django import test

import core.entity
from utils.magic_mixer import magic_mixer


class AccountSettingsTestCase(test.TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.entity.Account)

    def test_update_fields(self):
        self.account.settings.update(
            None,
            salesforce_url='test-url',
        )
        self.assertEqual(
            'test-url',
            self.account.settings.salesforce_url,
        )

        with patch('django.db.models.Model.save') as save_mock:
            self.account.settings.update(
                None,
                salesforce_url='new-url',
            )
            save_mock.assert_any_call(
                update_fields=['salesforce_url', 'created_by', 'created_dt'])
