import json

from django.test import TestCase
from django.core.urlresolvers import reverse


class TestTestData(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get(self):
        params = {
            'breakdowns': 'ad_group,date,age',
            'ranges': '1|10,1|10,1|10'
        }

        response = self.client.get(
            reverse('stats_test_data'),
            params,
            follow=True
        )

        result = json.loads(response.content)

        self.assertTrue(result['success'])



