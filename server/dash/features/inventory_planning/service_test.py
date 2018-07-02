import mock
from django.test import TestCase

from . import service
import redshiftapi.api_inventory


class TestService(TestCase):

    def setUp(self):
        self.query_patcher = mock.patch.object(redshiftapi.api_inventory, 'query')
        self.mock_query = self.query_patcher.start()
        self.addCleanup(self.query_patcher.stop)

    def test_get_summary(self):
        self.mock_query.return_value = [{'a': 1}, {'b': 2}]
        self.assertEqual(service.get_summary(None, {}), {'a': 1})

    @mock.patch.object(service, '_get_countries_map')
    def test_get_by_country(self, mock_countries_map):
        mock_countries_map.return_value = {
            'a': 'Country A',
            'b': 'Country B',
        }
        self.mock_query.return_value = [
            {
                'country': 'a',
                'bids': 1,
                'bid_reqs': 10000,
            },
            {
                'country': 'b',
                'bids': 2,
                'bid_reqs': 10000,
            },
            {
                'country': 'c',
                'bids': 3,
                'bid_reqs': 10000,
            },
            {
                'country': None,
                'bids': 4,
                'bid_reqs': 10000,
            },
        ]
        self.assertEqual(service.get_by_country(None, {}), [
            {
                'country': 'a',
                'name': 'Country A',
                'bids': 1,
                'bid_reqs': 10000,
            },
            {
                'country': 'b',
                'name': 'Country B',
                'bids': 2,
                'bid_reqs': 10000,
            },
            {
                'country': 'c',
                'name': 'Not reported',
                'bids': 3,
                'bid_reqs': 10000,
            },
            {
                'country': None,
                'name': 'Not reported',
                'bids': 4,
                'bid_reqs': 10000,
            },
        ])

    def test_get_by_device_type(self):
        self.mock_query.return_value = [
            {
                'device_type': 2,
                'bids': 1,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
            {
                'device_type': 5,
                'bids': 2,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
        ]
        self.assertEqual(service.get_by_device_type(None, {}), [
            {
                'device_type': 2,
                'name': 'Desktop',
                'bids': 1,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
            {
                'device_type': 5,
                'name': 'Tablet',
                'bids': 2,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
            {
                'bid_reqs': 0,
                'bids': 0,
                'device_type': 3,
                'name': 'TV & SetTop Box',
                'total_win_price': 0,
                'win_notices': 0},
            {
                'bid_reqs': 0,
                'bids': 0,
                'device_type': 4,
                'name': 'Mobile',
                'total_win_price': 0,
                'win_notices': 0
            }
        ])

    @mock.patch.object(service, '_get_filtered_sources_map')
    def test_get_by_media_source(self, mock_sources_map):
        mock_sources_map.return_value = {
            1: 'Source A',
            2: 'Source B',
            3: 'Source C',
        }
        self.mock_query.return_value = [
            {
                'source_id': 1,
                'bids': 1,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
            {
                'source_id': 2,
                'bids': 2,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
            {
                'source_id': 4,  # not in sources map
                'bids': 2,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
        ]
        self.assertEqual(service.get_by_media_source(None, {}), [
            {
                'source_id': 1,
                'name': 'Source A',
                'bids': 1,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
            {
                'source_id': 2,
                'name': 'Source B',
                'bids': 2,
                'bid_reqs': 10000,
                'win_notices': 5,
                'total_win_price': 10.0,
            },
            {
                'source_id': 3,
                'name': 'Source C',
                'bid_reqs': 0,
                'bids': 0,
                'total_win_price': 0,
                'win_notices': 0
            },
        ])
