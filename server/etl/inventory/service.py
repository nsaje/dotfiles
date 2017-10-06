import logging
import backtosql

from django.core.cache import caches

from redshiftapi import db
from etl import maintenance
import dash.features.geolocation
import dash.constants


logger = logging.getLogger(__name__)


TABLE_NAME = 'mv_inventory'
CACHE_NAME = 'inventory_planning'


def refresh_inventory_data(date_from, date_to, skip_vacuum=False):
    valid_country_codes = list(dash.features.geolocation.Geolocation.objects.filter(
        type=dash.constants.LocationType.COUNTRY
    ).values_list('key', flat=True))

    sql = backtosql.generate_sql(
        'etl_aggregate_inventory_data.sql',
        {'valid_country_codes': valid_country_codes}
    )

    with db.get_stats_cursor() as c:
        maintenance.truncate(TABLE_NAME)

        logger.info('Starting materialization of table %s', TABLE_NAME)
        c.execute(sql, {
            'date_from': date_from,
            'date_to': date_to,
            'valid_country_codes': valid_country_codes,
        })
        logger.info('Finished materialization of table %s', TABLE_NAME)

        logger.info('Clearing %s cache', CACHE_NAME)
        _clear_cache(CACHE_NAME)
        logger.info('Clearing cache successful')

        maintenance.vacuum(TABLE_NAME)
        maintenance.analyze(TABLE_NAME)


def _clear_cache(cache_name):
    cache = caches[cache_name]
    cache.clear()
