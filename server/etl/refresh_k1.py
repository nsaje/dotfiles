import influx
import datetime
import random
import string
import logging

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

    materialize_views.MVConversions,
    materialize_views.MVTouchpointConversions,

    # Derived views from master - from broder to narrower breakdown
    materialize_views.MVContentAdDelivery,
    materialize_views.MVAdGroupDelivery,
    materialize_views.MVCampaignDelivery,
    materialize_views.MVAccountDelivery,
    materialize_views.MVContentAd,
    materialize_views.MVAdGroup,
    materialize_views.MVCampaign,
    materialize_views.MVAccount,

    materialize_views.MVTouchpointAccount,
    materialize_views.MVTouchpointCampaign,
    materialize_views.MVTouchpointAdGroup,
    materialize_views.MVTouchpointContentAd,

    materialize_views.MVConversionsAccount,
    materialize_views.MVConversionsCampaign,
    materialize_views.MVConversionsAdGroup,
    materialize_views.MVConversionsContentAd,
]


@influx.timer('etl.refresh_k1.refresh_k1_timer', type='all')
def refresh_k1_reports(update_since):
    influx.incr('etl.refresh_k1.refresh_k1_reports', 1)

    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date())

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], dates[-1]
    job_id = generate_job_id()

    for mv_class in MATERIALIZED_VIEWS + NEW_MATERIALIZED_VIEWS:
        with influx.block_timer('etl.refresh_k1.generate_table', table=mv_class.TABLE_NAME):
            mv = mv_class(job_id, date_from, date_to)
            mv.generate(campaign_factors=effective_spend_factors)


@influx.timer('etl.refresh_k1.refresh_k1_timer', type='only_new')
def refresh_k1_new_reports(update_since):
    influx.incr('etl.refresh_k1.refresh_k1_reports', 1)

    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date())

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], dates[-1]
    job_id = generate_job_id()

    logger.info('Starting refresh k1 reports job %s for date range %s - %s', job_id, date_from, date_to)

    for mv_class in NEW_MATERIALIZED_VIEWS:
        with influx.block_timer('etl.refresh_k1.generate_table', table=mv_class.TABLE_NAME):
            mv = mv_class(job_id, date_from, date_to)
            mv.generate(campaign_factors=effective_spend_factors)


def generate_job_id():
    epoch = datetime.datetime.utcfromtimestamp(0)
    timestamp = int((datetime.datetime.now() - epoch).total_seconds() * 1000)

    rnd_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

    return "{}_{}".format(timestamp, rnd_str)
