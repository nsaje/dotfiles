import random
import itertools

from django.conf import settings

from decorator import get_thread_local


DEFAULT_DB_ALIAS = 'default'


dbs = getattr(settings, 'DATABASE_READ_REPLICAS')
if dbs:
    dbs = list(settings.DATABASE_READ_REPLICAS)
    random.shuffle(dbs)
    read_replicas = itertools.cycle(dbs)
else:
    read_replicas = itertools.repeat(DEFAULT_DB_ALIAS)


class UseReadReplicaRouter(object):

    def db_for_read(self, model, **hints):
        use_read_replica = get_thread_local('USE_READ_REPLICA', False)
        return next(read_replicas) if use_read_replica else DEFAULT_DB_ALIAS

    def db_for_write(self, model, **hints):
        return DEFAULT_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == DEFAULT_DB_ALIAS
