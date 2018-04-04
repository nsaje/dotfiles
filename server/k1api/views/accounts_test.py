import json


from django.core.urlresolvers import reverse

import dash.features.geolocation
import dash.features.ga
import dash.constants
import dash.models

import logging

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AccountsTest(K1APIBaseTest):

    def test_get_accounts(self):
        response = self.client.get(
            reverse('k1api.accounts'),
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']
        self.assertEqual(len(data), dash.models.Account.objects.count())

    def test_get_accounts_with_id(self):
        response = self.client.get(
            reverse('k1api.accounts'), {'account_ids': 1},
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], {
            'id': 1,
            'name': 'test account 1',
            'outbrain_marketer_id': 'abcde',
            'custom_audiences': [
                {'pixel_id': 1,
                 'rules': [
                     {'type': 1, 'values': 'dummy', 'id': 1},
                     {'type': 2, 'values': 'dummy2', 'id': 2}],
                 'name': 'Audience 1',
                 'id': 1,
                 'ttl': 90},
                {'pixel_id': 2,
                 'rules': [
                     {'type': 1, 'values': 'dummy3', 'id': 3},
                     {'type': 2, 'values': 'dummy4', 'id': 4}],
                 'name': 'Audience 2',
                 'id': 2,
                 'ttl': 60}],
            'pixels': [
                {'id': 1,
                 'name': 'Pixel 1',
                 'slug': 'testslug1',
                 'audience_enabled': False,
                 'additional_pixel': False,
                 'source_pixels': [
                     {'url': 'http://www.ob.com/pixelendpoint',
                      'source_pixel_id': 'ob_zem1',
                      'source_type': 'outbrain',
                      },
                     {'url': 'http://www.y.com/pixelendpoint',
                      'source_pixel_id': 'y_zem1',
                      'source_type': 'yahoo',
                      },
                     {'url': 'http://www.fb.com/pixelendpoint',
                      'source_pixel_id': 'fb_zem1',
                      'source_type': 'facebook',
                      },
                 ]},
                {'id': 2,
                 'name': 'Pixel 2',
                 'slug': 'testslug2',
                 'audience_enabled': True,
                 'additional_pixel': False,
                 'source_pixels': [
                     {'url': 'http://www.xy.com/pixelendpoint',
                      'source_pixel_id': 'xy_zem2',
                      'source_type': 'taboola',
                      },
                     {'url': 'http://www.y.com/pixelendpoint',
                      'source_pixel_id': 'y_zem2',
                      'source_type': 'yahoo',
                      },
                     {'url': 'http://www.fb.com/pixelendpoint',
                      'source_pixel_id': 'fb_zem2',
                      'source_type': 'facebook',
                      },
                 ]},
            ]})

    def test_get_custom_audience(self):
        response = self.client.get(
            reverse('k1api.accounts'),
            {'account_ids': 1},
        )

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        accounts_data = json_data['response']
        self.assertEqual(1, len(accounts_data))
        data = accounts_data[0]['custom_audiences']

        self.assertEqual(2, len(data))
        self.assertEqual(data, [{
            'id': 1,
            'name': 'Audience 1',
            'pixel_id': 1,
            'rules': [
                {'id': 1,
                 'type': 1,
                 'values': 'dummy',
                 },
                {'id': 2,
                 'type': 2,
                 'values': 'dummy2',
                 },
            ],
            'ttl': 90,
        }, {
            'id': 2,
            'name': 'Audience 2',
            'pixel_id': 2,
            'rules': [
                {'id': 3,
                 'type': 1,
                 'values': 'dummy3',
                 },
                {'id': 4,
                 'type': 2,
                 'values': 'dummy4',
                 },
            ],
            'ttl': 60,
        }])
