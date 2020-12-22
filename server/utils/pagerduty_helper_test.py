import datetime

from django.test import TestCase
from django.test import override_settings
from mock import ANY
from mock import patch

from utils import pagerduty_helper


@override_settings(
    HOSTNAME="testhost",
    PAGER_DUTY_ENABLED=True,
    PAGER_DUTY_URL="http://pagerduty.example.com",
    PAGER_DUTY_ENGINEERS_SERVICE_KEY="123abc",
)
class PagerDutyHelperTestCase(TestCase):
    @patch("utils.pagerduty_helper.requests.post")
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

    @patch("utils.pagerduty_helper.requests.post")
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

    @patch("utils.pagerduty_helper._call_api")
    def test_list_active_incidents(self, mock_call_api):
        data = {
            "incidents": [
                {
                    "assignments": [{"assignee": {"id": "ABCDEF"}}],
                    "created_at": "2020-12-01T12:13:14Z",
                    "title": "My incident",
                    "html_url": "http://example.com/myincident",
                },
                {
                    "assignments": [{"assignee": {"id": "XYZDEF"}}],
                    "created_at": "2020-12-02T12:13:14Z",
                    "title": "My incident 2",
                    "html_url": "http://example.com/myincident2",
                },
            ]
        }
        mock_call_api.return_value = data
        active_incidents = pagerduty_helper.list_active_incidents()
        mock_call_api.assert_called_with(
            "GET",
            "/incidents",
            {"statuses[]": ["triggered", "acknowledged"], "team_ids[]": [pagerduty_helper.Z1_TEAM_ID]},
        )
        self.assertEqual(
            active_incidents,
            [
                pagerduty_helper.PagerDutyIncident(
                    title="My incident",
                    url="http://example.com/myincident",
                    assignee_id="ABCDEF",
                    created_at=datetime.datetime(2020, 12, 1, 12, 13, 14),
                ),
                pagerduty_helper.PagerDutyIncident(
                    title="My incident 2",
                    url="http://example.com/myincident2",
                    assignee_id="XYZDEF",
                    created_at=datetime.datetime(2020, 12, 2, 12, 13, 14),
                ),
            ],
        )

    @patch("utils.pagerduty_helper._call_api")
    def test_get_on_call_user(self, mock_call_api):
        data = {
            "users": [
                {"name": "Person A", "email": "persona@example.com"},
                {"name": "Person A", "email": "persona@example.com"},
            ]
        }
        mock_call_api.return_value = data
        user = pagerduty_helper.get_on_call_user()
        mock_call_api.assert_called_with("GET", "/schedules/" + pagerduty_helper.Z1_TEAM_SCHEDULE_ID + "/users", ANY)
        self.assertEqual(user, pagerduty_helper.PagerDutyUser(name="Person A", email="persona@example.com"))

    @patch("utils.pagerduty_helper._call_api")
    def test_get_user(self, mock_call_api):
        data = {"user": {"name": "Person A", "email": "persona@example.com"}}
        mock_call_api.return_value = data
        user = pagerduty_helper.get_user("ABCDEF")
        mock_call_api.assert_called_with("GET", "/users/ABCDEF", ANY)
        self.assertEqual(user, pagerduty_helper.PagerDutyUser(name="Person A", email="persona@example.com"))
