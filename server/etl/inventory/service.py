from django.core.cache import caches
from django.db.models import Q

import backtosql
import core.models
import dash.constants
import dash.features.geolocation
import dash.features.inventory_planning.nas
from etl import maintenance
from redshiftapi import db
from utils import zlogging

logger = zlogging.getLogger(__name__)


TABLE_NAME = "mv_inventory"
CACHE_NAME = "inventory_planning"

NATIVE_AD_SERVER_IDS = dash.features.inventory_planning.nas.NAS_MAPPING.keys()


def refresh_inventory_data(date_from, date_to):
    valid_country_codes = list(
        dash.features.geolocation.Geolocation.objects.filter(type=dash.constants.LocationType.COUNTRY).values_list(
            "key", flat=True
        )
    )
    source_slug_to_id = {
        s.bidder_slug: s.id
        for s in core.models.Source.objects.filter(
            Q(deprecated=False) & (Q(released=True) | Q(id__in=NATIVE_AD_SERVER_IDS))
        )
    }

    sql = backtosql.generate_sql(
        "etl_aggregate_inventory_data.sql",
        {"valid_country_codes": valid_country_codes, "source_slug_to_id": source_slug_to_id},
    )

    with db.get_write_stats_cursor() as c:
        maintenance.truncate(TABLE_NAME)

        logger.info("Starting materialization of table", table=TABLE_NAME)
        c.execute(sql, {"date_from": date_from, "date_to": date_to})
        logger.info("Finished materialization of table", table=TABLE_NAME)

        logger.info("Clearing cache", cache=CACHE_NAME)
        _clear_cache(CACHE_NAME)
        logger.info("Clearing cache successful")

        maintenance.vacuum(TABLE_NAME)
        maintenance.analyze(TABLE_NAME)


def _clear_cache(cache_name):
    cache = caches[cache_name]
    cache.clear()
