from django.test import TestCase
from django.test import override_settings
from mock import patch

from core import models
from utils import k1_helper
from utils.magic_mixer import magic_mixer


@override_settings(
    K1_CONSISTENCY_PING_ACCOUNT_QUEUE="ping_account_queue",
    K1_CONSISTENCY_PING_AD_GROUP_QUEUE="ping_ad_group_queue",
    K1_CONSISTENCY_PING_CONTENT_AD_QUEUE="ping_content_ad_queue",
    K1_CONSISTENCY_PING_BLACKLIST_QUEUE="ping_blacklist_queue",
)
@patch("utils.k1_helper.app")
class K1HelperTest(TestCase):
    def setUp(self):
        patcher = patch.object(k1_helper.time, "time", return_value=1513594339.172575)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_update_account(self, mock_app):
        account = magic_mixer.blend(models.Account, id=123)
        k1_helper.update_account(account, msg="test")
        mock_app.send_task.assert_called_once_with(
            "consistency_ping_account",
            queue="ping_account_queue",
            ignore_result=True,
            kwargs={"msg": "test", "account_id": 123, "initiated_at": 1513594339.172575, "priority": False},
        )

    def test_update_ad_group(self, mock_app):
        ad_group = magic_mixer.blend(models.AdGroup, id=123, campaign__account__id=789)
        k1_helper.update_ad_group(ad_group, msg="test")
        mock_app.send_task.assert_called_once_with(
            "consistency_ping_ad_group",
            queue="ping_ad_group_queue",
            ignore_result=True,
            kwargs={
                "msg": "test",
                "account_id": 789,
                "ad_group_id": 123,
                "initiated_at": 1513594339.172575,
                "priority": False,
            },
        )

    def test_update_content_ad(self, mock_app):
        content_ad = magic_mixer.blend(models.ContentAd, ad_group__campaign__account__id=789, ad_group__id=123, id=456)
        k1_helper.update_content_ad(content_ad, msg="test")
        mock_app.send_task.assert_called_once_with(
            "consistency_ping_content_ad",
            queue="ping_content_ad_queue",
            ignore_result=True,
            kwargs={
                "msg": "test",
                "account_id": 789,
                "ad_group_id": 123,
                "content_ad_id": 456,
                "initiated_at": 1513594339.172575,
                "priority": False,
            },
        )

    def test_update_blacklist(self, mock_app):
        ad_group = magic_mixer.blend(models.AdGroup, id=123)
        k1_helper.update_blacklist(ad_group, msg="test")
        mock_app.send_task.assert_called_once_with(
            "consistency_ping_blacklist",
            queue="ping_blacklist_queue",
            ignore_result=True,
            kwargs={"msg": "test", "ad_group_id": 123, "initiated_at": 1513594339.172575, "priority": False},
        )
