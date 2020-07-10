import time
from dataclasses import dataclass
from typing import Dict

import django.db

from utils import zlogging

logger = zlogging.getLogger(__name__)


@dataclass
class CacheEntry:
    timestamp: float
    replica_ok: bool


_replica_lag_cache: Dict[str, CacheEntry] = {}
MAX_REPLICA_LAG = 20.0
CACHE_TTL = 30.0


def is_replica_healthy(db: str) -> bool:
    cache_entry = _replica_lag_cache.get(db)
    if not cache_entry or cache_entry.timestamp < time.time() - CACHE_TTL:
        replica_lag = _get_lag_from_db(db)
        replica_ok = replica_lag < MAX_REPLICA_LAG
        _replica_lag_cache[db] = CacheEntry(time.time(), replica_ok)
        return replica_ok
    else:
        return cache_entry.replica_ok


def _get_lag_from_db(db: str) -> float:
    with django.db.connections[db].cursor() as cursor:
        cursor.execute("select inet_server_addr()")
        row = cursor.fetchone()
        db_ip = row[0] or "NA"
        logger.info("Get lag from DB %s at IP %s", db, db_ip)
        cursor.execute("SELECT extract(epoch from now() - pg_last_xact_replay_timestamp()) AS slave_lag")
        row = cursor.fetchone()
    return row[0] or 0.0
