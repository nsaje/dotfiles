import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from zemauth.models import User

class TestTestData(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

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
