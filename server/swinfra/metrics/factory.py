import prometheus_client

from . import registry

_project_name = None


def configure(project_name):
    global _project_name
    _project_name = project_name


def new_summary(name, labelnames, documentation=None, **kwargs):
    return _new_metric(prometheus_client.Summary, name, labelnames, documentation, **kwargs)


def new_histogram(name, labelnames, documentation=None, **kwargs):
    return _new_metric(prometheus_client.Histogram, name, labelnames, documentation, **kwargs)


def new_counter(name, labelnames, documentation=None, **kwargs):
    return _new_metric(prometheus_client.Counter, name, labelnames, documentation, **kwargs)


def new_gauge(name, labelnames, documentation=None, **kwargs):
    return _new_metric(prometheus_client.Gauge, name, labelnames, documentation, **kwargs)


def _new_metric(cls, name, labelnames, documentation, **kwargs):
    return cls(
        _build_name(name), documentation or "", labelnames=labelnames, registry=registry.get_registry(), **kwargs
    )


def _build_name(name):
    return f"{_project_name}_{name}"


try:
    from django.conf import settings

    configure(settings.PROJECT_NAME)
except Exception:
    pass
