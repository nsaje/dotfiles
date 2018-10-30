import mock
from django.urls import reverse

import dash.features.inventory_planning
import restapi.common.views_base_test


class InventoryPlanningViewTest(restapi.common.views_base_test.RESTAPITest):
    @mock.patch.object(dash.features.inventory_planning, "get_summary", autospec=True)
    def test_summary(self, mock_func):
        mock_func.return_value = {"bid_reqs": 5, "bids": 4, "win_notices": 2, "total_win_price": 10.0}
        r = self.client.post(reverse("inventory_planning", kwargs=dict(breakdown="summary")))
        resp_json = self.assertResponseValid(r)
        mock_func.assert_called_with(r.renderer_context["request"], {})
        self.assertEqual(
            resp_json["data"],
            {
                "auctionCount": 5,
                "avgCpm": 5.0,
                "avgCpc": 5.0 / 1000 / dash.features.inventory_planning.constants.SourceCtr.AVG,
                "winRatio": 0.5,
            },
        )

    @mock.patch.object(dash.features.inventory_planning, "get_by_country", return_value={}, autospec=True)
    def test_by_country(self, mock_func):
        mock_func.return_value = [
            {"country": "a", "name": "A", "bid_reqs": 5, "bids": 4, "win_notices": 2, "total_win_price": 10.0},
            {"country": "b", "name": "B", "bid_reqs": 50, "bids": 40, "win_notices": 20, "total_win_price": 100.0},
        ]

        r = self.client.post(reverse("inventory_planning", kwargs=dict(breakdown="countries")))
        resp_json = self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})
        self.assertEqual(
            resp_json["data"],
            [{"value": "a", "name": "A", "auctionCount": 5}, {"value": "b", "name": "B", "auctionCount": 50}],
        )

    @mock.patch.object(dash.features.inventory_planning, "get_by_device_type", return_value={}, autospec=True)
    def test_by_device_type(self, mock_func):
        r = self.client.post(reverse("inventory_planning", kwargs=dict(breakdown="device-types")))
        self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})

    @mock.patch.object(dash.features.inventory_planning, "get_by_publisher", return_value={}, autospec=True)
    def test_by_publisher(self, mock_func):
        r = self.client.post(reverse("inventory_planning", kwargs=dict(breakdown="publishers")))
        self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})

    @mock.patch.object(dash.features.inventory_planning, "get_by_media_source", return_value={}, autospec=True)
    def test_by_media_source(self, mock_func):
        r = self.client.post(reverse("inventory_planning", kwargs=dict(breakdown="media-sources")))
        self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with(r.renderer_context["request"], {})

    @mock.patch.object(dash.features.inventory_planning, "get_summary", return_value={}, autospec=True)
    def test_filters_get(self, mock_func):
        r = self.client.get(
            reverse("inventory_planning", kwargs=dict(breakdown="summary"))
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
            reverse("inventory_planning", kwargs=dict(breakdown="summary"))
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
            reverse("inventory_planning", kwargs=dict(breakdown="summary")),
            data={"countries": ["1", "2"], "publishers": ["3", "4"], "devices": [5, 6], "sources": [7, 8]},
            format="json",
        )
        self.assertResponseValid(r)
        mock_func.assert_called_with(
            r.renderer_context["request"],
            {"country": ["1", "2"], "publisher": ["3", "4"], "device_type": [5, 6], "source_id": [7, 8]},
        )
