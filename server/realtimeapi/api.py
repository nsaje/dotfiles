from django.conf import settings
from pydruid.client import PyDruid
from pydruid.utils.aggregators import count
from pydruid.utils.aggregators import doublesum
from pydruid.utils.aggregators import filtered
from pydruid.utils.aggregators import longsum
from pydruid.utils.filters import Bound
from pydruid.utils.filters import Dimension
from pydruid.utils.filters import Filter
from pydruid.utils.having import Having
from pydruid.utils.postaggregator import Const
from pydruid.utils.postaggregator import Field

from utils import dates_helper

from . import constants

WINNOTICE_DATASOURCES = ["b1-lcl-winnotice1-ny", "b1-lcl-winnotice1-chi"]
CLICK_DATASOURCES = ["r1-click-ny"]

INTERVAL_TEMPLATE = "{from_:%Y-%m-%dT%H:%M:%S}/{to:%Y-%m-%dT%H:%M:%S}"

MARKER_LIMIT_ORDER = "numeric"


def groupby(
    *, breakdown=None, marker=None, limit=100, account_id=None, campaign_id=None, ad_group_id=None, content_ad_id=None
):
    if not breakdown:
        breakdown = []

    assert all(dimension in constants.ValidGroupByBreakdown.get_all() for dimension in breakdown), "invalid dimension"

    client = _get_client()
    filter_, limit_spec = _prepare_groupby_pagination(
        breakdown=breakdown,
        marker=marker,
        limit=limit,
        account_id=account_id,
        campaign_id=campaign_id,
        ad_group_id=ad_group_id,
        content_ad_id=content_ad_id,
    )
    query = client.groupby(
        datasource=WINNOTICE_DATASOURCES + CLICK_DATASOURCES,  # union datasource
        dimensions=breakdown,
        granularity="all",
        intervals=_get_current_day_interval(),
        aggregations=_prepare_aggregations(),
        post_aggregations=_prepare_post_aggregations(),
        filter=filter_,
        limit_spec=limit_spec,
        having=_prepare_groupby_having(breakdown),
    )

    return [row["event"] for row in query.result]


def _prepare_groupby_pagination(*, breakdown, marker, limit, account_id, campaign_id, ad_group_id, content_ad_id):
    filter_ = None
    entity_filter = _prepare_entity_filter(
        account_id=account_id, campaign_id=campaign_id, ad_group_id=ad_group_id, content_ad_id=content_ad_id
    )
    if entity_filter:
        filter_ = (filter_ or Filter(type="and", fields=[])) & entity_filter
    marker_filter, limit_spec = _prepare_marker_limit(breakdown, marker, limit)
    if marker_filter:
        filter_ = (filter_ or Filter(type="and", fields=[])) & marker_filter
    return filter_, limit_spec


def _prepare_marker_limit(breakdown, marker, limit):
    filter_ = _prepare_marker_filter(breakdown, marker)
    limit_spec = _prepare_limit_spec(breakdown, limit)
    return filter_, limit_spec


def _prepare_limit_spec(breakdown, limit):
    # NOTE: pydruid has no abstraction for limit specs, has to be assembled manually
    return {
        "type": "default",
        "limit": limit,
        "columns": [
            {"dimension": col, "direction": "ascending", "dimensionOrder": MARKER_LIMIT_ORDER} for col in breakdown
        ],
    }


def _prepare_marker_filter(breakdown, marker):
    assert len(breakdown) == 1, "marker pagination for multiple dimensions not supported"
    if not marker:
        return None

    return Bound(breakdown[0], lower=marker, lowerStrict=True, ordering=MARKER_LIMIT_ORDER)


def _prepare_groupby_having(breakdown):
    assert len(breakdown) == 1

    return Having(type="filter", filter=Filter.build_filter(Dimension(breakdown[0]) != None))  # noqa: E711


def topn(*, breakdown, order, limit=100, campaign_id=None, ad_group_id=None, content_ad_id=None):
    # TODO: IMPORTANT - check why union datasources don't work well with topn

    # NOTE: topn is an optimization for cases when getting approximate top K results is good
    # enough - doesn't guarantee complete accuracy. The query has to be aggregated by a single
    # dimension and uses single metric for sorting.

    if not breakdown:
        breakdown = []

    assert len(breakdown) == 1, "multiple dimensions not supported"
    assert all(dimension in constants.ValidTopNBreakdown.get_all() for dimension in breakdown), "invalid dimension"
    assert limit <= 1000, "limit too high"

    filter_ = _prepare_entity_filter(campaign_id=campaign_id, ad_group_id=ad_group_id, content_ad_id=content_ad_id)

    client = _get_client()
    query = client.topn(
        datasource=WINNOTICE_DATASOURCES + CLICK_DATASOURCES,  # union datasource
        dimension=breakdown[0],
        granularity="all",
        intervals=_get_current_day_interval(),
        aggregations=_prepare_aggregations(),
        post_aggregations=_prepare_post_aggregations(),
        filter=filter_,
        threshold=limit,
        metric=_prepare_topn_metric(order),  # NOTE: used for sorting
    )

    return query.result[0]["result"]


def _prepare_topn_metric(order):
    inverted = False
    if order.startswith("-"):
        inverted = True
        order = order[1:]
    metric_spec = {"type": "numeric", "metric": order}
    if inverted:
        return {"type": "inverted", "metric": metric_spec}
    return metric_spec


def _get_current_day_interval():
    from_ = dates_helper.local_midnight_to_utc_time()
    to = dates_helper.day_after(from_)

    return INTERVAL_TEMPLATE.format(from_=from_, to=to)


def _prepare_aggregations():
    return {
        "impressions": longsum("impressions"),
        "clicks": filtered(
            (Dimension("account_id_filter") != None)
            & (Dimension("blacklisted") != "true")
            & (Dimension("publisher") != ""),  # noqa: E711
            count("account_id_filter"),
        ),
        "price_nano": doublesum("billing_price_sum"),
        "data_price_nano": doublesum("billing_data_price_sum"),
    }


def _prepare_post_aggregations():
    return {"spend": (Field("price_nano") + Field("data_price_nano")) / Const("1000000000.0")}


def _prepare_entity_filter(account_id=None, campaign_id=None, ad_group_id=None, content_ad_id=None):
    filter_ = Filter(type="and", fields=[])
    if account_id:
        filter_ &= Dimension("account_id") == account_id
    if campaign_id:
        filter_ &= Dimension("campaign_id") == campaign_id
    if ad_group_id:
        filter_ &= Dimension("ad_group_id") == ad_group_id
    if content_ad_id:
        filter_ &= Dimension("content_ad_id") == content_ad_id

    if not filter_.filter["filter"]["fields"]:
        # NOTE: ideally pydruid would remove a filter at query time if it's empty but it does not
        # and it breaks the query, so this is done manually by returning None here and checking it
        # before applying it
        return None
    return filter_


def _get_client():
    client = PyDruid(settings.DRUID_HOST, "druid/v2/")
    if settings.DRUID_USERNAME:
        client.set_basic_auth_credentials(settings.DRUID_USERNAME, settings.DRUID_PASSWORD)
    return client
