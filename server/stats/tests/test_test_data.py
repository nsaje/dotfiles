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
            'level-1': 'ad_group',
            'level-2': 'date',
            'level-3': 'age',
            'level-1-pagination': '1|10',
            'level-2-pagination': '1|10',
            'level-3-pagination': '1|10',
        }

        response = self.client.get(
            reverse('stats_test_data'),
            params,
            follow=True
        )

        result = json.loads(response.content)

        print response.content
        assert False



