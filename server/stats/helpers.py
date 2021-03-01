import collections
import datetime

from django.db.models import Model
from django.db.models import QuerySet

import core.features.bid_modifiers
import dash.constants
import dash.models
from stats import constants
from stats import fields
from utils import exc
from utils import sort_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)

Goals = collections.namedtuple("Goals", "campaign_goals, conversion_goals, campaign_goal_values, pixels, primary_goals")


def get_goals(constraints, breakdown):
    campaign = constraints.get("campaign")
    account = constraints.get("account")

    campaign_goals, conversion_goals, campaign_goal_values, pixels = [], [], [], []
    primary_goals = []

    if campaign:
        conversion_goals = campaign.conversiongoal_set.all().select_related("pixel")
        campaign_goals = (
            campaign.campaigngoal_set.all()
            .order_by("-primary", "created_dt")
            .select_related("conversion_goal", "conversion_goal__pixel", "campaign", "campaign__account")
        )

        primary_goal = campaign_goals.first()
        if primary_goal:
            primary_goals = [primary_goal]

        campaign_goal_values = dash.campaign_goals.get_campaign_goal_values(campaign)

    elif "allowed_campaigns" in constraints and "account" in constraints and constants.CAMPAIGN in breakdown:
        # only take for campaigns when constraints for 1 account, otherwise its too much
        allowed_campaigns = constraints["allowed_campaigns"]
        conversion_goals = dash.models.ConversionGoal.objects.filter(campaign__in=allowed_campaigns).select_related(
            "pixel"
        )

        campaign_goals = (
            dash.models.CampaignGoal.objects.filter(campaign__in=allowed_campaigns)
            .order_by("-primary", "created_dt")
            .select_related("conversion_goal", "conversion_goal__pixel", "campaign", "campaign__account")
        )

        primary_goals_by_campaign = {}
        for cg in campaign_goals:
            if cg.campaign_id not in primary_goals_by_campaign:
                primary_goals_by_campaign[cg.campaign_id] = cg
        primary_goals = list(primary_goals_by_campaign.values())

        campaign_goal_values = dash.campaign_goals.get_campaigns_goal_values(allowed_campaigns)

    if account:
        pixels = account.conversionpixel_set.filter(archived=False)

    # force evaluation of querysets, otherwise we get "missing FROM-clause" error sporadically in threaded environments
    return Goals(
        list(campaign_goals), list(conversion_goals), list(campaign_goal_values), list(pixels), list(primary_goals)
    )


def extract_stats_constraints(constraints, breakdown):
    """
    Copy constraints and remove all that are not part of the stats query.

    # NOTE: try to keep constraints in order - eg. account_id always sorted the same way
    so that we get the same collection when the same parameters are use. This way we don't
    miss cache when we request the same data but order of parameters differs.
    """

    new_constraints = {
        "date__gte": constraints["date__gte"],
        "date__lte": constraints["date__lte"],
        "source_id": list(constraints["filtered_sources"].values_list("pk", flat=True).order_by("pk")),
        "account_id": (
            constraints["account"].id
            if "account" in constraints
            else list(constraints["allowed_accounts"].values_list("pk", flat=True).order_by("pk"))
        ),
    }

    if "ad_group" in constraints:
        new_constraints["ad_group_id"] = constraints["ad_group"].id
    elif "ad_group_id" in breakdown:
        new_constraints["ad_group_id"] = list(
            constraints["allowed_ad_groups"].values_list("pk", flat=True).order_by("pk")
        )

    if "campaign" in constraints:
        new_constraints["campaign_id"] = constraints["campaign"].id
    elif "campaign_id" in breakdown:
        new_constraints["campaign_id"] = list(
            constraints["allowed_campaigns"].values_list("pk", flat=True).order_by("pk")
        )

    if "account" in constraints:
        new_constraints["account_id"] = constraints["account"].id

    if "content_ad_id" in breakdown:
        new_constraints["content_ad_id"] = list(
            constraints["allowed_content_ads"].values_list("pk", flat=True).order_by("pk")
        )

    if ("publisher_id" in breakdown or "placement_id" in breakdown) and constraints[
        "publisher_blacklist_filter"
    ] != dash.constants.PublisherBlacklistFilter.SHOW_ALL:
        is_placement = constants.is_placement_breakdown(breakdown)
        constraints_entry_field = "placement_id" if is_placement else "publisher_id"
        if constraints["publisher_blacklist_filter"] == dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE:
            new_constraints[f"{constraints_entry_field}__neq"] = list(
                constraints["publisher_blacklist"]
                .filter_publisher_or_placement(is_placement)
                .annotate_entry_id(is_placement=is_placement)
                .values_list("entry_id", flat=True)
            )
        elif constraints["publisher_blacklist_filter"] == dash.constants.PublisherBlacklistFilter.SHOW_BLACKLISTED:
            new_constraints[constraints_entry_field] = list(
                constraints["publisher_blacklist"]
                .filter_publisher_or_placement(is_placement)
                .annotate_entry_id(is_placement=is_placement)
                .values_list("entry_id", flat=True)
            )
        elif constraints["publisher_blacklist_filter"] == dash.constants.PublisherBlacklistFilter.SHOW_WHITELISTED:
            new_constraints[constraints_entry_field] = list(
                constraints["publisher_whitelist"]
                .filter_publisher_or_placement(is_placement)
                .annotate_entry_id(is_placement=is_placement)
                .values_list("entry_id", flat=True)
            )

    return new_constraints


