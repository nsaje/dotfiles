from django import test
from mock import patch

import core.models
import utils.exc
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

    @patch.object(core.models.Campaign, "archive")
    def test_archiving(self, mock_campaign_archive):
        account = magic_mixer.blend(core.models.Account)
        magic_mixer.cycle(10).blend(core.models.Campaign, account=account)
        self.assertFalse(account.archived)
        self.assertFalse(account.settings.archived)

        account.settings.update(None, archived=True)
        self.assertTrue(account.archived)
        self.assertTrue(account.settings.archived)
        self.assertEqual(mock_campaign_archive.call_count, 10)

        account.settings.update(None, archived=True)

        mock_campaign_archive.reset_mock()
        account.settings.update(None, archived=False)
        self.assertFalse(account.archived)
        self.assertFalse(account.settings.archived)
        self.assertEqual(mock_campaign_archive.call_count, 0)

    @patch.object(core.models.Campaign, "can_archive", return_value=False)
    def test_cant_archive_campaign_fail(self, mock_campaign_can_archive):
        account = magic_mixer.blend(core.models.Account)
        magic_mixer.blend(core.models.Campaign, account=account)
        with self.assertRaises(utils.exc.ForbiddenError):
            account.settings.update(None, archived=True)
        self.assertFalse(account.settings.archived)

    def test_update_archived_account(self):
        account = magic_mixer.blend(core.models.Account)
        account.archive(None)
        account.refresh_from_db()
        self.assertTrue(account.archived)
        self.assertTrue(account.settings.archived)
        with self.assertRaises(utils.exc.ForbiddenError):
            account.settings.update(None, name="new name")
        account.settings.update(None, archived=True)
        account.settings.update(None, archived=False)
        account.refresh_from_db()
        self.assertFalse(account.archived)
        self.assertFalse(account.settings.archived)
