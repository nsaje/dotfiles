import mock
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.test import TestCase

from dash import models as dashmodels


class TestDashSignals(TestCase):

    fixtures = ['test_user.yaml'] 

    def test_no_request_available(self):
        with self.assertRaises(IntegrityError):
            dashmodels.Account(name='test account name').save()

    @mock.patch('dash.signals.get_request')
    def test_request_available(self, mock_get_request):
        mock_request = mock.Mock()
        mock_request.user = User.objects.get(username='tomaz')
        mock_get_request.return_value = mock_request
        raise Exception
        dashmodels.Account(name='test account name 2').save()
        self.assertEqual(dashmodels.Account.objects.get(name='test account name 2').changed_by.username,'tomaz')
