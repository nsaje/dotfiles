from mock import patch

from django.test import TestCase, override_settings

from utils import k1_helper


@override_settings(
    K1_CONSISTENCY_PING_AD_GROUP_QUEUE='ping_ad_group_queue',
    K1_CONSISTENCY_PING_CONTENT_AD_QUEUE='ping_content_ad_queue',
    K1_CONSISTENCY_PING_BLACKLIST_QUEUE='ping_blacklist_queue'
)
@patch('utils.k1_helper.app')
class K1HelperTest(TestCase):
    def test_update_ad_group(self, mock_app):
        k1_helper.update_ad_group(123, msg='test')
        mock_app.send_task.assert_called_once_with(
            'consistency_ping_ad_group',
            queue='ping_ad_group_queue',
            kwargs={
                'msg': 'test',
                'ad_group_id': 123,
            }
        )

    def test_update_content_ad(self, mock_app):
        k1_helper.update_content_ad(123, 456, msg='test')
        mock_app.send_task.assert_called_once_with(
            'consistency_ping_content_ad',
            queue='ping_content_ad_queue',
            kwargs={
                'msg': 'test',
                'ad_group_id': 123,
                'content_ad_id': 456,
            }
        )

    def test_update_blacklist(self, mock_app):
        k1_helper.update_blacklist(123, msg='test')
        mock_app.send_task.assert_called_once_with(
            'consistency_ping_blacklist',
            queue='ping_blacklist_queue',
            kwargs={
                'msg': 'test',
                'ad_group_id': 123,
            }
        )
