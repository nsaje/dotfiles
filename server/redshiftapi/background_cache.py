import influx
import pickle

from django.conf import settings
from django.core.cache import caches

from etl import materialization_run
from server import celery
from utils import dates_helper
from utils import db_for_reads

from . import api_breakdowns

cache = caches['redshift_background']


@influx.timer('redshift_background_cache.get_overhead')
def get(key):
    if not settings.USE_REDSHIFT_BACKGROUND_CACHE:
        return None

    cached_data, is_latest = _get(key)
    influx.incr('redshift_background_cache', 1, hit=str(cached_data is not None), latest=str(is_latest))

    rows = None
    if cached_data is not None:
        influx.timing(
            'redshift_background_cache.data_delay',
            (dates_helper.utc_now() - cached_data['created_dt']).total_seconds(),
            latest=str(is_latest),
        )
        rows = cached_data['rows']
        if not is_latest:
            update.delay(key)

    return rows


def _get(key):
    is_latest = False
    cached_data = cache.get(key)
    if cached_data is not None:
        last_materialization_dt = materialization_run.get_latest_finished_dt()
        if last_materialization_dt is not None:
            is_latest = last_materialization_dt < cached_data['created_dt']
    return cached_data, is_latest


@influx.timer('redshift_background_cache.set_overhead')
def set(key, rows, args, kwargs):
    if not settings.USE_REDSHIFT_BACKGROUND_CACHE:
        return
    _set(key, rows, pickle.dumps((args, kwargs), protocol=2))  # FIXME(nsaje): remove protocol after py3 migration complete


def _set(key, rows, pickled_args):
    cache.set(key, {
        'created_dt': dates_helper.utc_now(),
        'rows': rows,
        'pickled_args': pickled_args,
    })


@celery.app.task(acks_late=True, name='redshift_background_cache', soft_time_limit=5 * 60)
@db_for_reads.use_stats_read_replica()
def update(key):
    cached_data, is_latest = _get(key)
    if is_latest:
        return

    if cached_data is None or 'pickled_args' not in cached_data:
        return

    args, kwargs = pickle.loads(cached_data['pickled_args'])

    influx.incr('redshift_background_cache.background_update', 1)
    rows = api_breakdowns.query(*args, **kwargs)
    _set(key, rows, cached_data['pickled_args'])
