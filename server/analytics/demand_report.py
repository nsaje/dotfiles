import io
import json
from collections import defaultdict
from decimal import Decimal

import unicodecsv as csv
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Case
from django.db.models import Count
from django.db.models import DateField
from django.db.models import ExpressionWrapper
from django.db.models import F
from django.db.models import FloatField
from django.db.models import Func
from django.db.models import Max
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models import When
from django.db.models.functions import Cast
from django.db.models.functions import Coalesce

import automation.models
from analytics import demand_report_definitions
from core import models
from core.features import bcm
from core.features import bid_modifiers
from core.features.goals import campaign_goal
from core.features.goals import campaign_goal_value
from core.models.tags import helpers as tag_helpers
from dash import constants
from redshiftapi import db
from utils import bigquery_helper
from utils import converters
from utils import dates_helper
from utils import db_aggregates
from utils import queryset_helper
from utils import zlogging
from zemauth.models import User

DATASET_NAME = "ba"
TABLE_NAME = "demand"
BIGQUERY_TIMEOUT = 300

AD_GROUP_CHUNK_SIZE = 2000

logger = zlogging.getLogger(__name__)


def create_report():
    """
    Create demand report from AdGroup spend data and Z1 entities and their settings and upload it to BigQuery.
    """
    date = dates_helper.local_yesterday()
    rows = _rows_generator(date)
    output_stream = _generate_bq_csv_file(rows)
    _update_big_query(output_stream, date)

    logger.info("Demand report done.")


def _update_big_query(output_stream, date):
    logger.info("Updating BigQuery.")
    _delete_big_query_records(date)
    logger.info("Uploading data to BigQuery.")
    bigquery_helper.upload_csv_file(
        output_stream, DATASET_NAME, TABLE_NAME, timeout=BIGQUERY_TIMEOUT, skip_leading_rows=1
    )


def _delete_big_query_records(date):
    date_string = date.strftime("%Y-%m-%d")

    logger.info("Deleting existing records for date from BigQuery.", date=date_string)
    delete_query = "delete from %s.%s where date = '%s'" % (DATASET_NAME, TABLE_NAME, date_string)
    bigquery_helper.query(delete_query, timeout=BIGQUERY_TIMEOUT, use_legacy_sql=False)


def _generate_bq_csv_file(rows):
    logger.info("Generating CSV file.")
    output_stream = io.BytesIO()

    csv_writer = csv.DictWriter(
        output_stream, fieldnames=demand_report_definitions.OUTPUT_COLUMN_NAMES, extrasaction="ignore"
    )
    csv_writer.writeheader()

    for row in rows:
        csv_writer.writerow(row)

    output_stream.seek(0)
    logger.info("Done generating CSV file.")
    return output_stream


def _rows_generator(date):
    ad_group_stats_dict = {e["ad_group_id"]: e for e in _get_ad_group_stats()}
    account_data_dict = _get_account_data_dict()

    date_string = date.strftime("%Y-%m-%d")
    source_id_map = _source_id_map(constants.SourceType.OUTBRAIN, constants.SourceType.YAHOO)

    missing_ad_group_ids = set(ad_group_stats_dict.keys())

    for row in _ad_group_rows_generator(_get_ad_group_data(), account_data_dict, ad_group_stats_dict, source_id_map):
        row["date"] = date_string
        missing_ad_group_ids.discard(row["adgroup_id"])
        yield row

    for row in _ad_group_rows_generator(
        _get_ad_group_data(ad_group_ids=missing_ad_group_ids), account_data_dict, ad_group_stats_dict, source_id_map
    ):
        row["date"] = date_string
        yield row


