import mock

from django.core.urlresolvers import reverse

import restapi.views_test
import dash.features.inventory_planning

from . import views


class InventoryPlanningViewTest(restapi.views_test.RESTAPITest):

    @mock.patch.object(dash.features.inventory_planning, 'get_summary', autospec=True)
    def test_summary(self, mock_func):
        mock_func.return_value = {
            'bid_reqs': 5,
            'bids': 4,
            'win_notices': 2,
            'total_win_price': 10.0
        }
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='summary')))
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({})
        self.assertEqual(r['data'], {
            'auctionCount': 5,
            'avgCpm': 5.0,
            'avgCpc': 5.0 / 1000 / views.AVG_CTR,
            'winRatio': 0.5,
        })

    @mock.patch.object(dash.features.inventory_planning, 'get_by_country', return_value={}, autospec=True)
    def test_by_country(self, mock_func):
        mock_func.return_value = [{
            'country': 'a',
            'name': 'A',
            'bid_reqs': 5,
            'bids': 4,
            'win_notices': 2,
            'total_win_price': 10.0
        }, {
            'country': 'b',
            'name': 'B',
            'bid_reqs': 50,
            'bids': 40,
            'win_notices': 20,
            'total_win_price': 100.0
        }]

        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='countries')))
        r = self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with({})
        self.assertEqual(r['data'], [{
            'value': 'a',
            'name': 'A',
            'auctionCount': 5,
        }, {
            'value': 'b',
            'name': 'B',
            'auctionCount': 50,
        }])

    @mock.patch.object(dash.features.inventory_planning, 'get_by_device_type', return_value={}, autospec=True)
    def test_by_device_type(self, mock_func):
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='device-types')))
        r = self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with({})

    @mock.patch.object(dash.features.inventory_planning, 'get_by_publisher', return_value={}, autospec=True)
    def test_by_publisher(self, mock_func):
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='publishers')))
        r = self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with({})

    @mock.patch.object(dash.features.inventory_planning, 'get_by_media_source', return_value={}, autospec=True)
    def test_by_media_source(self, mock_func):
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='media-sources')))
        r = self.assertResponseValid(r, data_type=list)
        mock_func.assert_called_with({})

    @mock.patch.object(dash.features.inventory_planning, 'get_summary', return_value={}, autospec=True)
    def test_filters_get(self, mock_func):
        r = self.client.get(
            reverse('inventory_planning', kwargs=dict(breakdown='summary')) + '?c=1&c=2&p=3&p=4&d=5&d=6&s=7&s=8'
        )
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({'country': ['1', '2'], 'publisher': ['3', '4'], 'device_type': [5, 6], 'source_id': [7, 8]})

    @mock.patch.object(dash.features.inventory_planning, 'get_summary', return_value={}, autospec=True)
    def test_filters_get_commas(self, mock_func):
        r = self.client.get(
            reverse('inventory_planning', kwargs=dict(breakdown='summary')) + '?c=1,2&p=3,4&d=5,6&s=7,8',
        )
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({'country': ['1', '2'], 'publisher': ['3', '4'], 'device_type': [5, 6], 'source_id': [7, 8]})

    @mock.patch.object(dash.features.inventory_planning, 'get_summary', return_value={}, autospec=True)
    def test_filters_post(self, mock_func):
        r = self.client.post(
            reverse('inventory_planning', kwargs=dict(breakdown='summary')),
            data={'c': ['1', '2'], 'p': ['3', '4'], 'd': [5, 6], 's': [7, 8]},
            format='json'
        )
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({'country': ['1', '2'], 'publisher': ['3', '4'], 'device_type': [5, 6], 'source_id': [7, 8]})
