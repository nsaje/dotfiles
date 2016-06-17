import influx

from contextlib import contextmanager

from etl import daily_statements_k1
from etl import materialize_k1
from etl import materialize_views


MATERIALIZED_VIEWS = [
    materialize_k1.ContentAdStats(),
    materialize_k1.Publishers(),
    materialize_k1.TouchpointConversions(),

    # Views that help construct master view
    materialize_views.MVHelpersAdGroupStructure(),
    materialize_views.MVHelpersCampaignFactors(),
    materialize_views.MVHelpersSource(),
    materialize_views.MVHelpersNormalizedStats(),

    materialize_views.MasterView(),

    # Derived views from master - from broder to narrower breakdown
    materialize_views.MVAdGroupDelivery(),
    materialize_views.MVCampaignDelivery(),
    materialize_views.MVAccountDelivery(),
    materialize_views.MVAdGroup(),
    materialize_views.MVCampaign(),
    materialize_views.MVAccount(),
]


def refresh_k1_reports(update_since):
    influx.incr('etl.refresh_k1.refresh_k1_reports', 1)

    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date())

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], dates[-1]

    for mv in MATERIALIZED_VIEWS:
        with influx.block_timer('etl.refresh_k1.generate_table', table=mv.table_name()):
            mv.generate(date_from, date_to, campaign_factors=effective_spend_factors)
