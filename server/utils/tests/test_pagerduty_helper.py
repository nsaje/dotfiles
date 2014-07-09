from mock import patch
import json

from django.test import TestCase, override_settings

from utils import pagerduty_helper


@override_settings(
    HOSTNAME='testhost',
    PAGER_DUTY_URL='http://pagerduty.example.com',
    PAGER_DUTY_SERVICE_KEY='123abc'
)
@patch('utils.pagerduty_helper.urllib2.urlopen')
class PagerDutyHelperTestCase(TestCase):
    def test_trigger_event(self, mock_urlopen):
        data = json.dumps({
            'service_key': '123abc',
            'incident_key': 'adgroup_stop_failed',
            'event_type': 'trigger',
            'description': 'Adgroup stop action failed',
            'client': 'Zemanta One - testhost',
            'details': {
                'action_log_admin_url': 'https://one.zemanta.com/admin/actionlog/actionlog/1/',
            }
        })

        pagerduty_helper.trigger_event(1)

        mock_urlopen.assert_called_with('http://pagerduty.example.com', data)