def decode_parents(breakdown, parents):
    """
    Returns a list of parsed breakdown_ids or None.
    """

    if not parents:
        return None

    return [decode_breakdown_id(breakdown, breakdown_id_str) for breakdown_id_str in parents]


def decode_breakdown_id(breakdown, breakdown_id_str):
    """
    Creates a dict with constraints from a breakdown id.

    Example:
    breakdown = [account, campaign, dma, day]
    breakdown_id_str = '1-2-500'

    Returns: {account_id: 1, campaign_id: 2, dma: '500'}
    """

    d = {}
    ids = breakdown_id_str.split("||")
    for i, dimension in enumerate(breakdown[: len(ids)]):
        str_id = ids[i]
        if str_id == "-None-":
            str_id = None
        elif dimension in constants.IntegerDimensions:
            str_id = int(str_id)

        d[dimension] = str_id

    return d


def encode_breakdown_id(breakdown, row):
    """
    Creates a breakdown id - string of consecutive ids separated by delimiter.

    Example:
    breakdown = [account, campaign, dma, day]
    row = {account_id: 1, campaign_id: 2, dma: '500', clicks: 123, ...}

    Returns: '1-2-500'
    """

    values = []
    for dim in breakdown:
        value = row[dim]

        if value is None:
            value = "-None-"

        values.append(str(value))

    return "||".join(values)


def get_breakdown_id(row, breakdown):
    # returns a dict where breakdown dimensions are keys and values are dimension values
    d = {}
    for dim in breakdown:
        d[dim] = row[dim]
    return d


def check_constraints_are_supported(constraints):
    """
    Checks whether constraints include only known keys of known types.
    This way we check for programming mistakes.
    """

    query_set_keys = [
        "filtered_sources",
        "filtered_agencies",
        "allowed_accounts",
        "allowed_campaigns",
        "allowed_ad_groups",
        "allowed_content_ads",
        "publisher_blacklist",
        "publisher_whitelist",
    ]

    if "filtered_sources" not in constraints:
        raise exc.UnknownFieldBreakdownError("Missing filtered sources")

    for key in query_set_keys:
        if key in constraints and not isinstance(constraints[key], QuerySet):
            raise exc.UnknownFieldBreakdownError("Value of '{}' should be a queryset".format(key))

    if "account" not in constraints and "allowed_accounts" not in constraints:
        raise exc.UnknownFieldBreakdownError("Constraints should include either 'account' or 'allowed_accounts")

    model_keys = ["account", "campaign", "ad_group"]
    for key in model_keys:
        if key in constraints and not isinstance(constraints[key], Model):
            raise exc.UnknownFieldBreakdownError("Value of '{}' should be a django Model".format(key))

    other_keys = [
        "show_archived",
        "filtered_account_types",
        "date__gte",
        "date__lte",
        "publisher_blacklist_filter",
        "publisher_group_targeting",
    ]
    unknown_keys = set(constraints.keys()) - set(query_set_keys) - set(model_keys) - set(other_keys)

    if unknown_keys:
        raise exc.UnknownFieldBreakdownError("Unknown fields in constraints {}".format(unknown_keys))


