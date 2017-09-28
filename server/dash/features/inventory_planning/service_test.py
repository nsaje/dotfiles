import mock
from django.test import TestCase

import service
import redshiftapi.api_inventory


class TestService(TestCase):

    def setUp(self):
        self.query_patcher = mock.patch.object(redshiftapi.api_inventory, 'query')
        self.mock_query = self.query_patcher.start()
        self.addCleanup(self.query_patcher.stop)

    def test_get_summary(self):
        self.mock_query.return_value = [{'a': 1}, {'b': 2}]
        self.assertEqual(service.get_summary(None), {'a': 1})

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
            },
            {
                'country': 'b',
                'bids': 2,
            },
            {
                'country': 'c',
                'bids': 3,
            },
        ]
        self.assertEqual(service.get_by_country(None), [
            {
                'country': 'a',
                'name': 'Country A',
                'bids': 1,
            },
            {
                'country': 'b',
                'name': 'Country B',
                'bids': 2,
            },
            {
                'country': 'c',
                'name': None,
                'bids': 3,
            },
        ])

    def test_get_by_device_type(self):
        self.mock_query.return_value = [
            {
                'device_type': 1,
                'bids': 1,
            },
            {
                'device_type': 2,
                'bids': 2,
            },
        ]
        self.assertEqual(service.get_by_device_type(None), [
            {
                'device_type': 1,
                'name': 'Desktop',
                'bids': 1,
            },
            {
                'device_type': 2,
                'name': 'Tablet',
                'bids': 2,
            }
        ])
