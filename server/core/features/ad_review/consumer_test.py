from unittest import mock

from utils.base_test_case import BaseTestCase

from . import consumer
from . import realtimechanges


def get_fake_notification(notification_type=None, changes=None, entity_id=None):
    return {
        "class": "com.outbrain.amplifydatums.AdChangeNotification",
        "userName": "mwillaert",
        "applicationName": "GateKeeperServer",
        "type": notification_type or "UPDATE",
        "entityProperties": {
            "TEXT": {"value": "Aldi is urgently Hiring for various positions."},
            "DOCUMENT_ID": {"value": ["java.lang.Long", 3099877917]},
            "CAMPAIGN_ID": {"value": 1014206514},
            "ENABLED": {"value": True},
            "ID": {"value": entity_id or 185697454},
            "CREATOR": {"value": "AA_barnaby"},
            "IMAGE_UUID": {"value": "b3111de8e3e3b0f9b9f9139edc692047bb26572620c7e45c4ddb1ee576e180b2"},
            "STATUS": {"value": "REJECTED_MANUALLY_MISSING_PRIVACY_POLICY_SECTION"},
            "ARCHIVED": {"value": False},
            "IS_CUSTOM_IMAGE": {"value": True},
            "MARKETER_TYPE": {"value": None},
            "URL": {"value": "https://bestlocaljob.com/outbrain/index.php?jtype=AlDI&start=0"},
        },
        "valuesBeforeChange": {"STATUS": {"value": "PENDING"}},
        "valuesAfterChange": {"STATUS": {"value": "REJECTED_MANUALLY_MISSING_PRIVACY_POLICY_SECTION"}},
        "changes": [{"name": "STATUS"}] if changes is None else changes,
        "isInternalUser": True,
        "isApplicativeUser": False,
        "uuid": "78343af3-a9e4-45d2-9e5b-78145343cb5b",
        "timestamp": 1602787069788,
        "internalUser": True,
        "applicativeUser": False,
    }


class TestCase(BaseTestCase):
    @mock.patch.object(realtimechanges, "ping_ad_if_relevant")
    def test_process_notification(self, mock_service_ping):
        notification = get_fake_notification(notification_type="UPDATE", changes=[{"name": "STATUS"}], entity_id=123)
        consumer.process_notification(notification)
        mock_service_ping.assert_called_with(123)

    @mock.patch.object(realtimechanges, "ping_ad_if_relevant")
    def test_process_notification_wrong_type(self, mock_service_ping):
        notification = get_fake_notification(notification_type="CREATE", changes=[{"name": "STATUS"}], entity_id=123)
        consumer.process_notification(notification)
        mock_service_ping.assert_not_called()

    @mock.patch.object(realtimechanges, "ping_ad_if_relevant")
    def test_process_notification_wrong_change(self, mock_service_ping):
        notification = get_fake_notification(notification_type="UPDATE", changes=[{"enabled": True}], entity_id=123)
        consumer.process_notification(notification)
        mock_service_ping.assert_not_called()
