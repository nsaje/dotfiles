import datetime
from mock import patch, Mock
import json

from django.test import TestCase
from requests import Response

from dash import constants
from dash import models

from . import sspd_client

from utils.magic_mixer import magic_mixer


@patch("django.conf.settings.SSPD_BASE_URL", "http://testssp.zemanta.com")
class SSPDClientTestCase(TestCase):
    @patch("requests.request")
    @patch("utils.dates_helper.utc_now", Mock(return_value=datetime.datetime(2018, 10, 1, 12)))
    @patch("django.conf.settings.SSPD_AUTH_SECRET", "qwerty")
    def test_get_approval_status(self, mock_request):
        response = Response()
        response._content = b'{"1234": "APPROVED", "9876": "BLOCKED", "5555": "PENDING"}'
        response.status_code = 200
        mock_request.return_value = response
        approval_statuses = sspd_client.get_approval_status([1234, 9876, 5555])
        mock_request.assert_called_once_with(
            "get",
            "http://testssp.zemanta.com/service/approvalstatus",
            data={},
            headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJaMSIsImV4cCI6MTUzODM5NTI2MH0.Xn_HgLj_5Hn6mezRcj58zPJn236hCIm-rE1KDLRiVUg"
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

    @patch("requests.request")
    @patch("utils.dates_helper.utc_now", Mock(return_value=datetime.datetime(2018, 10, 1, 12)))
    @patch("django.conf.settings.SSPD_AUTH_SECRET", "qwerty")
    def test_get_content_ad_status(self, mock_request):
        source = magic_mixer.blend(models.Source)

        response_content = {
            "1234": [{"status": "APPROVED", "reason": "", "sourceId": source.id}],
            "9876": [{"status": "BLOCKED", "reason": "Inappropriate content", "sourceId": source.id}],
            "5555": [{"status": "PENDING", "reason": "", "sourceId": source.id}],
        }

        response = Response()
        response._content = json.dumps(response_content).encode()
        response.status_code = 200
        mock_request.return_value = response
        approval_statuses = sspd_client.get_content_ad_status([1234, 9876, 5555])
        mock_request.assert_called_once_with(
            "get",
            "http://testssp.zemanta.com/service/contentadstatus",
            data={},
            headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJaMSIsImV4cCI6MTUzODM5NTI2MH0.Xn_HgLj_5Hn6mezRcj58zPJn236hCIm-rE1KDLRiVUg"
            },
            params={"contentAdIds": "1234,9876,5555"},
        )

        self.assertEqual(
            {
                1234: {source.id: {"status": constants.ContentAdSubmissionStatus.APPROVED, "reason": ""}},
                9876: {
                    source.id: {
                        "status": constants.ContentAdSubmissionStatus.REJECTED,
                        "reason": "Inappropriate content",
                    }
                },
                5555: {source.id: {"status": constants.ContentAdSubmissionStatus.PENDING, "reason": ""}},
            },
            approval_statuses,
        )
