from dataclasses import dataclass

import mock
from django.test import TestCase

import redshiftapi.api_inventory

from . import constants
from . import nas
from . import service


class TestService(TestCase):
    def setUp(self):
        self.query_patcher = mock.patch.object(redshiftapi.api_inventory, "query")
        self.mock_query = self.query_patcher.start()
        self.addCleanup(self.query_patcher.stop)

    def test_get_summary(self):
        self.mock_query.return_value = [{"a": 1}, {"b": 2}]
        self.assertEqual(service.get_summary(None, {}), {"a": 1})

    @mock.patch.object(service, "get_countries_map")
    def test_get_by_country(self, mock_countries_map):
        mock_countries_map.return_value = {"a": "Country A", "b": "Country B"}
        self.mock_query.return_value = [
            {"country": "a", "bids": 1, "slots": 10000},
            {"country": "b", "bids": 2, "slots": 10000},
            {"country": "c", "bids": 3, "slots": 10000},
            {"country": None, "bids": 4, "slots": 10000},
        ]
        self.assertEqual(
            service.get_by_country(None, {}),
            [
                {"country": "a", "name": "Country A", "bids": 1, "slots": 10000},
                {"country": "b", "name": "Country B", "bids": 2, "slots": 10000},
                {"country": "c", "name": "Not reported", "bids": 3, "slots": 10000},
                {"country": None, "name": "Not reported", "bids": 4, "slots": 10000},
            ],
        )

    def test_get_by_device_type(self):
        self.mock_query.return_value = [
            {
                "device_type": 2,
                "bids": 1,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 20000,
                "redirects": 100,
            },
            {
                "device_type": 5,
                "bids": 2,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 20000,
                "redirects": 100,
            },
        ]
        self.assertEqual(
            service.get_by_device_type(None, {}),
            [
                {
                    "device_type": 2,
                    "name": "Desktop",
                    "bids": 1,
                    "bid_reqs": 10000,
                    "win_notices": 5,
                    "total_win_price": 10.0,
                    "slots": 20000,
                    "redirects": 100,
                },
                {
                    "device_type": 5,
                    "name": "Tablet",
                    "bids": 2,
                    "bid_reqs": 10000,
                    "win_notices": 5,
                    "total_win_price": 10.0,
                    "slots": 20000,
                    "redirects": 100,
                },
                {
                    "bid_reqs": 0,
                    "bids": 0,
                    "device_type": 3,
                    "name": "TV & SetTop Box",
                    "total_win_price": 0,
                    "win_notices": 0,
                    "slots": 0,
                    "redirects": 0,
                },
                {
                    "bid_reqs": 0,
                    "bids": 0,
                    "device_type": 4,
                    "name": "Mobile",
                    "total_win_price": 0,
                    "win_notices": 0,
                    "slots": 0,
                    "redirects": 0,
                },
            ],
        )

    @mock.patch.object(service, "get_filtered_sources_map")
    def test_get_by_media_source(self, mock_sources_map):
        mock_sources_map.return_value = {1: "Source A", 2: "Source B", 3: "Source C"}
        self.mock_query.return_value = [
            {
                "source_id": 1,
                "bids": 1,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 20000,
                "redirects": 100,
            },
            {
                "source_id": 2,
                "bids": 2,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 20000,
                "redirects": 100,
            },
            {
                "source_id": 4,  # not in sources map
                "bids": 2,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 20000,
                "redirects": 100,
            },
        ]
        self.assertEqual(
            service.get_by_media_source(None, {}),
            [
                {
                    "source_id": 1,
                    "name": "Source A",
                    "bids": 1,
                    "bid_reqs": 10000,
                    "win_notices": 5,
                    "total_win_price": 10.0,
                    "slots": 20000,
                    "redirects": 100,
                },
                {
                    "source_id": 2,
                    "name": "Source B",
                    "bids": 2,
                    "bid_reqs": 10000,
                    "win_notices": 5,
                    "total_win_price": 10.0,
                    "slots": 20000,
                    "redirects": 100,
                },
                {
                    "source_id": 3,
                    "name": "Source C",
                    "bid_reqs": 0,
                    "bids": 0,
                    "total_win_price": 0,
                    "win_notices": 0,
                    "slots": 0,
                    "redirects": 0,
                },
            ],
        )

    def test_get_by_channel(self):
        self.mock_query.return_value = [
            {
                "channel": constants.InventoryChannel.NATIVE,
                "bids": 1,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 20000,
                "redirects": 100,
            },
            {
                "channel": constants.InventoryChannel.NATIVE_OR_VIDEO,
                "bids": 2,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 30000,
                "redirects": 100,
            },
            {
                "channel": constants.InventoryChannel.DISPLAY,
                "bids": 2,
                "bid_reqs": 10000,
                "win_notices": 5,
                "total_win_price": 10.0,
                "slots": 20000,
                "redirects": 100,
            },
        ]
        self.assertEqual(
            service.get_by_channel(None, {}),
            [
                {
                    "channel": constants.InventoryChannel.NATIVE,
                    "name": "Native",
                    "bids": 3,
                    "bid_reqs": 20000,
                    "win_notices": 10,
                    "total_win_price": 20.0,
                    "slots": 50000,
                    "redirects": 200,
                },
                {
                    "channel": constants.InventoryChannel.VIDEO,
                    "name": "Video",
                    "bids": 2,
                    "bid_reqs": 10000,
                    "win_notices": 5,
                    "total_win_price": 10.0,
                    "slots": 30000,
                    "redirects": 100,
                },
                {
                    "channel": constants.InventoryChannel.DISPLAY,
                    "name": "Display",
                    "bids": 2,
                    "bid_reqs": 10000,
                    "win_notices": 5,
                    "total_win_price": 10.0,
                    "slots": 20000,
                    "redirects": 100,
                },
            ],
        )

    def test_get_by_channel_query(self):
        service.get_by_channel(None, {"channel": [constants.InventoryChannel.NATIVE]})
        self.mock_query.assert_called_with(
            breakdown="channel",
            constraints={
                "channel": [constants.InventoryChannel.NATIVE, constants.InventoryChannel.NATIVE_OR_VIDEO],
                "source_id": [],
            },
        )

        service.get_by_channel(None, {"channel": [constants.InventoryChannel.NATIVE, constants.InventoryChannel.VIDEO]})
        self.mock_query.assert_called_with(
            breakdown="channel",
            constraints={
                "channel": [
                    constants.InventoryChannel.NATIVE,
                    constants.InventoryChannel.VIDEO,
                    constants.InventoryChannel.NATIVE_OR_VIDEO,
                ],
                "source_id": [],
            },
        )

        service.get_by_channel(None, {"channel": [constants.InventoryChannel.VIDEO]})
        self.mock_query.assert_called_with(
            breakdown="channel",
            constraints={
                "channel": [constants.InventoryChannel.VIDEO, constants.InventoryChannel.NATIVE_OR_VIDEO],
                "source_id": [],
            },
        )

        service.get_by_channel(None, {"channel": [constants.InventoryChannel.DISPLAY]})
        self.mock_query.assert_called_with(
            breakdown="channel", constraints={"channel": [constants.InventoryChannel.DISPLAY], "source_id": []}
        )


