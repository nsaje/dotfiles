from django.test import TestCase
from mock import patch

import reach


class ReachTestCase(TestCase):

    @patch('dash.features.bluekai.service.bluekaiapi.get_segment_reach')
    def test_get_reach(self, mock_api_call):
        mock_api_call.return_value = pow(10, 9)

        result = reach.get_reach([])
        self.assertDictEqual(result, {'relative': 99, 'value': pow(10, 9)})

    @patch('dash.features.bluekai.service.bluekaiapi.get_segment_reach')
    def test_get_reach_error(self, mock_api_call):
        mock_api_call.side_effect = Exception()
        result = reach.get_reach([])
        self.assertEqual(result, None)

    def test_calcuate_relative_reach(self):
        relative = reach.calculate_relative_reach(87654321)
        self.assertEqual(relative, 89)
