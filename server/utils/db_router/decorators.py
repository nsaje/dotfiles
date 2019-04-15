import functools

import utils.request_context


class _database_router_base(object):
    def __call__(self, func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return inner


class use_read_replica(_database_router_base):
    def __enter__(self):
        utils.request_context.set("USE_READ_REPLICA", True)

    def __exit__(self, exc_type, exc_value, traceback):
        utils.request_context.set("USE_READ_REPLICA", None)


class use_stats_read_replica(_database_router_base):
    def __enter__(self):
        utils.request_context.set("USE_STATS_READ_REPLICA", True)

    def __exit__(self, exc_type, exc_value, traceback):
        utils.request_context.set("USE_STATS_READ_REPLICA", None)


class use_stats_read_replica_postgres(_database_router_base):
    def __init__(self, should_use_postgres=True):
        self.should_use_postgres = should_use_postgres

    def __enter__(self):
        utils.request_context.set("USE_STATS_READ_REPLICA_POSTGRES", self.should_use_postgres)

    def __exit__(self, exc_type, exc_value, traceback):
        utils.request_context.set("USE_STATS_READ_REPLICA_POSTGRES", None)
