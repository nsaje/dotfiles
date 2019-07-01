from unittest import mock

from django.test import TestCase

from . import push
from . import registry


class PushTest(TestCase):
    @mock.patch("prometheus_client.pushadd_to_gateway")
    def test_basic(self, mock_pushadd):
        push.start_push_mode("mygateway:8000", 15, "my-job", push_periodically=False)
        push.flush_push_metrics()
        mock_pushadd.assert_called_once_with("mygateway:8000", job="my-job", registry=registry.get_registry())
