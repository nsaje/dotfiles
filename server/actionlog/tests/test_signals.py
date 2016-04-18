from mock import Mock, patch

from django.test import TestCase, override_settings

from actionlog import constants
from actionlog import signals


@override_settings(
    HOSTNAME='testhost',
    PAGER_DUTY_ENABLED=True,
    PAGER_DUTY_URL='http://pagerduty.example.com',
    PAGER_DUTY_ADOPS_SERVICE_KEY='123abc',
    PAGER_DUTY_ENGINEERS_SERVICE_KEY='123bca'
)
@patch('actionlog.signals.pagerduty_helper.trigger')
class ActionLogSignalsTestCase(TestCase):
    def test_trigger_alert_pre_save_signal_handler(self, mock_trigger_event):
        instance_id = 1
        mock_instance = self._get_instance_mock(instance_id)
        mock_instance.ad_group_source.source.has_3rd_party_dashboard = lambda: True

        signals.trigger_alert_pre_save_signal_handler(None, mock_instance)

        mock_trigger_event.assert_called_with(
            details={'action_log_admin_url': 'https://one.zemanta.com/admin/actionlog/actionlog/1/change/'},
            incident_key='adgroup_stop_failed',
            description='Adgroup stop action failed',
            event_type='adops',
        )

    def test_trigger_alert_pre_save_signal_handler_trigger_engineers(self, mock_trigger_event):
        instance_id = 1
        mock_instance = self._get_instance_mock(instance_id)
        mock_instance.ad_group_source.source.has_3rd_party_dashboard = lambda: False

        signals.trigger_alert_pre_save_signal_handler(None, mock_instance)

        mock_trigger_event.assert_called_with(
            details={'action_log_admin_url': 'https://one.zemanta.com/admin/actionlog/actionlog/1/change/'},
            incident_key='adgroup_stop_failed',
            description='Adgroup stop action failed',
            event_type='engineers',
        )

    def test_trigger_alert_pre_save_signal_handler_no_action(self, mock_trigger_event):
        instance_id = 1
        mock_instance = self._get_instance_mock(instance_id)

        mock_instance.action_type = constants.ActionType.MANUAL

        signals.trigger_alert_pre_save_signal_handler(None, mock_instance)

        assert not mock_trigger_event.called, 'event should not be triggered'

    def _get_instance_mock(self, instance_id):
        mock_instance = Mock()
        mock_instance.id = instance_id
        mock_instance.state = constants.ActionState.FAILED
        mock_instance.action_type = constants.ActionType.AUTOMATIC
        mock_instance.action = constants.Action.SET_CAMPAIGN_STATE
        mock_instance.ad_group_source = Mock()
        mock_instance.ad_group_source.source = Mock()

        return mock_instance
