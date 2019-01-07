import datetime
import io
import json
import logging
from decimal import Decimal

import unicodecsv as csv
from django.db.models import F

from analytics import demand_report_definitions
from core import models
from core.features import bcm
from dash import constants
from redshiftapi import db
from utils import bigquery_helper
from utils import queryset_helper
from zemauth.models import User

DATASET_NAME = "ba"
TABLE_NAME = "demand"
BIGQUERY_TIMEOUT = 300

AD_GROUP_CHUNK_SIZE = 2000

logger = logging.getLogger(__name__)


def create_report():
    """
    Create demand report from AdGroup spend data and Z1 entities and their settings and upload it to BigQuery.
    """

    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    ad_group_spend_dict = {e["ad_group_id"]: e for e in _get_ad_group_spend()}

    output_stream = _generate_bq_csv_file(ad_group_spend_dict, yesterday)
    _update_big_query(output_stream, yesterday)

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

    logger.info("Deleting existing records for %s from BigQuery.", date_string)
    delete_query = "delete from %s.%s where date = '%s'" % (DATASET_NAME, TABLE_NAME, date_string)
    bigquery_helper.query(delete_query, timeout=BIGQUERY_TIMEOUT, use_legacy_sql=False)


def _generate_bq_csv_file(ad_group_spend_dict, date):
    logger.info("Generating CSV file.")
    output_stream = io.BytesIO()

    csv_writer = csv.DictWriter(
        output_stream, fieldnames=demand_report_definitions.OUTPUT_COLUMN_NAMES, extrasaction="ignore"
    )
    csv_writer.writeheader()

    for row in _csv_rows_generator(ad_group_spend_dict, date):
        csv_writer.writerow(row)

    output_stream.seek(0)
    logger.info("Done generating CSV file.")
    return output_stream


def _csv_rows_generator(ad_group_spend_dict, date):
    date_string = date.strftime("%Y-%m-%d")
    source_id_map = _source_id_map(constants.SourceType.OUTBRAIN, constants.SourceType.YAHOO)

    missing_ad_group_ids = set(ad_group_spend_dict.keys())

    for row in _ad_group_rows_generator(_get_ad_group_data(), ad_group_spend_dict, source_id_map):
        row["date"] = date_string
        missing_ad_group_ids.discard(row["adgroup_id"])
        yield row

    for row in _ad_group_rows_generator(
        _get_ad_group_data(ad_group_ids=missing_ad_group_ids), ad_group_spend_dict, source_id_map
    ):
        row["date"] = date_string
        yield row


def _ad_group_rows_generator(ad_group_query_set, ad_group_spend_dict, source_id_map):
    chunk_id = 0

    for ad_group_data_chunk in queryset_helper.chunk_iterator(ad_group_query_set, chunk_size=AD_GROUP_CHUNK_SIZE):
        chunk_id += 1
        logger.info("Processing ad group chunk #%s", chunk_id)

        campaign_ids = set(e["campaign_id"] for e in ad_group_data_chunk)

        campaign_data_dict = {e["campaign_id"]: e for e in _get_campaign_data(campaign_ids)}

        account_data_dict = {e["campaign_id"]: e for e in _get_account_data(campaign_ids)}

        user_email_dict = _get_user_email_dict(account_data_dict.values())

        ad_group_ids = set(e["adgroup_id"] for e in ad_group_data_chunk)

        ad_group_source_data_dict = {}
        for ad_group_source_row in _get_ad_group_source_data(ad_group_ids):
            ad_group_source_list = ad_group_source_data_dict.setdefault(ad_group_source_row["adgroup_id"], [])
            ad_group_source_list.append(ad_group_source_row)

        ad_group_stats_dict = _calculate_ad_group_stats(
            ad_group_data_chunk, campaign_data_dict, ad_group_source_data_dict, ad_group_spend_dict, source_id_map
        )

        for ad_group_data_row in ad_group_data_chunk:
            row = ad_group_data_row.copy()
            row.update(campaign_data_dict[row["campaign_id"]])
            row.update(account_data_dict[row["campaign_id"]])
            row.update(ad_group_stats_dict[row["adgroup_id"]])

            target_regions, geo_targeting_types = _resolve_geo_targeting(row)
            row["target_regions"] = target_regions
            row["geo_targeting_type"] = geo_targeting_types

            row["world_region"] = (
                demand_report_definitions.WORLD_REGIONS.get(row["target_regions"][0], "N/A")
                if row["target_regions"]
                else "N/A"
            )
            row["type"] = constants.CampaignType.get_name(row["type"])
            row["cs_email"] = user_email_dict.get(row["cs_representative_id"], "N/A")
            row["sales_email"] = user_email_dict.get(row["sales_representative_id"], "N/A")

            _normalize_row(row)
            yield row