class TestFilteredSourcesMap(TestCase):
    def setUp(self):
        @dataclass
        class Source:
            id: int
            supports_video: bool
            supports_display: bool
            name: str = "name"
            released: bool = True

        self.native_source = Source(id=1, supports_video=False, supports_display=False)
        self.video_source = Source(id=2, supports_video=True, supports_display=False)
        self.display_source = Source(id=3, supports_video=False, supports_display=True)
        self.unreleased_source = Source(id=4, supports_video=False, supports_display=False, released=False)
        self.all_sources = [self.native_source, self.video_source, self.display_source, self.unreleased_source]

    @mock.patch.object(nas, "should_show_nas_source", return_value=False)
    @mock.patch.object(service, "_get_sources_cache")
    def test_filtered_sources_channel(self, mock_sources, mock_nas):
        mock_sources.return_value = self.all_sources
        self.assertEqual(
            service.get_filtered_sources_map(None, {"channel": [constants.InventoryChannel.VIDEO]}).keys(),
            {self.video_source.id},
        )
        self.assertEqual(
            service.get_filtered_sources_map(None, {"channel": [constants.InventoryChannel.DISPLAY]}).keys(),
            {self.display_source.id},
        )
        self.assertEqual(
            service.get_filtered_sources_map(
                None, {"channel": [constants.InventoryChannel.VIDEO, constants.InventoryChannel.DISPLAY]}
            ).keys(),
            {self.video_source.id, self.display_source.id},
        )

    @mock.patch.object(nas, "should_show_nas_source", return_value=False)
    @mock.patch.object(service, "_get_sources_cache")
    def test_filtered_sources_unreleased(self, mock_sources, mock_nas):
        mock_sources.return_value = self.all_sources
        self.assertEqual(
            service.get_filtered_sources_map(None, {}).keys(),
            {self.native_source.id, self.video_source.id, self.display_source.id},
        )

    @mock.patch.object(nas, "should_show_nas_source")
    @mock.patch.object(service, "_get_sources_cache")
    def test_filtered_sources_unreleased_nas(self, mock_sources, mock_nas):
        mock_nas.side_effect = lambda source, _: True if source == self.unreleased_source else False
        mock_sources.return_value = self.all_sources
        self.assertEqual(
            service.get_filtered_sources_map(None, {}).keys(),
            {self.native_source.id, self.video_source.id, self.display_source.id, self.unreleased_source.id},
        )
