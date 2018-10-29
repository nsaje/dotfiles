import datetime
from mock import patch, Mock, ANY, call
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
        approval_statuses = sspd_client.get_approval_status(content_ad_source_ids=[1234, 9876, 5555])
        mock_request.assert_called_once_with(
            "post",
            "http://testssp.zemanta.com/service/approvalstatus",
            data=json.dumps(
                {
                    "adGroupIds": None,
                    "contentAdIds": None,
                    "sourceTypes": None,
                    "slugs": None,
                    "contentAdSourceIds": [1234, 9876, 5555],
                }
            ),
            headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJaMSIsImV4cCI6MTUzODM5NTI2MH0.Xn_HgLj_5Hn6mezRcj58zPJn236hCIm-rE1KDLRiVUg",
                "Content-type": "application/json",
            },
            params={},
            timeout=None,
        )

        self.assertEqual(
            {
                1234: constants.ContentAdSubmissionStatus.APPROVED,
                9876: constants.ContentAdSubmissionStatus.REJECTED,
                5555: constants.ContentAdSubmissionStatus.PENDING,
            },
            approval_statuses,
        )

    def _create_requests_response(self, content, status_code=200):
        response = Response()
        response._content = content
        response.status_code = status_code
        return response

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
        sspd_client.TIMEOUT = (10, 10)
        approval_statuses = sspd_client.get_content_ad_status([1234, 9876, 5555])
        mock_request.assert_called_once_with(
            "get",
            "http://testssp.zemanta.com/service/contentadstatus",
            data={},
            headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJaMSIsImV4cCI6MTUzODM5NTI2MH0.Xn_HgLj_5Hn6mezRcj58zPJn236hCIm-rE1KDLRiVUg"
            },
            params={"contentAdIds": "1234,9876,5555"},
            timeout=sspd_client.TIMEOUT,
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

    @patch("requests.request")
    @patch("utils.dates_helper.utc_now", Mock(return_value=datetime.datetime(2018, 10, 1, 12)))
    @patch("django.conf.settings.SSPD_AUTH_SECRET", "qwerty")
    @patch("utils.sspd_client.MAX_REQUEST_IDS", 10)
    def test_paginate_request(self, mock_request):
        mock_request.side_effect = [
            self._create_requests_response(json.dumps({k: "APPROVED" for k in range(10)}).encode("utf-8")),
            self._create_requests_response(json.dumps({k: "BLOCKED" for k in range(10, 20)}).encode("utf-8")),
            self._create_requests_response(json.dumps({k: "PENDING" for k in range(20, 25)}).encode("utf-8")),
        ]
        sspd_client_timeout = (10, 10)
        approval_statuses = sspd_client._paginate_request(
            "get",
            "http://testssp.zemanta.com/test",
            {"testIds": [i for i in range(25)]},
            paginate_key="testIds",
            timeout=sspd_client_timeout,
        )
        mock_request.assert_has_calls(
            [
                call(
                    "get",
                    "http://testssp.zemanta.com/test",
                    data={},
                    headers=ANY,
                    params={"testIds": "{}".format(",".join(str(x) for x in range(10)))},
                    timeout=sspd_client_timeout,
                ),
                call(
                    "get",
                    "http://testssp.zemanta.com/test",
                    data={},
                    headers=ANY,
                    params={"testIds": "{}".format(",".join(str(x) for x in range(10, 20)))},
                    timeout=sspd_client_timeout,
                ),
                call(
                    "get",
                    "http://testssp.zemanta.com/test",
                    data={},
                    headers=ANY,
                    params={"testIds": "{}".format(",".join(str(x) for x in range(20, 25)))},
                    timeout=sspd_client_timeout,
                ),
            ]
        )
        for i in range(10):
            self.assertEqual("APPROVED", approval_statuses[str(i)])
        for i in range(10, 20):
            self.assertEqual("BLOCKED", approval_statuses[str(i)])
        for i in range(20, 25):
            self.assertEqual("PENDING", approval_statuses[str(i)])