def _ad_group_rows_generator(ad_group_query_set, account_data_dict, ad_group_stats_dict, source_id_map):
    chunk_id = 0

    for ad_group_data_chunk in queryset_helper.chunk_iterator(ad_group_query_set, chunk_size=AD_GROUP_CHUNK_SIZE):
        chunk_id += 1
        logger.info("Processing ad group chunk #%s", chunk_id)

        campaign_ids = set(e["campaign_id"] for e in ad_group_data_chunk)

        campaign_data_dict = {e["campaign_id"]: e for e in _get_campaign_data(campaign_ids)}
        logger.info("Fetched %s campaign data rows for chunk #%s", len(campaign_data_dict), chunk_id)

        user_email_dict = _get_user_email_dict(account_data_dict.values())
        logger.info("Fetched %s user data rows for chunk #%s", len(user_email_dict), chunk_id)

        remaining_budget_dict = _get_remaining_budget_data_map(campaign_ids)
        logger.info("Fetched %s remaining budget data rows for chunk #%s", len(remaining_budget_dict), chunk_id)

        ad_group_ids = set(e["adgroup_id"] for e in ad_group_data_chunk)

        ad_group_source_data_dict = defaultdict(list)
        for ad_group_source_row in _get_ad_group_source_data(ad_group_ids):
            ad_group_source_data_dict[ad_group_source_row["adgroup_id"]].append(ad_group_source_row)
        logger.info("Fetched %s ad group source data rows for chunk #%s", len(ad_group_source_data_dict), chunk_id)

        ad_group_stats_prepared = _calculate_ad_group_stats(
            ad_group_data_chunk, campaign_data_dict, ad_group_source_data_dict, ad_group_stats_dict, source_id_map
        )

        rules_by_ad_group_id = _compute_active_rules_by_ad_group(ad_group_data_chunk, campaign_data_dict)
        bid_modifiers_by_ad_group_id = _get_bid_modifier_count_by_ad_group(ad_group_ids)
        trackers_count_by_ad_group_id = _get_trackers_count_by_ad_group(ad_group_ids)

        for ad_group_data_row in ad_group_data_chunk:
            row = ad_group_data_row.copy()
            row.update(campaign_data_dict[row["campaign_id"]])
            row.update(account_data_dict[campaign_data_dict[row["campaign_id"]]["account_id"]])
            row.update(remaining_budget_dict.get(row["campaign_id"], {"remaining_budget": Decimal(0.0)}))
            row.update(ad_group_stats_prepared[row["adgroup_id"]])
            row.update(bid_modifiers_by_ad_group_id[row["adgroup_id"]])

            target_regions, geo_targeting_types = _resolve_geo_targeting(row)
            row["target_regions"] = target_regions
            row["geo_targeting_type"] = geo_targeting_types

            row["world_region"] = (
                demand_report_definitions.WORLD_REGIONS.get(row["target_regions"][0], "World")
                if row["target_regions"]
                else "World"
            )
            row["type"] = constants.CampaignType.get_name(row["type"])
            row["cs_email"] = user_email_dict.get(row["cs_representative_id"], "N/A")
            row["sales_email"] = user_email_dict.get(row["sales_representative_id"], "N/A")
            row["rules"] = rules_by_ad_group_id[row["adgroup_id"]]
            row["rules_count"] = len(rules_by_ad_group_id[row["adgroup_id"]])
            row["js_tracking"] = trackers_count_by_ad_group_id[row["adgroup_id"]]

            _normalize_row(row)
            yield row

        logger.info("Done processing ad group chunk #%s", chunk_id)


def _get_budget_data_dict(campaign_ids):
    budget_data = _get_budget_data(campaign_ids)
    budget_dict = defaultdict(list)
    for row in budget_data:
        budget_dict[row["campaign_id"]].append(row)

    return budget_dict


