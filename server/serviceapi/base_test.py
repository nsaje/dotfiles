from django.conf.urls import url
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from . import base


class MockTestView(base.ServiceAPIBaseView):
    """ A subclass that doesn't define authentication methods should always return PermissionDenied """

    def get(self, request):
        pass


urlpatterns = [url(r"^test/$", MockTestView.as_view(), name="test.test")]


@override_settings(ROOT_URLCONF="serviceapi.base_test")
class TestUnauthenticated(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated(self):
        r = self.client.get(reverse("test.test"))
        self.assertEqual(r.status_code, 403)
