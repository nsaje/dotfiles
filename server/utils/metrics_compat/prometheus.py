import threading

import swinfra.metrics

__all__ = ["gauge", "incr", "timing"]


class CompatMetricStore:
    def __init__(self, factory):
        self.factory = factory
        self.store = {}
        self.lock = threading.Lock()

    def get_metric(self, name, tags):
        name = self._sanitize_name(name)
        metric = self.store.get(name)
        if not metric:
            with self.lock:
                if name not in self.store:
                    metric = self.factory(name, labelnames=tuple(tags.keys()))
                    self.store[name] = metric
                else:
                    metric = self.store.get(name)
        return metric

    @staticmethod
    def _sanitize_name(name):
        return name.replace(".", "_")


_gauge_store = CompatMetricStore(swinfra.metrics.new_gauge)
_counter_store = CompatMetricStore(swinfra.metrics.new_counter)
_histogram_store = CompatMetricStore(swinfra.metrics.new_histogram)


def gauge(name, value, **tags):
    metric = _gauge_store.get_metric(name, tags)
    if tags:
        metric = metric.labels(**tags)
    metric.set(value)


def incr(name, count, **tags):
    metric = _counter_store.get_metric(name, tags)
    if tags:
        metric = metric.labels(**tags)
    metric.inc(count)


def timing(name, seconds, **tags):
    metric = _histogram_store.get_metric(name, tags)
    if tags:
        metric = metric.labels(**tags)
    metric.observe(seconds)
