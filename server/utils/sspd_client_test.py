import datetime
from mock import patch, Mock

from django.test import TestCase
from django.http import HttpResponse

from dash import constants

from . import sspd_client


@patch("django.conf.settings.SSPD_BASE_URL", "http://testssp.zemanta.com")
class SSPDClientTestCase(TestCase):
    @patch("requests.request")
    @patch("utils.dates_helper.utc_now", Mock(return_value=datetime.datetime(2018, 10, 1, 12)))
    @patch("django.conf.settings.SSPD_AUTH_SECRET", "qwerty")
    def test_get_approval_status(self, mock_request):
        mock_request.return_value = HttpResponse(
            '{"1234": "APPROVED", "9876": "REJECTED", "5555": "PENDING"}', content_type="application/json"
        )
        approval_statuses = sspd_client.get_approval_status([1234, 9876, 5555])
        mock_request.assert_called_once_with(
            "get",
            "http://testssp.zemanta.com/service/status",
            data={},
            headers={
                "Authorization": "Bearer b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJaMSIsImV4cCI6IjIwMTgtMTAtMDFUMTI6MDA6MDUifQ.QQSM0vAymLkrcoJAXJb5XMbwtxW5qKdSrLCG-LqTqvc'"
            },
            params={"contentAdSourceIds": "1234,9876,5555"},
        )

        self.assertEqual(
            {
                1234: constants.ContentAdSubmissionStatus.APPROVED,
                9876: constants.ContentAdSubmissionStatus.REJECTED,
                5555: constants.ContentAdSubmissionStatus.PENDING,
            },
            approval_statuses,
        )