def _get_budget_data_dict(campaign_ids):
    budget_data = _get_budget_data(campaign_ids)
    budget_dict = {}
    for row in budget_data:
        campaign_list = budget_dict.setdefault(row["campaign_id"], [])
        campaign_list.append(row)

    return budget_dict


def _aggregate_stats(ad_group_spend_dict, ad_group_id):
    impressions, clicks, spend = 0, 0, 0

    if ad_group_id in ad_group_spend_dict:
        ad_group_spend = ad_group_spend_dict[ad_group_id]
        impressions = ad_group_spend["impressions"]
        clicks = ad_group_spend["clicks"]
        spend = float(ad_group_spend["spend_nano"]) / 1000000000

    return impressions, clicks, spend


def _calculate_ad_group_stats(
    ad_group_data_chunk, campaign_data_dict, ad_group_source_data_dict, ad_group_spend_dict, source_id_map
):
    budget_data_dict = _get_budget_data_dict(set(e["campaign_id"] for e in ad_group_data_chunk))

    ad_group_dict = {}
    campaign_adgroup_map = {}

    for ad_group_data_row in ad_group_data_chunk:
        ad_group_id = ad_group_data_row["adgroup_id"]

        ad_group_id_set = campaign_adgroup_map.setdefault(ad_group_data_row["campaign_id"], set())
        ad_group_id_set.add(ad_group_id)

        impressions, clicks, spend = _aggregate_stats(ad_group_spend_dict, ad_group_id)
        budget, cpc = _calculate_budget_and_cpc(
            campaign_data_dict[ad_group_data_row["campaign_id"]],
            ad_group_data_row,
            ad_group_source_data_dict[ad_group_id],
            source_id_map,
        )
        ad_group_dict[ad_group_id] = {
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "calculated_daily_budget": budget,
            "calculated_cpc": cpc,
        }

    for campaign_id, ad_group_id_set in campaign_adgroup_map.items():
        if campaign_id not in budget_data_dict:
            logger.warning("No budget data for campaign id %s", campaign_id)
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


def _calculate_budget_and_cpc(campaign_data_row, ad_group_data_row, ad_group_source_rows, source_id_map):
    adgroup_row = campaign_data_row.copy()
    adgroup_row.update(ad_group_data_row)
    adgroup_row.update(ad_group_source_rows[0])

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
                calculated_cpc = _weighted_average_cpc(source_data, daily_budget_sum=calculated_daily_budget)
            else:
                calculated_cpc = Decimal(0)
        else:
            calculated_cpc = adgroup_row["cpc_cc"]

    elif adgroup_row["autopilot_state"] == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        calculated_daily_budget = adgroup_row["autopilot_daily_budget"]
        calculated_cpc = adgroup_row["cpc_cc"]
    else:
        raise ValueError("Unhandled autopilot_state: %s" % adgroup_row["autopilot_state"])

    return calculated_daily_budget, calculated_cpc


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

    _normalize_array(row, "target_regions")
    _normalize_array(row, "geo_targeting_type")
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
    _normalize_array(row, "target_placements")
    _normalize_array(row, "target_devices")


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


def _normalize_array(row, field_name):
    val = row[field_name]
    row[field_name] = _normalize_array_value(val)


