import datetime

from django.conf import settings
from django.db import connections
from django.db.models import F

import backtosql
import core.features.bcm.calculations
import dash.constants
import dash.models
import redshiftapi
import utils.converters
from utils import zlogging

from . import helpers
from . import redshift

logger = zlogging.getLogger(__name__)


def process_cpc_billing(from_date, to_date, agency_id):

    license_fee = (
        dash.models.CreditLineItem.objects.filter_active(to_date).filter(agency__id=agency_id).first().license_fee
    )

    ad_groups_w_cpc = (
        dash.models.AdGroupSource.objects.filter(
            ad_group__in=dash.models.AdGroup.objects.filter(campaign__account__agency_id=agency_id),
            source__cpc_billing=True,
        )
        .annotate(cpc_cc=F("settings__cpc_cc"))
        .values("ad_group_id", "cpc_cc")
    )

    ad_groups_cpc_micro = [(i["ad_group_id"], _calculate_cpc_micro(i["cpc_cc"], license_fee)) for i in ad_groups_w_cpc]
    _update_mvh_ad_groups_cpc(ad_groups_cpc_micro)
    _insert_stats_diff(from_date, to_date)


def check_discrepancy(from_date, to_date):
    if to_date == datetime.date.today():
        to_date = datetime.date.today() - datetime.timedelta(1)

    context = helpers.get_local_multiday_date_context(from_date, to_date)
    sql = backtosql.generate_sql("nas_spend_discrepency.sql", context)
    with connections[settings.STATS_DB_HOT_CLUSTER].cursor() as c:
        c.execute(sql)
        return redshiftapi.db.dictfetchall(c)


def _calculate_cpc_micro(cpc_value, fee, margin=0):
    cpc_media = core.features.bcm.calculations.subtract_fee_and_margin(cpc_value, fee, margin)
    return int(cpc_media * utils.converters.CURRENCY_TO_MICRO)


def _update_mvh_ad_groups_cpc(ad_groups_cpc_micro):
    redshift.delete_from_table("mvh_ad_groups_cpc")
    context = {"values": ",".join([str(i) for i in ad_groups_cpc_micro])}
    query = backtosql.generate_sql("insert_mvh_ad_groups_cpc.sql", context)
    with redshiftapi.db.get_write_stats_cursor() as cur:
        logger.info("Will insert data into table mvh_ad_groups_cpc.")
        cur.execute(query)
        logger.info("Data inserted into table mvh_ad_groups_cpc.")


def _insert_stats_diff(from_date, to_date):
    context = helpers.get_local_multiday_date_context(from_date, to_date)
    delete_query = backtosql.generate_sql("delete_stats_diff_with_tz.sql", context)
    insert_query = backtosql.generate_sql("insert_cpc_billing_stats_diff.sql", context)
    with redshiftapi.db.get_write_stats_cursor() as cur:
        logger.info("Will remove data in stats_diff between dates.", from_date=from_date, to_date=to_date)
        cur.execute(delete_query)
        logger.info("Done with removal.")
        logger.info("Will insert data into table stats_diff.")
        cur.execute(insert_query)
        logger.info("Data inserted into stats_diff.")
