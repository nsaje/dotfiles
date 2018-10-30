from __future__ import unicode_literals

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.test import override_settings
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from utils.magic_mixer import magic_mixer

from .throttling import UserRateOverrideThrottle


class User3SecRateThrottle(UserRateOverrideThrottle):
    rate = "3/sec"
    scope = "seconds"


class MockView(APIView):
    throttle_classes = (User3SecRateThrottle,)

    def get(self, request):
        return Response("foo")


class ThrottlingTests(TestCase):
    def setUp(self):
        """
        Reset the cache so that no throttles will be active
        """
        cache.clear()
        self.factory = APIRequestFactory()
        self.backup_settings = settings.REST_FRAMEWORK.copy()

    def tearDown(self):
        settings.REST_FRAMEWORK = self.backup_settings

    def test_is_throttled(self):
        self.ensure_is_throttled(MockView, 200)

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_RATES": {"user": "3/s"},
            "DEFAULT_OVERRIDE_THROTTLE_RATES": {"b@x.com": "1/s"},
        }
    )
    def ensure_is_throttled(self, view, expect):
        user_a = magic_mixer.blend_user()
        user_b = magic_mixer.blend_user()
        user_service = magic_mixer.blend_user()
        user_a.email = "a@x.com"
        user_b.email = "b@x.com"
        user_service.email = "test-service@service.zemanta.com"

        request = self.factory.get("/")
        request.user = user_a
        for dummy in range(3):
            response = view.as_view()(request)
            self.assertEqual(response.status_code, 200)
        response = view.as_view()(request)
        self.assertEqual(response.status_code, 429)

        request.user = user_b
        response = view.as_view()(request)
        self.assertEqual(response.status_code, 200)
        response = view.as_view()(request)
        self.assertEqual(response.status_code, 429)

        request = self.factory.get("/")
        request.user = user_service
        for dummy in range(10):
            response = view.as_view()(request)
            self.assertEqual(response.status_code, 200)