def _calculate_ad_group_stats(
    ad_group_data_chunk, campaign_data_dict, ad_group_source_data_dict, ad_group_stats_dict, source_id_map
):
    budget_data_dict = _get_budget_data_dict(set(e["campaign_id"] for e in ad_group_data_chunk))

    ad_group_dict = {}
    campaign_adgroup_map = defaultdict(set)

    for ad_group_data_row in ad_group_data_chunk:
        ad_group_id = ad_group_data_row["adgroup_id"]
        campaign_adgroup_map[ad_group_data_row["campaign_id"]].add(ad_group_id)

        if ad_group_data_row["adgroupsettings_state"] == constants.AdGroupSourceSettingsState.ACTIVE:
            active_ssps = [ssp["adgroupsource_source_name"] for ssp in ad_group_source_data_dict[ad_group_id]]
        else:
            active_ssps = []

        budget, bid = _calculate_budget_and_bid(
            campaign_data_dict[ad_group_data_row["campaign_id"]],
            ad_group_data_row,
            ad_group_source_data_dict[ad_group_id],
            source_id_map,
        )
        ad_group_stats = ad_group_stats_dict.get(ad_group_id, {})
        ad_group_dict[ad_group_id] = {
            "impressions": ad_group_stats.get("impressions", 0),
            "clicks": ad_group_stats.get("clicks", 0),
            "spend": float(ad_group_stats["spend_nano"]) / 10 ** 9 if "spend_nano" in ad_group_stats else 0,
            "license_fee": float(ad_group_stats["license_fee_nano"]) / 10 ** 9
            if "license_fee_nano" in ad_group_stats
            else 0,
            "calculated_daily_budget": budget,
            "calculated_bid": bid,
            "active_ssps": ", ".join(sorted(active_ssps)),
            "active_ssps_count": len(active_ssps),
            "bidding_type": ad_group_data_row["adgroup_bidding_type"],
            "visits": ad_group_stats.get("visits", 0),
            "video_midpoint": ad_group_stats.get("video_midpoint", 0),
            "video_complete": ad_group_stats.get("video_complete", 0),
            "mrc50_measurable": ad_group_stats.get("mrc50_measurable", 0),
            "mrc50_viewable": ad_group_stats.get("mrc50_viewable", 0),
            "mrc100_measurable": ad_group_stats.get("mrc100_measurable", 0),
            "mrc100_viewable": ad_group_stats.get("mrc100_viewable", 0),
            "vast4_measurable": ad_group_stats.get("vast4_measurable", 0),
            "vast4_viewable": ad_group_stats.get("vast4_viewable", 0),
        }

    for campaign_id, ad_group_id_set in campaign_adgroup_map.items():
        if campaign_id not in budget_data_dict:
            logger.warning("No budget data for campaign", campaign=campaign_id)
            continue

        budget_data = budget_data_dict[campaign_id]

        full_budget_yesterday = Decimal(sum(item["amount"] for item in budget_data))
        spend_until_yesterday = Decimal(sum(item["spend_data_etfm_total"] for item in budget_data) / 1000000000)
        remaining_budget_yesterday = full_budget_yesterday - spend_until_yesterday

        configured_budget = Decimal(
            sum(
                item["calculated_daily_budget"]
                for ad_group_id, item in ad_group_dict.items()
                if ad_group_id in campaign_adgroup_map[campaign_id]
            )
        )

        if remaining_budget_yesterday < configured_budget:
            if remaining_budget_yesterday > 0:
                # distribute remaining budget according to AdGroup daily budgets
                for ad_group_id in ad_group_id_set:
                    ad_group_remaining_budget = (
                        remaining_budget_yesterday
                        * ad_group_dict[ad_group_id]["calculated_daily_budget"]
                        / configured_budget
                    )
                    ad_group_dict[ad_group_id]["calculated_daily_budget"] = (
                        Decimal(ad_group_dict[ad_group_id]["spend"]) + ad_group_remaining_budget
                    )

            else:
                # use actual spend as AdGroup daily budgets
                for ad_group_id in ad_group_id_set:
                    ad_group_dict[ad_group_id]["calculated_daily_budget"] = Decimal(ad_group_dict[ad_group_id]["spend"])

    return ad_group_dict


def _calculate_budget_and_bid(campaign_data_row, ad_group_data_row, ad_group_source_rows, source_id_map):
    adgroup_row = campaign_data_row.copy()
    adgroup_row.update(ad_group_data_row)

    uses_realtime_autopilot = adgroup_row["uses_realtime_autopilot"] is True

    if adgroup_row["autopilot"] or adgroup_row["autopilot_state"] in (
        constants.AdGroupSettingsAutopilotState.INACTIVE,
        constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
    ):
        if adgroup_row["b1_sources_group_enabled"]:
            outbrain = _get_source_budget_and_cpc_by_source_id(
                ad_group_source_rows, source_id_map[constants.SourceType.OUTBRAIN]
            )
            yahoo = _get_source_budget_and_cpc_by_source_id(
                ad_group_source_rows, source_id_map[constants.SourceType.YAHOO]
            )
            rtb = {
                "budget": adgroup_row["b1_sources_group_daily_budget"],
                "cpc": adgroup_row["b1_sources_group_cpc_cc"],
            }

            source_data = [outbrain, yahoo, rtb]

        else:
            source_data = [_get_source_budget_and_cpc(r) for r in ad_group_source_rows]

        calculated_daily_budget = sum([i["budget"] for i in source_data])
        if adgroup_row["autopilot_state"] == constants.AdGroupSettingsAutopilotState.INACTIVE:
            if calculated_daily_budget != 0:
                calculated_bid = _weighted_average_cpc(source_data, daily_budget_sum=calculated_daily_budget)
            else:
                calculated_bid = Decimal(0)
        else:
            calculated_bid = adgroup_row["bid"] if uses_realtime_autopilot else adgroup_row["max_autopilot_bid"]

    elif adgroup_row["autopilot_state"] == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        calculated_daily_budget = adgroup_row["autopilot_daily_budget"]
        calculated_bid = adgroup_row["bid"] if uses_realtime_autopilot else adgroup_row["max_autopilot_bid"]
    elif adgroup_row["autopilot_state"] == constants.AdGroupSettingsAutopilotState.ACTIVE:
        calculated_daily_budget = adgroup_row["daily_budget"]
        calculated_bid = adgroup_row["bid"]

        # TODO RTAP: don't fail the job until we fix daily budgets
        if calculated_daily_budget is None:
            logger.error("Unassigned daily budget", ad_group_id=adgroup_row["adgroup_id"])
            calculated_daily_budget = Decimal(0.0)
    else:
        raise ValueError("Unhandled autopilot_state: %s" % adgroup_row["autopilot_state"])

    return calculated_daily_budget, calculated_bid


