import mock

from utils.base_test_case import BaseTestCase

from . import send_depleting_credits_emails


class ApplyBrowsersTargetingTestCase(BaseTestCase):
    @mock.patch("core.features.credit_notifications.check_and_notify_depleting_credits", autospec=True)
    def test_command(self, mock_check):
        command = send_depleting_credits_emails.Command()
        command.handle()

        mock_check.assert_called_once_with()
