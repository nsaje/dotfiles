from django.test import TestCase
from django.test import override_settings
from mock import patch

from utils import pagerduty_helper


@override_settings(
    HOSTNAME="testhost",
    PAGER_DUTY_ENABLED=True,
    PAGER_DUTY_URL="http://pagerduty.example.com",
    PAGER_DUTY_ENGINEERS_SERVICE_KEY="123abc",
)
@patch("utils.pagerduty_helper.requests.post")
class PagerDutyHelperTestCase(TestCase):
    def test_trigger(self, mock_urlopen):
        data = {
            "routing_key": "123abc",
            "dedup_key": "adgroup_stop_failed",
            "event_action": "trigger",
            "payload": {
                "summary": "Adgroup stop action failed",
                "source": "Zemanta One - testhost",
                "severity": pagerduty_helper.PagerDutyEventSeverity.CRITICAL,
                "custom_details": {"action_log_admin_url": "https://one.zemanta.com/admin/actionlog/actionlog/1/"},
            },
        }

        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
            incident_key="adgroup_stop_failed",
            description="Adgroup stop action failed",
            details={"action_log_admin_url": "https://one.zemanta.com/admin/actionlog/actionlog/1/"},
        )

        mock_urlopen.assert_called_with("http://pagerduty.example.com", json=data, timeout=60)

    def test_resolve(self, mock_urlopen):
        data = {
            "routing_key": "123abc",
            "dedup_key": "adgroup_stop_failed",
            "event_action": "resolve",
            "payload": {
                "summary": "Adgroup stop action failed",
                "source": "Zemanta One - testhost",
                "severity": pagerduty_helper.PagerDutyEventSeverity.CRITICAL,
                "custom_details": {"action_log_admin_url": "https://one.zemanta.com/admin/actionlog/actionlog/1/"},
            },
        }

        pagerduty_helper.resolve(
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
            incident_key="adgroup_stop_failed",
            description="Adgroup stop action failed",
            details={"action_log_admin_url": "https://one.zemanta.com/admin/actionlog/actionlog/1/"},
        )

        mock_urlopen.assert_called_with("http://pagerduty.example.com", json=data, timeout=60)
