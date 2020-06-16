import mock
from django.urls import reverse

import dash.features.inventory_planning
import restapi.common.views_base_test_case


class InventoryPlanningViewTest(restapi.common.views_base_test_case.RESTAPITestCase):
    fixtures = ["test_geolocations"]

    @mock.patch.object(dash.features.inventory_planning, "get_summary", autospec=True)
    def test_summary(self, mock_func):
        mock_func.return_value = {
            "bid_reqs": 5,
            "bids": 4,
            "win_notices": 2,
            "total_win_price": 10.0,
            "slots": 10,
            "redirects": 1,
        }
        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="summary"))
        )
        resp_json = self.assertResponseValid(r)
        mock_func.assert_called_with(r.renderer_context["request"], {})
        self.assertEqual(
            resp_json["data"], {"auctionCount": 10, "avgCpm": 5.0, "avgCpc": 10.0 / 1000 / 1, "winRatio": 0.5}
        )

    @mock.patch.object(dash.features.inventory_planning, "get_by_country", return_value={}, autospec=True)
    def test_by_country(self, mock_func):
        mock_func.return_value = [
            {
                "country": "a",
                "name": "A",
                "bid_reqs": 5,
                "bids": 4,
                "win_notices": 2,
                "total_win_price": 10.0,
                "slots": 10,
                "redirects": 1,
            },
            {
                "country": "b",
                "name": "B",
                "bid_reqs": 50,
                "bids": 40,
                "win_notices": 20,
                "total_win_price": 100.0,
                "slots": 60,
                "redirects": 10,
            },
        ]

        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="countries"))
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})
        self.assertEqual(
            resp_json["data"],
            [{"value": "a", "name": "A", "auctionCount": 10}, {"value": "b", "name": "B", "auctionCount": 60}],
        )

    @mock.patch.object(dash.features.inventory_planning, "get_by_device_type", return_value={}, autospec=True)
    def test_by_device_type(self, mock_func):
        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="device-types"))
        )
        self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})

    @mock.patch.object(dash.features.inventory_planning, "get_by_publisher", return_value={}, autospec=True)
    def test_by_publisher(self, mock_func):
        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="publishers"))
        )
        self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})

    @mock.patch.object(dash.features.inventory_planning, "get_by_media_source", return_value={}, autospec=True)
    def test_by_media_source(self, mock_func):
        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="media-sources"))
        )
        self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})

    @mock.patch.object(dash.features.inventory_planning, "get_summary", return_value={}, autospec=True)
    def test_filters_get(self, mock_func):
        r = self.client.get(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="summary"))
            + "?countries=1&countries=2&publishers=3&publishers=4&devices=5&devices=6&sources=7&sources=8"
        )
        self.assertResponseValid(r)
        mock_func.assert_called_with(
            r.renderer_context["request"],
            {"country": ["1", "2"], "publisher": ["3", "4"], "device_type": [5, 6], "source_id": [7, 8]},
        )

    @mock.patch.object(dash.features.inventory_planning, "get_summary", return_value={}, autospec=True)
    def test_filters_get_commas(self, mock_func):
        r = self.client.get(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="summary"))
            + "?countries=1,2&publishers=3,4&devices=5,6&sources=7,8"
        )
        self.assertResponseValid(r)
        mock_func.assert_called_with(
            r.renderer_context["request"],
            {"country": ["1", "2"], "publisher": ["3", "4"], "device_type": [5, 6], "source_id": [7, 8]},
        )

    @mock.patch.object(dash.features.inventory_planning, "get_summary", return_value={}, autospec=True)
    def test_filters_post(self, mock_func):
        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning", kwargs=dict(breakdown="summary")),
            data={"countries": ["1", "2"], "publishers": ["3", "4"], "devices": [5, 6], "sources": [7, 8]},
            format="json",
        )
        self.assertResponseValid(r)
        mock_func.assert_called_with(
            r.renderer_context["request"],
            {"country": ["1", "2"], "publisher": ["3", "4"], "device_type": [5, 6], "source_id": [7, 8]},
        )

    @mock.patch.object(dash.features.inventory_planning, "get_by_media_source", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_by_device_type", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_by_publisher", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_by_country", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_summary", return_value={}, autospec=True)
    def test_export_filters(self, mock_summary, mock_country, mock_publisher, mock_device_type, mock_media_source):
        mock_data = [
            {
                "country": "a",
                "publisher": "P1",
                "device_type": 2,
                "source_id": 123,
                "name": "A",
                "bid_reqs": 5,
                "bids": 4,
                "win_notices": 2,
                "total_win_price": 10.0,
                "slots": 10,
                "redirects": 1,
            },
            {
                "country": "b",
                "publisher": "P2",
                "device_type": 5,
                "source_id": 123,
                "name": "B",
                "bid_reqs": 50,
                "bids": 40,
                "win_notices": 20,
                "total_win_price": 100.0,
                "slots": 60,
                "redirects": 10,
            },
        ]
        mock_summary.return_value = mock_data[0]
        mock_country.return_value = mock_data
        mock_publisher.return_value = mock_data
        mock_device_type.return_value = mock_data
        mock_media_source.return_value = mock_data

        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning_export"),
            data={"countries": ["US", "UK"], "publishers": ["www.msn.com"], "devices": ["5"], "sources": ["85"]},
            format="json",
        )
        response_csv = r.content.decode("utf-8").replace('"', "")
        expected_csv = (
            "Active filters\r\n"
            "Countries\r\n"
            "United States,UK\r\n"
            "\r\n"
            "Publishers\r\n"
            "www.msn.com\r\n"
            "\r\n"
            "Devices\r\n"
            "Tablet\r\n"
            "\r\n"
            "SSPs\r\n"
            "85\r\n"
            "\r\n"
            "Devices\r\n"
            "A,10\r\n"
            "B,60\r\n"
            "\r\n"
            "SSPs\r\n"
            "A,10\r\n"
            "B,60\r\n"
            "\r\n"
            "Countries\r\n"
            "A,10\r\n"
            "B,60\r\n"
            "\r\n"
            "Publishers\r\n"
            "P1,10\r\n"
            "P2,60\r\n"
            "\r\n"
        )
        self.assertEqual(expected_csv, response_csv)

    @mock.patch.object(dash.features.inventory_planning, "get_by_media_source", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_by_device_type", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_by_publisher", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_by_country", return_value={}, autospec=True)
    @mock.patch.object(dash.features.inventory_planning, "get_summary", return_value={}, autospec=True)
    def test_export_no_filters(self, mock_summary, mock_country, mock_publisher, mock_device_type, mock_media_source):
        mock_data = [
            {
                "country": "a",
                "publisher": "P1",
                "device_type": 2,
                "source_id": 123,
                "name": "A",
                "bid_reqs": 5,
                "bids": 4,
                "win_notices": 2,
                "total_win_price": 10.0,
                "slots": 10,
                "redirects": 1,
            },
            {
                "country": "b",
                "publisher": "P2",
                "device_type": 5,
                "source_id": 123,
                "name": "B",
                "bid_reqs": 50,
                "bids": 40,
                "win_notices": 20,
                "total_win_price": 100.0,
                "slots": 60,
                "redirects": 10,
            },
        ]
        mock_summary.return_value = mock_data[0]
        mock_country.return_value = mock_data
        mock_publisher.return_value = mock_data
        mock_device_type.return_value = mock_data
        mock_media_source.return_value = mock_data

        r = self.client.post(
            reverse("restapi.inventory_planning.internal:inventory_planning_export"), data={}, format="json"
        )
        response_csv = r.content.decode("utf-8").replace('"', "")
        expected_csv = (
            "Devices\r\n"
            "A,10\r\n"
            "B,60\r\n"
            "\r\n"
            "SSPs\r\n"
            "A,10\r\n"
            "B,60\r\n"
            "\r\n"
            "Countries\r\n"
            "A,10\r\n"
            "B,60\r\n"
            "\r\n"
            "Publishers\r\n"
            "P1,10\r\n"
            "P2,60\r\n"
            "\r\n"
        )
        self.assertEqual(expected_csv, response_csv)
