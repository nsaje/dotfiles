from django import test
from mock import patch

import core.models
import utils.exc
from utils.magic_mixer import magic_mixer

from . import exceptions


class AccountSettingsInstanceTestCase(test.TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)

    def test_update(self):
        initial = {"name": "abc"}
        self.account.settings.update(None, **initial)
        user_changes = {"name": "abc2"}
        applied_changes = self.account.settings.update(None, **user_changes)
        expected_changes = {"name": "abc2"}
        self.assertEqual(applied_changes, expected_changes)

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

    def test_update_default_icon(self):
        account = magic_mixer.blend(core.models.Account)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", image_hash="icon_hash", width=150, height=150, file_size=1000
        )
        account.settings.update(None, default_icon=default_icon)

        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(150, account.settings.default_icon.width)
        self.assertEqual(150, account.settings.default_icon.height)
        self.assertEqual(1000, account.settings.default_icon.file_size)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset,
            image_id="icon_id2",
            image_hash="icon_hash2",
            width=151,
            height=151,
            file_size=1001,
            origin_url="http://origin.com",
        )
        account.settings.update(None, default_icon=default_icon)

        self.assertEqual("icon_id2", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash2", account.settings.default_icon.image_hash)
        self.assertEqual(151, account.settings.default_icon.width)
        self.assertEqual(151, account.settings.default_icon.height)
        self.assertEqual(1001, account.settings.default_icon.file_size)
        self.assertEqual("http://origin.com", account.settings.default_icon.origin_url)

    def test_update_default_icon_not_square(self):
        account = magic_mixer.blend(core.models.Account)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", image_hash="icon_hash", width=151, height=150, file_size=1000
        )
        with self.assertRaises(exceptions.DefaultIconNotSquare):
            account.settings.update(None, default_icon=default_icon)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", image_hash="icon_hash", width=149, height=150, file_size=1000
        )
        with self.assertRaises(exceptions.DefaultIconNotSquare):
            account.settings.update(None, default_icon=default_icon)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, id="icon_id", image_hash="icon_hash", width=150, height=150, file_size=1000
        )
        self.account.settings.update(None, default_icon=default_icon)

    def test_update_default_icon_too_small(self):
        account = magic_mixer.blend(core.models.Account)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", image_hash="icon_hash", width=127, height=127, file_size=1000
        )
        with self.assertRaises(exceptions.DefaultIconTooSmall):
            account.settings.update(None, default_icon=default_icon)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, id="icon_id", image_hash="icon_hash", width=128, height=128, file_size=1000
        )
        self.account.settings.update(None, default_icon=default_icon)

    def test_update_default_icon_too_big(self):
        account = magic_mixer.blend(core.models.Account)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset,
            image_id="icon_id",
            image_hash="icon_hash",
            width=10001,
            height=10001,
            file_size=1000,
        )
        with self.assertRaises(exceptions.DefaultIconTooBig):
            account.settings.update(None, default_icon=default_icon)

        default_icon = magic_mixer.blend(
            core.models.ImageAsset, id="icon_id", image_hash="icon_hash", width=9999, height=9999, file_size=1000
        )
        self.account.settings.update(None, default_icon=default_icon)
