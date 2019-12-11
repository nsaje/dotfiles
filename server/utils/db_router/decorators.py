import functools

import dash.constants
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


class use_stats_database(_database_router_base):
    def __init__(self, stats_database_type=dash.constants.StatsDatabaseType.POSTGRES):
        self.stats_database_type = stats_database_type

    def __enter__(self):
        utils.request_context.set("STATS_DATABASE_TYPE", self.stats_database_type)

    def __exit__(self, exc_type, exc_value, traceback):
        utils.request_context.set("STATS_DATABASE_TYPE", None)