def _get_source_budget_and_cpc(source_row):
    if not source_row:
        return {"budget": Decimal(0), "cpc": Decimal(0)}

    return {
        "budget": source_row["adgroupsourcesettings_daily_budget_cc"],
        "cpc": source_row["adgroupsourcesettings_cpc_cc"],
    }


def _weighted_average_cpc(source_data, daily_budget_sum=None):
    if daily_budget_sum is None:
        daily_budget_sum = sum([i["budget"] for i in source_data])

    return sum([i["cpc"] * i["budget"] for i in source_data]) / daily_budget_sum


def _get_source_budget_and_cpc_by_source_id(adgroup_rows, source_id):
    source_row = (list(filter(lambda x: x["adgroupsource_source_id"] == source_id, adgroup_rows)) or [None])[0]
    return _get_source_budget_and_cpc(source_row)


def _source_id_map(*source_types):
    source_id_map = dict(
        models.Source.objects.filter(source_type__type__in=source_types).values_list("source_type__type", "id")
    )

    if len(source_id_map) != len(source_types):
        missing_source_types = set(source_types) - set(source_id_map.keys())
        raise ValueError("Could not find source types for: %s" % ", ".join(missing_source_types))

    return source_id_map


def _normalize_row(row):
    _normalize_list_to_bool(
        row,
        "whitelist_publisher_groups",
        [
            "whitelist_publisher_groups",
            "accountsettings_whitelist_publisher_groups",
            "campaignsettings_whitelist_publisher_groups",
            "adgroupsettings_whitelist_publisher_groups",
        ],
    )

    _normalize_list_to_bool(
        row,
        "blacklist_publisher_groups",
        [
            "blacklist_publisher_groups",
            "accountsettings_blacklist_publisher_groups",
            "campaignsettings_blacklist_publisher_groups",
            "adgroupsettings_blacklist_publisher_groups",
            "agency_default_blacklist_id",
            "account_default_blacklist_id",
            "campaign_default_blacklist_id",
            "adgroup_default_blacklist_id",
        ],
    )

    row["frequency_capping"] = _bool_repr(
        _normalize_field(row, "frequency_capping")
        or _normalize_field(row, "campaignsettings_frequency_capping")
        or _normalize_field(row, "adgroupsettings_frequency_capping")
    )

    _normalize_field(row, "real_time_campaign_stop")
    _normalize_field(row, "auto_add_new_sources")
    _normalize_field(row, "automatic_campaign_stop")
    _normalize_field(row, "enable_adobe_tracking")
    _normalize_field(row, "enable_ga_tracking")
    _normalize_field(row, "autopilot")

    _normalize_iterable(row, "target_regions")
    _normalize_iterable(row, "geo_targeting_type")
    _normalize_field(row, "retargeting_ad_groups")
    _normalize_field(row, "exclusion_retargeting_ad_groups")
    _normalize_field(row, "bluekai_targeting")
    _normalize_field(row, "exclusion_interest_targeting")
    _normalize_field(row, "interest_targeting")
    _normalize_field(row, "audience_targeting")
    _normalize_field(row, "exclusion_audience_targeting")
    _normalize_field(row, "dayparting")
    _normalize_field(row, "b1_sources_group_enabled")

    _normalize_field(row, "exclusion_target_regions")
    _normalize_field(row, "target_os")
    _normalize_iterable(row, "target_environments")
    _normalize_iterable(row, "target_devices")
    _normalize_iterable(row, "rules")
    _normalize_field(row, "target_browsers")
    _normalize_field(row, "exclusion_target_browsers")
    _normalize_field(row, "target_connection_types")
    _normalize_field(row, "js_tracking")

    row["agency_tags"] = tag_helpers.entity_tag_names_to_string(row["agency_tags"])
    row["account_tags"] = tag_helpers.entity_tag_names_to_string(row["account_tags"])
    row["campaign_tags"] = tag_helpers.entity_tag_names_to_string(row["campaign_tags"])
    row["adgroup_tags"] = tag_helpers.entity_tag_names_to_string(row["adgroup_tags"])


def _resolve_geo_targeting(row):
    geos = set()
    geo_targeting_types = set()

    for c in _extract_list(row["target_regions"]):
        if _is_number(c):
            # DMA code
            geos.add("US")
            geo_targeting_types.add("DMA")

        elif c.find("-") > -1:
            # zip code targeting
            geos.add(c.split("-")[0])
            geo_targeting_types.add("ZIP")

        elif c.find(":") > -1:
            # state / city targeting
            geos.add(c.split(":")[0])
            geo_targeting_types.add("state")

        else:

            geos.add(c)
            geo_targeting_types.add("country")

    return list(geos), list(geo_targeting_types)