def extract_order_field(order, target_dimension, primary_goals=None):
    """
    Returns the order field that should be used to get visually pleasing results. Time is always
    shown ordered by time, so we don't get mixed dates etc.
    """

    # all time dimensions and age, age_gender, device_type are always sorted the same way
    if target_dimension in constants.TimeDimension._ALL or target_dimension in ("age", "age_gender", "device_type"):
        return "name"

    prefix, order_field = sort_helper.dissect_order(order)

    if order_field == "state":
        order_field = "status"

    if target_dimension != "content_ad_id" and order_field in fields.CONTENT_ADS_FIELDS:
        order_field = "name"

    if target_dimension != "source_id" and order_field in fields.SOURCE_FIELDS:
        order_field = "clicks"

    if order_field == "performance":
        if primary_goals:
            order_field = "etfm_performance_" + primary_goals[0].get_view_key()
        else:
            order_field = "clicks"

    if target_dimension in ("publisher_id", "placement_id"):
        if order_field == "status":
            order_field = "clicks"

        if order_field == "exchange":
            order_field = "source_id"

    return prefix + order_field


def extract_rs_order_field(order, target_dimension):
    """
    Converts order field to field name that is understood by redshiftapi.
    """

    prefix, order_field = sort_helper.dissect_order(order)

    if target_dimension in constants.TimeDimension._ALL or target_dimension in ("age", "age_gender", "device_type"):
        return prefix + target_dimension

    if target_dimension == "publisher_id" and order_field == "name":
        order_field = "publisher"

    if target_dimension == "placement_id" and order_field == "name":
        order_field = "placement"

    # all delivery dimensions are sorted by targeted dimension ids
    if target_dimension in constants.DeliveryDimension._ALL:
        if order_field == "name":
            order_field = target_dimension
        elif order_field in ("state", "status", "archived"):
            # delivery does not have status/archived etc,
            # so mimick with clicks - more clicks, more active :)
            order_field = "clicks"

    return prefix + order_field


def get_report_currency(user, accounts):
    if len(accounts) == 0:
        return dash.constants.Currency.USD

    currency_set = set(account.currency for account in accounts if account.currency)
    if len(currency_set) == 1:
        return currency_set.pop()
    else:
        return dash.constants.Currency.USD


def update_rows_to_contain_values_in_currency(rows, currency):
    if currency == dash.constants.Currency.USD:
        _strip_local_values_from_rows(rows)
        return
    update_rows_to_contain_local_values(rows)


def update_rows_to_contain_local_values(rows):
    for row in rows:
        for key in list(row.keys()):
            if key and key.startswith("local_"):
                non_local_key = key.replace("local_", "", 1)
                row[non_local_key] = row.pop(key, None)


def _strip_local_values_from_rows(rows):
    for row in rows:
        for key in list(row.keys()):
            if key and key.startswith("local_"):
                row.pop(key, None)


def update_with_refunds(row, refunds):
    media_amount, service_fee_amount, license_fee_amount, margin_amount = refunds
    for field in fields.PLATFORM_SPEND_REFUND_FIELDS:
        row[field] += media_amount + service_fee_amount
    for field in fields.SERVICE_FEE_REFUND_FIELDS:
        row[field] += service_fee_amount
    for field in fields.LICENSE_FEE_REFUND_FIELDS:
        row[field] += license_fee_amount
    for field in fields.MARGIN_REFUND_FIELDS:
        row[field] += margin_amount
    for field in fields.AGENCY_SPEND_REFUND_FIELDS:
        row[field] += media_amount + service_fee_amount + license_fee_amount
    for field in fields.TOTAL_SPEND_REFUND_FIELDS:
        row[field] += media_amount + service_fee_amount + license_fee_amount + margin_amount


