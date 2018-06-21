from django import test
from django.core.urlresolvers import reverse

from rest_framework.test import APIClient
from zemauth.models import User

import json


class UserViewTest(test.TestCase):

    def test_user_get(self):
        client = APIClient()
        user = User.objects.create_superuser('test@test.com', password='123')
        client.force_authenticate(user=user)
        r = client.get(reverse('user_details'))
        resp_json = json.loads(r.content)
        self.assertEqual(user.email, resp_json['email'])
        self.assertEqual(str(user.id), resp_json['id'])
        self.assertEqual(user.get_all_permissions_with_access_levels(), resp_json['permissions'])
