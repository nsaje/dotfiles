import datetime
from mock import patch

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.test import TestCase

from zemauth import devices
from zemauth import models

from utils import threads

MOCK_NOW = datetime.datetime(2017, 3, 20, 12)

TEST_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/31.0.163213123 Safari/537.36"
)


@patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
class DeviceCookieTestCase(TestCase):
    fixtures = ["test_users.yaml"]

    def setUp(self):
        self.user = models.User.objects.get(id=2)

        utc_now_patcher = patch("utils.dates_helper.utc_now")
        mock_utc_now = utc_now_patcher.start()
        mock_utc_now.return_value = MOCK_NOW
        self.addCleanup(utc_now_patcher.stop)

    @patch("utils.email_helper.send_new_user_device_email")
    def test_new_device_new_cookie(self, mock_send_email):
        request = HttpRequest()
        request.user = self.user
        request.META["HTTP_USER_AGENT"] = TEST_USER_AGENT

        response = HttpResponse()

        self.assertEqual(0, len(response.cookies))
        self.assertEqual(0, models.Device.objects.count())
        self.assertEqual(0, models.UserDevice.objects.count())
        devices.handle_user_device(request, response)

        self.assertEqual(1, len(response.cookies))
        device = models.Device.objects.get()
        user_device = models.UserDevice.objects.get()

        self.assertEqual(device.device_key, response.cookies[devices.DEVICE_COOKIE_NAME].value)
        self.assertEqual(device.expire_date, MOCK_NOW + devices.DEVICE_KEY_EXPIRY)
        self.assertEqual(user_device.user, self.user)
        self.assertEqual(user_device.device, device)
        self.assertTrue(mock_send_email.called)

    @patch("utils.email_helper.send_new_user_device_email")
    def test_known_device_new_user(self, mock_send_email):
        existing_device = models.Device.objects.create(
            device_key="a" * 32, expire_date=MOCK_NOW - datetime.timedelta(seconds=5 * 60) + devices.DEVICE_KEY_EXPIRY
        )
        existing_user = models.User.objects.get(id=1)
        models.UserDevice.objects.create(device=existing_device, user=existing_user)

        request = HttpRequest()
        request.user = self.user
        request.COOKIES[devices.DEVICE_COOKIE_NAME] = existing_device.device_key
        request.META["HTTP_USER_AGENT"] = TEST_USER_AGENT

        response = HttpResponse()

        self.assertEqual(0, len(response.cookies))
        self.assertEqual(1, models.Device.objects.count())
        self.assertEqual(1, models.UserDevice.objects.count())
        devices.handle_user_device(request, response)

        user_device = models.UserDevice.objects.get(user=self.user)
        self.assertEqual(1, len(response.cookies))
        self.assertEqual(user_device.device.device_key, response.cookies[devices.DEVICE_COOKIE_NAME].value)
        self.assertEqual(user_device.device, existing_device)
        self.assertEqual(
            user_device.device.expire_date, MOCK_NOW + devices.DEVICE_KEY_EXPIRY  # expire date was refreshed
        )
        self.assertEqual(user_device.user, self.user)
        self.assertTrue(mock_send_email.called)

    @patch("utils.email_helper.send_new_user_device_email")
    def test_known_device_existing_user(self, mock_send_email):
        existing_device = models.Device.objects.create(
            device_key="a" * 32, expire_date=MOCK_NOW - datetime.timedelta(seconds=5 * 60) + devices.DEVICE_KEY_EXPIRY
        )
        models.UserDevice.objects.create(device=existing_device, user=self.user)

        request = HttpRequest()
        request.user = self.user
        request.COOKIES[devices.DEVICE_COOKIE_NAME] = existing_device.device_key
        request.META["HTTP_USER_AGENT"] = TEST_USER_AGENT

        response = HttpResponse()

        self.assertEqual(0, len(response.cookies))
        self.assertEqual(1, models.Device.objects.count())
        self.assertEqual(1, models.UserDevice.objects.count())
        devices.handle_user_device(request, response)

        self.assertEqual(1, models.Device.objects.count())
        self.assertEqual(1, models.UserDevice.objects.count())

        user_device = models.UserDevice.objects.get(user=self.user)
        self.assertEqual(1, len(response.cookies))
        self.assertEqual(user_device.device.device_key, response.cookies[devices.DEVICE_COOKIE_NAME].value)
        self.assertEqual(user_device.device, existing_device)
        self.assertEqual(
            user_device.device.expire_date, MOCK_NOW - datetime.timedelta(seconds=5 * 60) + devices.DEVICE_KEY_EXPIRY
        )
        self.assertEqual(user_device.user, self.user)
        self.assertFalse(mock_send_email.called)
