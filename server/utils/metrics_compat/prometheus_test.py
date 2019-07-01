from unittest import mock

from django.test import TestCase

from . import prometheus


class PrometheusTest(TestCase):
    @staticmethod
    def _get_mock_factory():
        factory = mock.Mock()
        factory.side_effect = lambda *args, **kwargs: mock.Mock()
        return factory

    def test_basic(self):
        factory = self._get_mock_factory()
        store = prometheus.CompatMetricStore(factory)
        metric = store.get_metric("a", dict(b=1, c=2))
        metric2 = store.get_metric("a", dict(b=1, c=2))
        factory.assert_called_once_with("a", labelnames=("b", "c"))
        self.assertEqual(metric, metric2)

    def test_different_labelvalues(self):
        factory = self._get_mock_factory()
        store = prometheus.CompatMetricStore(factory)
        metric = store.get_metric("a", dict(b=1, c=2))
        metric2 = store.get_metric("a", dict(b=3, c=4))
        factory.assert_called_once_with("a", labelnames=("b", "c"))
        self.assertEqual(metric, metric2)

    def test_different_names(self):
        factory = self._get_mock_factory()
        store = prometheus.CompatMetricStore(factory)
        metric = store.get_metric("a", dict(b=1, c=2))
        metric2 = store.get_metric("b", dict(b=3, c=4))
        factory.assert_has_calls([mock.call("a", labelnames=("b", "c")), mock.call("b", labelnames=("b", "c"))])
        self.assertNotEqual(metric, metric2)
