from django import test
from mock import patch

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class AccountSettingsTestCase(test.TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)

    def test_update_fields(self):
        self.account.settings.update(None, salesforce_url="test-url")
        self.assertEqual("test-url", self.account.settings.salesforce_url)

        with patch("django.db.models.Model.save") as save_mock:
            self.account.settings.update(None, salesforce_url="new-url")
            save_mock.assert_any_call(update_fields=["salesforce_url", "created_by", "created_dt"])

    def test_publisher_groups(self):
        with self.assertRaises(exceptions.PublisherWhitelistInvalid):
            self.account.settings.update(None, whitelist_publisher_groups=[1])

        with self.assertRaises(exceptions.PublisherBlacklistInvalid):
            self.account.settings.update(None, blacklist_publisher_groups=[2])

    def test_update_name(self):
        self.account.settings.update(None, name="TEST")
        self.account.refresh_from_db()
        self.assertEqual("TEST", self.account.settings.name)
        self.assertEqual("TEST", self.account.name)
