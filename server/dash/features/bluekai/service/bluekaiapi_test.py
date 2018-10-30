import json
from collections import namedtuple

from django.test import TestCase
from mock import patch

from . import bluekaiapi

MockRequestsResponse = namedtuple("MockRequestsResponse", ["content"])


class SegmentReachTestCase(TestCase):
    def setUp(self):
        patcher = patch("dash.features.bluekai.service.bluekaiapi._perform_request")
        self.mock_perform_request = patcher.start()
        self.mock_perform_request.return_value = MockRequestsResponse(content=json.dumps({"reach": 1}))
        self.addCleanup(patcher.stop)

    def test_simple_expression(self):
        expression = ["and", ["and", ["or", "bluekai:1234"]]]
        bluekaiapi.get_segment_reach(expression)

        self.mock_perform_request.assert_called_with(
            "POST",
            bluekaiapi.SEGMENT_INVENTORY_URL,
            params={"countries": "ALL"},
            data='{"AND":[{"AND":[{"OR":[{"cat":1234}]}]}]}',
        )

    def test_single_and(self):
        expression = ["and", ["or", "bluekai:1234"]]
        bluekaiapi.get_segment_reach(expression)

        self.mock_perform_request.assert_called_with(
            "POST",
            bluekaiapi.SEGMENT_INVENTORY_URL,
            params={"countries": "ALL"},
            data='{"AND":[{"AND":[{"OR":[{"cat":1234}]}]}]}',
        )

    def test_no_and(self):
        expression = ["or", "bluekai:1234"]
        bluekaiapi.get_segment_reach(expression)

        self.mock_perform_request.assert_called_with(
            "POST",
            bluekaiapi.SEGMENT_INVENTORY_URL,
            params={"countries": "ALL"},
            data='{"AND":[{"AND":[{"OR":[{"cat":1234}]}]}]}',
        )

    def test_single_and_with_not(self):
        expression = ["and", ["or", "bluekai:1234"], ["not", "bluekai:5432"]]
        bluekaiapi.get_segment_reach(expression)

        self.mock_perform_request.assert_called_with(
            "POST",
            bluekaiapi.SEGMENT_INVENTORY_URL,
            params={"countries": "ALL"},
            data='{"AND":[{"AND":[{"OR":[{"cat":1234}]}]},{"NOT":{"cat":5432}}]}',
        )

    def test_only_not(self):
        expression = ["not", "bluekai:5432"]
        bluekaiapi.get_segment_reach(expression)

        self.mock_perform_request.assert_called_with(
            "POST", bluekaiapi.SEGMENT_INVENTORY_URL, params={"countries": "ALL"}, data='{"AND":[{"NOT":{"cat":5432}}]}'
        )
