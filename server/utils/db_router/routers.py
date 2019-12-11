import itertools
import random

from django.conf import settings

import dash.constants
import utils.request_context

from . import pg_replica_lag

DEFAULT_DB_ALIAS = "default"
STATS_DB_HOT_CLUSTER = settings.STATS_DB_HOT_CLUSTER


class NoHealthyDatabaseException(Exception):
    pass


def _get_database_generator(settings_key, default_db_alias=None):
    dbs = getattr(settings, settings_key)
    if dbs:
        dbs = list(dbs)
        random.shuffle(dbs)
        return itertools.cycle(dbs)
    else:
        return itertools.repeat(default_db_alias)


read_replicas = _get_database_generator("DATABASE_READ_REPLICAS", DEFAULT_DB_ALIAS)
stats_db_postgres = _get_database_generator("STATS_DB_POSTGRES", STATS_DB_HOT_CLUSTER)
stats_db_cold_clusters = _get_database_generator("STATS_DB_COLD_CLUSTERS")


class UseReadReplicaRouter(object):
    def db_for_read(self, model, **hints):
        use_read_replica = utils.request_context.get("USE_READ_REPLICA", False)
        return (
            _get_database_for_current_request(read_replicas, [pg_replica_lag.is_replica_healthy])
            if use_read_replica
            else DEFAULT_DB_ALIAS
        )

    def db_for_write(self, model, **hints):
        return DEFAULT_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == DEFAULT_DB_ALIAS


class UseStatsDatabaseRouter(object):
    def db_for_read(self, model, **hints):
        stats_database_type = utils.request_context.get("STATS_DATABASE_TYPE")
        if stats_database_type == dash.constants.StatsDatabaseType.POSTGRES:
            return _get_database_for_current_request(stats_db_postgres)
        return (
            STATS_DB_HOT_CLUSTER
            if stats_database_type == dash.constants.StatsDatabaseType.HOT_CLUSTER
            else _get_database_for_current_request(stats_db_cold_clusters)
        )

    def db_for_write(self, model, **hints):
        return STATS_DB_HOT_CLUSTER

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return False


def _get_database_for_current_request(database_generator, additional_checks=None):
    """ pins to one database for the duration of the request """
    database_key = f"_request_replica_{database_generator}"
    request_database = utils.request_context.get(database_key)
    if not request_database:
        request_database = _pick_healthy_database(database_generator, additional_checks)
        utils.request_context.set(database_key, request_database)
    return request_database


def _pick_healthy_database(database_generator, additional_checks):
    invalid = set()
    while True:
        request_database = next(database_generator)
        if request_database in invalid:
            raise NoHealthyDatabaseException()
        checks = additional_checks or []
        if not all(check(request_database) for check in checks):
            invalid.add(request_database)
        else:
            return request_database