def _normalize_iterable(row, field_name):
    row[field_name] = _normalize_array_value(row[field_name])


def _normalize_array_value(val):
    if val is None:
        val = []
    elif isinstance(val, str):
        val = json.loads(val)

    try:
        return ",".join(str(el) for el in sorted(val))
    except TypeError:
        raise ValueError("%s is not iterable" % type(val))


def _normalize_field(row, field_name):
    val = row[field_name]
    result = _normalize_value(val)
    row[field_name] = _bool_repr(result)
    return result


def _normalize_value(val):
    if val is None:
        return False

    if isinstance(val, bool):
        return val

    if _is_number(val):
        return val > 0

    if isinstance(val, list) or isinstance(val, dict):
        return len(val) > 0

    if isinstance(val, str):
        if len(val) == 0 or val == "null":
            return False

        try:
            return len(json.loads(val)) > 0
        except Exception:
            raise ValueError("Can not parse json from: %s", val)

    raise ValueError("Can not normalize value: %s" % val)


def _normalize_list_to_bool(row, target_field, source_fields_list):
    normalized = []
    for source_field in source_fields_list:
        normalized.extend(_extract_list(row[source_field]))
    normalized = set(normalized)
    if "" in normalized:
        normalized.remove("")

    row[target_field] = _bool_repr(normalized)


def _bool_repr(arg):
    return "TRUE" if arg else "FALSE"


def _extract_list(input_arg):
    if input_arg is None:
        return []
    elif isinstance(input_arg, int):
        return [input_arg]
    elif isinstance(input_arg, list):
        return input_arg
    else:
        lst = json.loads(input_arg)
        if not isinstance(lst, list):
            raise ValueError("%s can not be parsed to list" % input_arg)
        return lst


def _is_number(input_arg):
    try:
        float(input_arg)
        return True
    except Exception:
        return False


def _get_user_email_dict(account_data):
    user_ids = set()
    for account_row in account_data:
        for field in ("sales_representative_id", "cs_representative_id"):
            uid = account_row[field]
            if uid:
                user_ids.add(uid)

    return dict(User.objects.filter(id__in=user_ids).values_list("id", "email"))


def _get_account_data_dict(account_ids=None, date=None):
    account_data_dict = {e["account_id"]: e for e in _get_account_data(account_ids=account_ids, date=date)}
    logger.info("Fetched %s account data entries", len(account_data_dict))
    return account_data_dict


def _get_account_data(account_ids=None, date=None):
    if date is None:
        date = dates_helper.local_yesterday()

    field_mapping = {
        "account_id": F("id"),
        "agency_name": F("agency__name"),
        "agency_created_dt": F("agency__created_dt"),
        "sales_representative_id": F("agency__sales_representative_id"),
        "cs_representative_id": F("agency__cs_representative_id"),
        "whitelabel": F("agency__white_label__theme"),
        "agency_default_blacklist_id": F("agency__default_blacklist_id"),
        "whitelist_publisher_groups": F("agency__settings__whitelist_publisher_groups"),
        "blacklist_publisher_groups": F("agency__settings__blacklist_publisher_groups"),
        "account_name": F("name"),
        "account_created_dt": F("created_dt"),
        "account_default_blacklist_id": F("default_blacklist_id"),
        "account_type": F("settings__account_type"),
        "accountsettings_blacklist_publisher_groups": F("settings__blacklist_publisher_groups"),
        "accountsettings_whitelist_publisher_groups": F("settings__whitelist_publisher_groups"),
        "auto_add_new_sources": F("settings__auto_add_new_sources"),
        "frequency_capping": F("settings__frequency_capping"),
        "agency_tags": ArrayAgg("agency__entity_tags__name", distinct=True),
        "account_tags": ArrayAgg("entity_tags__name", distinct=True),
    }
    output_values = list(field_mapping.keys()) + ["agency_id", "currency", "credit_end_date", "remaining_credit"]

    credit_query = (
        bcm.CreditLineItem.objects.filter(Q(account__id=OuterRef("id")) | Q(agency__account__id=OuterRef("id")))
        .filter(currency=OuterRef("currency"))
        .filter_active(date)
    )

    remaining_credit_query = (
        credit_query.annotate(
            budget_amount=Subquery(
                bcm.BudgetLineItem.objects.filter(credit__id=OuterRef("id"))
                .annotate(
                    budget_amount=Func(
                        Coalesce(Cast("amount", FloatField()), 0.0)
                        - converters.CC_TO_DECIMAL_CURRENCY * Coalesce(Cast("freed_cc", FloatField()), 0.0),
                        function="SUM",
                    )
                )
                .values("budget_amount"),
                output_field=FloatField(),
            )
        )
        .annotate(credit_amount=ExpressionWrapper(Coalesce("amount", 0), output_field=FloatField()))
        .annotate(
            remaining_credit=Func(Coalesce("credit_amount", 0.0), function="SUM")
            - Func(Coalesce("budget_amount", 0.0), function="SUM")
        )
        .values("remaining_credit")
    )

    qs = models.Account.objects.all()
    if account_ids is not None:
        qs = qs.filter(id__in=account_ids)

    return (
        qs.select_related("agency", "agency__settings", "settings")
        .annotate(remaining_credit=Subquery(remaining_credit_query, output_field=FloatField()))
        .annotate(
            credit_end_date=Subquery(
                credit_query.annotate(max_end_date=Max("end_date"))
                .order_by("-max_end_date")
                .values("max_end_date")[:1],
                output_field=DateField(),
            )
        )
        .annotate(**field_mapping)
        .values(*output_values)
    )


