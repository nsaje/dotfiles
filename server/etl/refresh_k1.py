from etl import daily_statements_k1
from etl import materialize_k1
from etl import materialize_views


MATERIALIZED_VIEWS = [
    materialize_k1.ContentAdStats(),
    materialize_k1.Publishers(),
    materialize_k1.TouchpointConversions(),
    materialize_views.MasterView(),
    materialize_views.MVAccount(),
    materialize_views.MVAccountDelivery(),
]


def refresh_k1_reports(update_since):
    effective_spend_factors = daily_statements_k1.reprocess_daily_statements(update_since.date())

    dates = sorted(effective_spend_factors.keys())
    date_from, date_to = dates[0], dates[-1]
    for mv in MATERIALIZED_VIEWS:
        mv.generate(date_from, date_to, effective_spend_factors)