def _normalize_array_value(val):
    if val is None:
        val = []
    elif isinstance(val, str):
        val = json.loads(val)
    elif not isinstance(val, list):
        raise ValueError("%s is not a list" % type(val))

    return ",".join(sorted(val))


def _normalize_field(row, field_name):
    val = row[field_name]
    result = _normalize_value(val)
    row[field_name] = _bool_repr(result)
    return result


def _normalize_value(val):
    if val is None:
        result = False
    elif isinstance(val, bool):
        result = val
    elif _is_number(val):
        result = val > 0
    elif isinstance(val, list):
        result = len(val) > 0
    else:
        result = len(json.loads(val)) > 0

    return result


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


def _get_account_data(campaign_ids):
    field_mapping = {
        "campaign_id": F("campaign__id"),
        "agency_name": F("agency__name"),
        "agency_created_dt": F("agency__created_dt"),
        "sales_representative_id": F("agency__sales_representative_id"),
        "cs_representative_id": F("agency__cs_representative_id"),
        "whitelabel": F("agency__whitelabel"),
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
    }
    output_values = list(field_mapping.keys()) + ["agency_id", "currency"]

    return (
        models.Account.objects.filter(campaign__id__in=campaign_ids)
        .select_related("agency", "agency__settings", "settings")
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
    }
    output_values = list(field_mapping.keys()) + ["account_id", "modified_by_id", "type", "real_time_campaign_stop"]

    return (
        models.Campaign.objects.filter(id__in=campaign_ids)
        .select_related("settings")
        .annotate(**field_mapping)
        .values(*output_values)
    )


def _get_budget_data(campaign_ids, date=None):
    if date is None:
        date = datetime.date.today() - datetime.timedelta(days=1)

    return (
        bcm.BudgetLineItem.objects.filter(statements__date__lte=date, campaign_id__in=campaign_ids)
        .annotate_spend_data()
        .values("id", "amount", "campaign_id", "spend_data_etfm_total")
    )


def _get_ad_group_data(ad_group_ids=None, date=None):
    if date is None:
        date = datetime.date.today() - datetime.timedelta(days=1)

    field_mapping = {
        "adgroup_id": F("id"),
        "adgroup_name": F("name"),
        "adgroup_created_dt": F("created_dt"),
        "adgroup_default_blacklist_id": F("default_blacklist_id"),
        "start_date": F("settings__start_date"),
        "end_date": F("settings__end_date"),
        "cpc_cc": F("settings__cpc_cc"),
        "target_devices": F("settings__target_devices"),
        "target_regions": F("settings__target_regions"),
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
        "target_placements": F("settings__target_placements"),
        "delivery_type": F("settings__delivery_type"),
        "click_capping_daily_ad_group_max_clicks": F("settings__click_capping_daily_ad_group_max_clicks"),
        "b1_sources_group_cpm": F("settings__b1_sources_group_cpm"),
        "adgroupsettings_frequency_capping": F("settings__frequency_capping"),
    }

    output_values = list(field_mapping.keys()) + ["campaign_id"]

    if ad_group_ids is None:
        qs = models.AdGroup.objects.all().filter_running(date=date)
    else:
        qs = models.AdGroup.objects.filter(id__in=ad_group_ids)

    return qs.select_related("settings").annotate(**field_mapping).values(*output_values)


def _get_ad_group_source_data(ad_group_ids=None, date=None):
    if date is None:
        date = datetime.date.today() - datetime.timedelta(days=1)

    field_mapping = {
        "adgroup_id": F("ad_group_id"),
        "adgroupsource_source_id": F("source_id"),
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


def _get_ad_group_spend():
    logger.info("Querying AdGroup spend.")

    sql = """
SELECT
    ad_group_id,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(COALESCE(effective_cost_nano, 0) + COALESCE(effective_data_cost_nano, 0) + COALESCE(license_fee_nano, 0) + COALESCE(margin_nano, 0)) AS spend_nano
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