def _get_campaign_data(campaign_ids):
    field_mapping = {
        "campaign_id": F("id"),
        "campaign_name": F("name"),
        "campaign_created_dt": F("created_dt"),
        "campaign_default_blacklist_id": F("default_blacklist_id"),
        "iab_category": F("settings__iab_category"),
        "automatic_campaign_stop": F("settings__automatic_campaign_stop"),
        "enable_adobe_tracking": F("settings__enable_adobe_tracking"),
        "enable_ga_tracking": F("settings__enable_ga_tracking"),
        "ga_tracking_type": F("settings__ga_tracking_type"),
        "campaignsettings_blacklist_publisher_groups": F("settings__blacklist_publisher_groups"),
        "campaignsettings_whitelist_publisher_groups": F("settings__whitelist_publisher_groups"),
        "language": F("settings__language"),
        "autopilot": F("settings__autopilot"),
        "campaignsettings_frequency_capping": F("settings__frequency_capping"),
        "campaign_tags": ArrayAgg("entity_tags__name", distinct=True),
        "uses_realtime_autopilot": F("account__agency__uses_realtime_autopilot"),
    }
    output_values = list(field_mapping.keys()) + [
        "account_id",
        "modified_by_id",
        "type",
        "real_time_campaign_stop",
        "goal_type",
        "goal_value",
        "budget_end_date",
    ]

    goal_query = campaign_goal.CampaignGoal.objects.filter(campaign__id=OuterRef("id"), primary=True).filter(
        Q(
            values__created_dt=Subquery(
                campaign_goal_value.CampaignGoalValue.objects.filter(campaign_goal_id=OuterRef("id"))
                .annotate(max_created_dt=Max("created_dt"))
                .values("max_created_dt")
                .order_by("-max_created_dt")[:1]
            )
        )
        | Q(values__isnull=True)
    )

    return (
        models.Campaign.objects.filter(id__in=campaign_ids)
        .select_related("settings")
        .annotate(
            goal_type=Subquery(goal_query.values("type")), goal_value=Subquery(goal_query.values("values__value"))
        )
        .annotate(
            budget_end_date=Subquery(
                bcm.BudgetLineItem.objects.filter(campaign__id=OuterRef("id"))
                .annotate(max_end_date=Max("end_date"))
                .order_by("-max_end_date")
                .values("max_end_date")[:1]
            )
        )
        .annotate(**field_mapping)
        .values(*output_values)
    )


def _get_remaining_budget_data_map(campaign_ids, date=None):
    budget_map = defaultdict(list)
    for record in _get_remaining_budget_data(campaign_ids, date=date):
        budget_map[record["campaign_id"]].append(record)

    remaining_budget_map = {}
    for campaign_id, record_list in budget_map.items():
        budget = 0
        for record in record_list:
            total_spend = converters.nano_to_decimal(record["spend_data_local_etfm_total"] or 0)
            allocated_amount = (
                Decimal(record["amount"] * converters.CURRENCY_TO_CC - record["freed_cc"])
                * converters.CC_TO_DECIMAL_CURRENCY
            )
            budget += allocated_amount - total_spend

        remaining_budget_map[campaign_id] = {"remaining_budget": budget}

    return remaining_budget_map


def _get_remaining_budget_data(campaign_ids, date=None):
    if date is None:
        date = dates_helper.local_yesterday()

    return (
        bcm.BudgetLineItem.objects.filter(campaign__id__in=campaign_ids)
        .filter_active(date)
        .annotate_spend_data()
        .values("amount", "freed_cc", "campaign_id", "spend_data_local_etfm_total")
    )


