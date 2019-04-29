import json
from collections import namedtuple

from django.test import TestCase
from mock import MagicMock
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
        expression = ["and", ["or", "bluekai:1234"], ["not", ["or", "bluekai:5432"]]]
        bluekaiapi.get_segment_reach(expression)

        self.mock_perform_request.assert_called_with(
            "POST",
            bluekaiapi.SEGMENT_INVENTORY_URL,
            params={"countries": "ALL"},
            data='{"AND":[{"AND":[{"OR":[{"cat":1234}]}]},{"NOT":{"AND":[{"OR":[{"cat":5432}]}]}}]}',
        )

    def test_only_not(self):
        expression = ["not", ["or", "bluekai:5432"]]
        bluekaiapi.get_segment_reach(expression)

        self.mock_perform_request.assert_called_with(
            "POST",
            bluekaiapi.SEGMENT_INVENTORY_URL,
            params={"countries": "ALL"},
            data='{"AND":[{"NOT":{"AND":[{"OR":[{"cat":5432}]}]}}]}',
        )


class ExpressionFromAudience(TestCase):
    @patch.object(bluekaiapi, "get_campaign", new=MagicMock())
    @patch.object(bluekaiapi, "get_audience")
    def test_get(self, mock_get_audience):
        mock_get_audience.return_value = {
            "segments": {
                "AND": [
                    {
                        "AND": [
                            {
                                "OR": [
                                    {
                                        "cat": 851366,
                                        "name": "Wellness",
                                        "path": "Oracle Country-Specific Audiences > Spain (ES) > Hobbies and Interests (Affinity) > Health and Fitness > Wellness",
                                        "status": "active",
                                        "price": 0.75,
                                        "freq": [1, None],
                                    },
                                    {
                                        "cat": 851368,
                                        "name": "Dieting and Weight Loss",
                                        "path": "Oracle Country-Specific Audiences > Spain (ES) > Hobbies and Interests (Affinity) > Health and Fitness > Wellness > Dieting and Weight Loss",
                                        "status": "active",
                                        "price": 0.75,
                                        "freq": [1, None],
                                    },
                                    {
                                        "cat": 851369,
                                        "name": "Nutrition",
                                        "path": "Oracle Country-Specific Audiences > Spain (ES) > Hobbies and Interests (Affinity) > Health and Fitness > Wellness > Nutrition",
                                        "status": "active",
                                        "price": 0.75,
                                        "freq": [1, None],
                                    },
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        result = bluekaiapi.get_expression_from_campaign(123)
        self.assertEqual(result, ["or", "bluekai:851366", "bluekai:851368", "bluekai:851369"])

    @patch.object(bluekaiapi, "get_campaign", new=MagicMock())
    @patch.object(bluekaiapi, "get_audience")
    def test_get_2(self, mock_get_audience):
        mock_get_audience.return_value = {
            "segments": {
                "AND": [
                    {
                        "AND": [
                            {
                                "OR": [
                                    {
                                        "cat": 2284,
                                        "name": "Alfa Romeo",
                                        "path": "In-Market > Auto, Cars and Trucks > Makes and Models > Alfa Romeo",
                                        "status": "active",
                                        "price": 1.8,
                                        "freq": [1, None],
                                    },
                                    {
                                        "cat": 9288,
                                        "name": "Aston Martin",
                                        "path": "In-Market > Auto, Cars and Trucks > Makes and Models > Aston Martin",
                                        "status": "active",
                                        "price": 1.8,
                                        "freq": [1, None],
                                    },
                                ]
                            },
                            {
                                "OR": [
                                    {
                                        "cat": 355,
                                        "name": "Audi A4",
                                        "path": "In-Market > Auto, Cars and Trucks > Makes and Models > Audi > Audi A4",
                                        "status": "active",
                                        "price": 1.8,
                                        "freq": [1, None],
                                    },
                                    {
                                        "cat": 359,
                                        "name": "Audi A3",
                                        "path": "In-Market > Auto, Cars and Trucks > Makes and Models > Audi > Audi A3",
                                        "status": "active",
                                        "price": 1.8,
                                        "freq": [1, None],
                                    },
                                ]
                            },
                        ]
                    },
                    {
                        "NOT": {
                            "AND": [
                                {
                                    "OR": [
                                        {
                                            "cat": 2150,
                                            "name": "BMW 3-Series",
                                            "path": "In-Market > Auto, Cars and Trucks > Makes and Models > BMW > BMW 3-Series",
                                            "status": "active",
                                            "price": 1.8,
                                            "freq": [1, None],
                                        },
                                        {
                                            "cat": 372199,
                                            "name": "BMW 4-Series",
                                            "path": "In-Market > Auto, Cars and Trucks > Makes and Models > BMW > BMW 4-Series",
                                            "status": "active",
                                            "price": 1.8,
                                            "freq": [1, None],
                                        },
                                    ]
                                }
                            ]
                        }
                    },
                ]
            }
        }
        result = bluekaiapi.get_expression_from_campaign(123)
        self.assertEqual(
            result,
            [
                "and",
                ["and", ["or", "bluekai:2284", "bluekai:9288"], ["or", "bluekai:355", "bluekai:359"]],
                ["not", ["or", "bluekai:2150", "bluekai:372199"]],
            ],
        )

    @patch.object(bluekaiapi, "get_campaign", new=MagicMock())
    @patch.object(bluekaiapi, "get_audience")
    def test_simple_expression(self, mock_get_audience):
        mock_get_audience.return_value = {"segments": {"AND": [{"AND": [{"OR": [{"cat": 1234}]}]}]}}
        expected = ["or", "bluekai:1234"]
        self.assertEqual(expected, bluekaiapi.get_expression_from_campaign(123))

    @patch.object(bluekaiapi, "get_campaign", new=MagicMock())
    @patch.object(bluekaiapi, "get_audience")
    def test_single_and_with_not(self, mock_get_audience):
        mock_get_audience.return_value = {
            "segments": {"AND": [{"AND": [{"OR": [{"cat": 1234}]}]}, {"NOT": {"AND": [{"OR": [{"cat": 5432}]}]}}]}
        }
        expected = ["and", ["or", "bluekai:1234"], ["not", ["or", "bluekai:5432"]]]
        self.assertEqual(expected, bluekaiapi.get_expression_from_campaign(123))

    @patch.object(bluekaiapi, "get_campaign", new=MagicMock())
    @patch.object(bluekaiapi, "get_audience")
    def test_only_not(self, mock_get_audience):
        mock_get_audience.return_value = {"segments": {"AND": [{"NOT": {"AND": [{"OR": [{"cat": 5432}]}]}}]}}
        expected = ["not", ["or", "bluekai:5432"]]
        self.assertEqual(expected, bluekaiapi.get_expression_from_campaign(123))
