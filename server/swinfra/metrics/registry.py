import prometheus_client

_registry = prometheus_client.REGISTRY


def get_registry():
    return _registry


def set_registry(registry):
    global _registry
    _registry = registry
