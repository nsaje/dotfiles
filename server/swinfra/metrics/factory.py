import prometheus_client

_project_name = None


def configure(project_name):
    global _project_name
    _project_name = project_name


def new_summary(name, documentation=None, labelnames=None):
    return _new_metric(prometheus_client.Summary, name, documentation, labelnames)


def new_histogram(name, documentation=None, labelnames=None):
    return _new_metric(prometheus_client.Histogram, name, documentation, labelnames)


def new_counter(name, documentation=None, labelnames=None):
    return _new_metric(prometheus_client.Counter, name, documentation, labelnames)


def new_gauge(name, documentation=None, labelnames=None):
    return _new_metric(prometheus_client.Gauge, name, documentation, labelnames)


def _new_metric(cls, name, documentation, labelnames):
    return cls(_build_name(name), documentation or "", labelnames=labelnames)


def _build_name(name):
    return f"{_project_name}_{name}"


try:
    from django.conf import settings

    configure(settings.PROJECT_NAME)
except Exception:
    pass