def _get_budget_data(campaign_ids, date=None):
    if date is None:
        date = dates_helper.local_yesterday()

    return (
        bcm.BudgetLineItem.objects.filter(statements__date__lte=date, campaign_id__in=campaign_ids)
        .annotate_spend_data()
        .values("id", "amount", "campaign_id", "spend_data_etfm_total")
    )


def _compute_active_rules_by_ad_group(ad_group_data_chunk, campaign_data_dict):
    ad_groups_by_account = {}
    ad_groups_by_campaign = {}
    for row in ad_group_data_chunk:
        ad_group_id = row["adgroup_id"]
        campaign_id = row["campaign_id"]
        ad_groups_by_campaign.setdefault(campaign_id, set())
        ad_groups_by_campaign[campaign_id].add(ad_group_id)

        account_id = campaign_data_dict[campaign_id]["account_id"]
        ad_groups_by_account.setdefault(account_id, set())
        ad_groups_by_account[account_id].add(ad_group_id)

    rules_by_ad_group_id = defaultdict(set)
    for row in _get_enabled_rules_qs([row["adgroup_id"] for row in ad_group_data_chunk]):
        if row["included_ad_group"]:
            ad_group_id = row["included_ad_group"]
            rules_by_ad_group_id[ad_group_id].add(row["id"])
        if row["included_campaign"]:
            campaign_id = row["included_campaign"]
            for ad_group_id in ad_groups_by_campaign.get(campaign_id, []):
                rules_by_ad_group_id[ad_group_id].add(row["id"])
        if row["included_account"]:
            account_id = row["included_account"]
            for ad_group_id in ad_groups_by_account.get(account_id, []):
                rules_by_ad_group_id[ad_group_id].add(row["id"])

    return rules_by_ad_group_id


def _get_enabled_rules_qs(ad_group_ids):
    ad_groups = models.AdGroup.objects.filter(id__in=ad_group_ids)
    campaigns = models.Campaign.objects.filter(adgroup__in=ad_groups)
    accounts = models.Account.objects.filter(campaign__adgroup__in=ad_groups)

    return (
        automation.models.Rule.objects.filter(
            Q(ad_groups_included__in=ad_groups)
            | Q(campaigns_included__in=campaigns)
            | Q(accounts_included__in=accounts)
        )
        .filter_enabled()
        .exclude_archived()
        .annotate(
            included_ad_group=F("ad_groups_included"),
            included_campaign=F("campaigns_included"),
            included_account=F("accounts_included"),
        )
        .values("id", "included_ad_group", "included_campaign", "included_account")
    )


def _get_bid_modifier_count_by_ad_group(ad_group_ids):
    qs = (
        bid_modifiers.BidModifier.objects.filter(ad_group_id__in=ad_group_ids)
        .values("ad_group_id", "type")
        .annotate(count=Count("*"))
        .values_list("ad_group_id", "type", "count")
        .order_by()
    )

    result = {}
    for ad_group_id in ad_group_ids:
        result[ad_group_id] = {
            name.lower() + "_bid_modifiers_count": 0 for name in bid_modifiers.BidModifierType.get_all_names()
        }
    for ad_group_id, type_, count in qs:
        field_name = bid_modifiers.BidModifierType.get_name(type_).lower() + "_bid_modifiers_count"
        result[ad_group_id][field_name] = count
    return result


def _get_trackers_count_by_ad_group(ad_group_ids):
    qs = (
        models.ContentAd.objects.filter(ad_group_id__in=ad_group_ids)
        .values("ad_group_id")
        .annotate(trackers_count=db_aggregates.SumJSONLength("trackers"))
        .values_list("ad_group_id", "trackers_count")
    )

    trackers_count_by_ad_group = dict(qs)
    result = {}
    for ad_group_id in ad_group_ids:
        result[ad_group_id] = trackers_count_by_ad_group.get(ad_group_id, 0)

    return result


