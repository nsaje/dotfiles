import mock

from django.core.urlresolvers import reverse

import restapi.views_test
import dash.features.inventory_planning


class InventoryPlanningViewTest(restapi.views_test.RESTAPITest):

    @mock.patch.object(dash.features.inventory_planning, 'get_summary', return_value={}, autospec=True)
    def test_summary(self, mock_func):
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='summary')))
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({})

    @mock.patch.object(dash.features.inventory_planning, 'get_by_country', return_value={}, autospec=True)
    def test_by_country(self, mock_func):
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='countries')))
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({})

    @mock.patch.object(dash.features.inventory_planning, 'get_by_device_type', return_value={}, autospec=True)
    def test_by_device_type(self, mock_func):
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='device-types')))
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({})

    @mock.patch.object(dash.features.inventory_planning, 'get_by_publisher', return_value={}, autospec=True)
    def test_by_publisher(self, mock_func):
        r = self.client.post(reverse('inventory_planning', kwargs=dict(breakdown='publishers')))
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({})

    @mock.patch.object(dash.features.inventory_planning, 'get_summary', return_value={}, autospec=True)
    def test_filters_get(self, mock_func):
        r = self.client.get(
            reverse('inventory_planning', kwargs=dict(breakdown='summary')),
            data={'c': ['1', '2'], 'p': ['3', '4'], 'd': [5, 6]}
        )
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({'country': ['1', '2'], 'publisher': ['3', '4'], 'device_type': [5, 6]})

    @mock.patch.object(dash.features.inventory_planning, 'get_summary', return_value={}, autospec=True)
    def test_filters_post(self, mock_func):
        r = self.client.post(
            reverse('inventory_planning', kwargs=dict(breakdown='summary')),
            data={'c': ['1', '2'], 'p': ['3', '4'], 'd': [5, 6]},
            format='json'
        )
        r = self.assertResponseValid(r)
        mock_func.assert_called_with({'country': ['1', '2'], 'publisher': ['3', '4'], 'device_type': [5, 6]})