def should_query_dashapi_first(order, target_dimension):
    if target_dimension == constants.StructureDimension.PUBLISHER:
        return False

    if target_dimension == constants.StructureDimension.PLACEMENT:
        return False

    if target_dimension == constants.StructureDimension.SOURCE:
        return True

    _, order_field = sort_helper.dissect_order(order)

    if order_field == "name" and target_dimension in constants.StructureDimension._ALL:
        return True

    if order_field == "status" and target_dimension in constants.StructureDimension._ALL:
        return True

    if order_field == "daily_budget" and target_dimension in constants.StructureDimension._ALL:
        return True

    if order_field in fields.CONTENT_ADS_FIELDS and target_dimension == constants.StructureDimension.CONTENT_AD:
        return True

    if order_field in fields.OTHER_DASH_FIELDS:
        return True

    return False


def should_query_dashapi(breakdown, target_dimension):
    return (
        target_dimension in constants.StructureDimension._ALL
        or len(breakdown) == 1
        and constants.is_top_level_delivery_dimension(target_dimension)
    )


def should_query_counts_dashapi(target_dimension):
    return target_dimension in set(constants.StructureDimension._ALL) - set(constants.StructureDimension._EXTENDED)


def merge_rows(breakdown, dash_rows, stats_rows):
    """
    Merges stats rows to dash rows. Preserves order of the rows.
    All stats rows should have a corresponding dash row. The opposite is not
    necessarily true in cases where there is no stats.
    """

    group_b = sort_helper.group_rows_by_breakdown_key(breakdown, stats_rows, max_1=True)

    rows = []
    for row_a in dash_rows:
        key = sort_helper.get_breakdown_key(row_a, breakdown)
        row_b = group_b.pop(key, None)
        if row_b:
            row_a = merge_row(row_a, row_b)

        rows.append(row_a)

    if group_b:
        # not all rows were popped from group_b, that means that we fetched
        # stats rows for dash rows that either do not exist or were a part of
        # some other page
        logger.warning("Got stats for unknown objects", count=len(group_b), breakdown=str(breakdown))

    return rows


def merge_row(row_a, row_b):
    row = {}
    row.update(row_a)
    row.update(row_b)
    return row


def log_user_query_request(user, breakdown, constraints, order, offset, limit):
    logger.debug(
        "Stats query request: user_id {}, breakdown {}, order {}, offset {}, limit {}, date range {}/{}, age {}, account_id {}, campaign_id {}, ad_group_id {}".format(
            user.id,
            "__".join(breakdown),
            order,
            offset,
            limit,
            constraints["date__gte"].isoformat(),
            constraints["date__lte"].isoformat(),
            (datetime.date.today() - constraints["date__gte"]).days,
            constraints["account"].id if "account" in constraints else "NULL",
            constraints["campaign"].id if "campaign" in constraints else "NULL",
            constraints["ad_group"].id if "ad_group" in constraints else "NULL",
        )
    )


def remap_delivery_stats_keys(stats_rows, target_dimension):
    if not constants.is_top_level_delivery_dimension(target_dimension):
        return

    for row in stats_rows:
        bid_modifier_type = core.features.bid_modifiers.helpers.breakdown_name_to_modifier_type(target_dimension)
        if target_dimension in (constants.DeliveryDimension.DEVICE, constants.DeliveryDimension.DMA) or not row.get(
            target_dimension
        ):
            continue
        try:
            row[target_dimension] = core.features.bid_modifiers.DashboardConverter.to_target(
                bid_modifier_type, row[target_dimension]
            )
        except core.features.bid_modifiers.exceptions.BidModifierTargetInvalid:
            pass


def extract_counts(parents, rows):
    if not parents:
        return [{"parent_breakdown_id": None, "count": len(rows)}]

    rows_by_parent_br_id = collections.defaultdict(list)
    for row in rows:
        rows_by_parent_br_id[row["parent_breakdown_id"]].append(row)

    counts = []
    for key, values in rows_by_parent_br_id.items():
        counts.append({"parent_breakdown_id": key, "count": len(values)})
    return counts