def _get_ad_group_data(ad_group_ids=None, date=None):
    if date is None:
        date = dates_helper.local_yesterday()

    field_mapping = {
        "adgroup_id": F("id"),
        "adgroup_name": F("name"),
        "adgroup_created_dt": F("created_dt"),
        "adgroup_default_blacklist_id": F("default_blacklist_id"),
        "start_date": F("settings__start_date"),
        "end_date": F("settings__end_date"),
        "bid": Case(When(bidding_type=constants.BiddingType.CPM, then=F("settings__cpm")), default=F("settings__cpc")),
        "max_autopilot_bid": F("settings__max_autopilot_bid"),
        "target_devices": F("settings__target_devices"),
        "target_regions": F("settings__target_regions"),
        "daily_budget": F("settings__daily_budget"),
        "autopilot_daily_budget": F("settings__autopilot_daily_budget"),
        "autopilot_state": F("settings__autopilot_state"),
        "retargeting_ad_groups": F("settings__retargeting_ad_groups"),
        "exclusion_retargeting_ad_groups": F("settings__exclusion_retargeting_ad_groups"),
        "bluekai_targeting": F("settings__bluekai_targeting"),
        "exclusion_interest_targeting": F("settings__exclusion_interest_targeting"),
        "interest_targeting": F("settings__interest_targeting"),
        "audience_targeting": F("settings__audience_targeting"),
        "exclusion_audience_targeting": F("settings__exclusion_audience_targeting"),
        "b1_sources_group_daily_budget": F("settings__b1_sources_group_daily_budget"),
        "b1_sources_group_enabled": F("settings__b1_sources_group_enabled"),
        "b1_sources_group_state": F("settings__b1_sources_group_state"),
        "dayparting": F("settings__dayparting"),
        "adgroupsettings_blacklist_publisher_groups": F("settings__blacklist_publisher_groups"),
        "adgroupsettings_whitelist_publisher_groups": F("settings__whitelist_publisher_groups"),
        "b1_sources_group_cpc_cc": F("settings__b1_sources_group_cpc_cc"),
        "exclusion_target_regions": F("settings__exclusion_target_regions"),
        "target_os": F("settings__target_os"),
        "target_environments": F("settings__target_environments"),
        "target_browsers": F("settings__target_browsers"),
        "exclusion_target_browsers": F("settings__exclusion_target_browsers"),
        "target_connection_types": F("settings__target_connection_types"),
        "delivery_type": F("settings__delivery_type"),
        "click_capping_daily_ad_group_max_clicks": F("settings__click_capping_daily_ad_group_max_clicks"),
        "b1_sources_group_cpm": F("settings__b1_sources_group_cpm"),
        "adgroupsettings_frequency_capping": F("settings__frequency_capping"),
        "adgroupsettings_state": F("settings__state"),
        "adgroup_bidding_type": F("bidding_type"),
        "adgroup_tags": ArrayAgg("entity_tags__name", distinct=True),
    }

    output_values = list(field_mapping.keys()) + ["campaign_id"]

    if ad_group_ids is None:
        qs = models.AdGroup.objects.all().filter_running(date=date)
    else:
        qs = models.AdGroup.objects.filter(id__in=ad_group_ids)

    return qs.select_related("settings").annotate(**field_mapping).values(*output_values)


def _get_ad_group_source_data(ad_group_ids=None, date=None):
    if date is None:
        date = dates_helper.local_yesterday()

    field_mapping = {
        "adgroup_id": F("ad_group_id"),
        "adgroupsource_source_id": F("source_id"),
        "adgroupsource_source_name": F("source__name"),
        "adgroupsourcesettings_cpc_cc": F("settings__cpc_cc"),
        "adgroupsourcesettings_daily_budget_cc": F("settings__daily_budget_cc"),
    }

    if ad_group_ids is None:
        qs = models.AdGroupSource.objects.all().filter_running(date=date)
    else:
        qs = models.AdGroupSource.objects.filter(
            ad_group__id__in=ad_group_ids, settings__state=constants.AdGroupSourceSettingsState.ACTIVE
        )

    return qs.select_related("settings").annotate(**field_mapping).values(*field_mapping.keys())


def _get_ad_group_stats():
    logger.info("Querying AdGroup spend.")

    sql = """
SELECT
    ad_group_id,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(COALESCE(effective_cost_nano, 0)
      + COALESCE(effective_data_cost_nano, 0)
      + COALESCE(service_fee_nano, 0)
      + COALESCE(license_fee_nano, 0)
      + COALESCE(margin_nano, 0)
    ) AS spend_nano,
    SUM(license_fee_nano) AS license_fee_nano,
    SUM(visits) AS visits,
    SUM(video_midpoint) AS video_midpoint,
    SUM(video_complete) AS video_complete,
    SUM(mrc50_measurable) AS mrc50_measurable,
    SUM(mrc50_viewable) AS mrc50_viewable,
    SUM(mrc100_measurable) AS mrc100_measurable,
    SUM(mrc100_viewable) AS mrc100_viewable,
    SUM(vast4_measurable) AS vast4_measurable,
    SUM(vast4_viewable) AS vast4_viewable
FROM mv_adgroup
WHERE
    date = DATE(CURRENT_DATE - interval '1 day')
GROUP BY ad_group_id
HAVING SUM(impressions) > 0
    """

    with db.get_stats_cursor() as cursor:
        cursor.execute(sql)
        rows = db.dictfetchall(cursor)

    logger.info("Got %s AdGroup spend rows.", len(rows))
    return rows
