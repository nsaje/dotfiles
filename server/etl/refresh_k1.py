import influx
import datetime
import random
import string
import logging

from django.core.cache import caches
import dash.models

from etl import daily_statements_k1
from etl import materialize_k1
from etl import materialize_views


logger = logging.getLogger(__name__)

MATERIALIZED_VIEWS = [
    materialize_k1.ContentAdStats,
    materialize_k1.Publishers,
    materialize_k1.TouchpointConversions,
]

NEW_MATERIALIZED_VIEWS = [
    # Views that help construct master view
    materialize_views.MVHelpersSource,
    materialize_views.MVHelpersAdGroupStructure,
    materialize_views.MVHelpersCampaignFactors,
    materialize_views.MVHelpersNormalizedStats,

    materialize_views.MasterView,
    materialize_views.MasterPublishersView,

    materialize_views.MVConversions,
    materialize_views.MVTouchpointConversions,

    # Derived views from master - from broder to narrower breakdown
    materialize_views.MVContentAdDeliveryGeo,
    materialize_views.MVContentAdDeliveryDemo,
    materialize_views.MVAdGroupDeliveryGeo,
    materialize_views.MVAdGroupDeliveryDemo,
    materialize_views.MVCampaignDeliveryGeo,
    materialize_views.MVCampaignDeliveryDemo,
    materialize_views.MVAccountDeliveryGeo,
    materialize_views.MVAccountDeliveryDemo,
    materialize_views.MVContentAd,
    materialize_views.MVAdGroup,
    materialize_views.MVCampaign,
    materialize_views.MVAccount,

    # Derived views from publishers master
    materialize_views.MVPublishersAdGroup,

    materialize_views.MVTouchpointAccount,
    materialize_views.MVTouchpointCampaign,
    materialize_views.MVTouchpointAdGroup,
    materialize_views.MVTouchpointContentAd,

    materialize_views.MVConversionsAccount,
    materialize_views.MVConversionsCampaign,
    materialize_views.MVConversionsAdGroup,
    materialize_views.MVConversionsContentAd,
]


ALL_MATERIALIZED_VIEWS = MATERIALIZED_VIEWS + NEW_MATERIALIZED_VIEWS


@influx.timer('etl.refresh_k1.refresh_k1_timer', type='all')
def refresh_k1_reports(update_since, account_id=None):
    _refresh_k1_reports(update_since, ALL_MATERIALIZED_VIEWS, account_id)


@influx.timer('etl.refresh_k1.refresh_k1_timer', type='only_new')
def refresh_k1_new_reports(update_since, account_id=None):
    _refresh_k1_reports(update_since, NEW_MATERIALIZED_VIEWS, account_id)


def _refresh_k1_reports(update_since, views, account_id=None):
    influx.incr('etl.refresh_k1.refresh_k1_reports', 1)

    if account_id:
        validate_can_reprocess_account(account_id)

    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date(), account_id)

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], dates[-1]
    job_id = generate_job_id(account_id)

    logger.info('Starting refresh k1 reports job %s for date range %s - %s', job_id, date_from, date_to)

    for mv_class in views:
        with influx.block_timer('etl.refresh_k1.generate_table', table=mv_class.TABLE_NAME):
            mv = mv_class(job_id, date_from, date_to, account_id=account_id)
            mv.generate(campaign_factors=effective_spend_factors)

    influx.incr('etl.refresh_k1.refresh_k1_reports_finished', 1)
    # while everything is being updated data is not consistent among tables
    # so might as well leave cache until refresh finishes
    invalidate_breakdowns_rs_cache()


def generate_job_id(account_id):
    epoch = datetime.datetime.utcfromtimestamp(0)
    timestamp = int((datetime.datetime.now() - epoch).total_seconds() * 1000)

    rnd_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

    if account_id:
        return "{}_A{}_{}".format(timestamp, account_id, rnd_str)

    return "{}_{}".format(timestamp, rnd_str)


def invalidate_breakdowns_rs_cache():
    cache = caches['breakdowns_rs']
    cache.clear()


def validate_can_reprocess_account(account_id):
    # check account exists
    dash.models.Account.objects.get(pk=account_id)

    if not dash.models.AdGroup.objects.filter(campaign__account_id=account_id).exists():
        raise Exception("No ad groups exist for the selected account (pk={})".format(account_id))
