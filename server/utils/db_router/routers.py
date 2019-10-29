import itertools
import random

from django.conf import settings

import utils.request_context

from . import pg_replica_lag

DEFAULT_DB_ALIAS = "default"
DEFAULT_STATS_DB_ALIAS = settings.STATS_DB_NAME


class NoHealthyReplicasException(Exception):
    pass


def _get_read_replicas_generator(settings_key, default_db_alias):
    dbs = getattr(settings, settings_key)
    if dbs:
        dbs = list(dbs)
        random.shuffle(dbs)
        return itertools.cycle(dbs)
    else:
        return itertools.repeat(default_db_alias)


read_replicas = _get_read_replicas_generator("DATABASE_READ_REPLICAS", DEFAULT_DB_ALIAS)
stats_read_replicas = _get_read_replicas_generator("STATS_DB_READ_REPLICAS", DEFAULT_STATS_DB_ALIAS)
stats_read_replicas_postgres = _get_read_replicas_generator("STATS_DB_READ_REPLICAS_POSTGRES", DEFAULT_STATS_DB_ALIAS)


class UseReadReplicaRouter(object):
    def db_for_read(self, model, **hints):
        use_read_replica = utils.request_context.get("USE_READ_REPLICA", False)
        return (
            _get_replica_for_current_request(read_replicas, [pg_replica_lag.is_replica_healthy])
            if use_read_replica
            else DEFAULT_DB_ALIAS
        )

    def db_for_write(self, model, **hints):
        return DEFAULT_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == DEFAULT_DB_ALIAS


class UseStatsReadReplicaRouter(object):
    def db_for_read(self, model, **hints):
        use_read_replica_postgres = utils.request_context.get("USE_STATS_READ_REPLICA_POSTGRES", False)
        if use_read_replica_postgres:
            return _get_replica_for_current_request(stats_read_replicas_postgres)
        use_read_replica = utils.request_context.get("USE_STATS_READ_REPLICA", False)
        return _get_replica_for_current_request(stats_read_replicas) if use_read_replica else DEFAULT_STATS_DB_ALIAS

    def db_for_write(self, model, **hints):
        return DEFAULT_STATS_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return False


def _get_replica_for_current_request(replica_generator, additional_checks=None):
    """ pins to one replica for the duration of the request """
    replica_key = f"_request_replica_{replica_generator}"
    request_replica = utils.request_context.get(replica_key)
    if not request_replica:
        request_replica = _pick_healthy_replica(replica_generator, additional_checks)
        utils.request_context.set(replica_key, request_replica)
    return request_replica


def _pick_healthy_replica(replica_generator, additional_checks):
    invalid = set()
    while True:
        request_replica = next(replica_generator)
        if request_replica in invalid:
            raise NoHealthyReplicasException()
        checks = additional_checks or []
        if not all(check(request_replica) for check in checks):
            invalid.add(request_replica)
        else:
            return request_replica
