import datetime
import io
import json
import logging
from decimal import Decimal

import unicodecsv as csv
from django.db.models import F
from django.db.models import Q

from analytics import demand_report_definitions
from automation.campaignstop import constants as campaignstop_constants
from core import models
from core.features import bcm
from dash import constants
from redshiftapi import db
from utils import bigquery_helper
from zemauth.models import User

DATASET_NAME = "ba"
TABLE_NAME = "demand"
BIGQUERY_TIMEOUT = 300

logger = logging.getLogger(__name__)


def create_report():
    """
    Create demand report from AdGroup spend data and Z1 entities and their settings and upload it to BigQuery.
    """

    yesterday = datetime.date.today() - datetime.timedelta(days=1)

    ad_group_spend_dict = {e["ad_group_id"]: e for e in _get_ad_group_spend()}
    ad_group_dict = _get_ad_group_data_dict()
    campaign_data = _get_campaign_data(ad_group_dict.keys())
    budget_data_dict = _get_budget_data_dict(ad_group_dict.keys())
    user_email_dict = _get_user_email_dict(campaign_data)

    output_stream = _generate_bq_csv_file(
        campaign_data, ad_group_dict, budget_data_dict, ad_group_spend_dict, user_email_dict, yesterday
    )
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


def _generate_bq_csv_file(campaign_data, ad_group_dict, budget_data_dict, ad_group_spend_dict, user_email_dict, date):
    logger.info("Generating CSV file.")
    output_stream = io.BytesIO()

    csv_writer = csv.DictWriter(
        output_stream, fieldnames=demand_report_definitions.OUTPUT_COLUMN_NAMES, extrasaction="ignore"
    )
    csv_writer.writeheader()

    for row in _csv_rows_generator(
        campaign_data, ad_group_dict, budget_data_dict, ad_group_spend_dict, user_email_dict, date
    ):
        csv_writer.writerow(row)

    output_stream.seek(0)
    return output_stream


def _csv_rows_generator(campaign_data, ad_group_dict, budget_data_dict, ad_group_spend_dict, user_email_dict, date):
    date_string = date.strftime("%Y-%m-%d")
    source_id_map = _source_id_map(constants.SourceType.OUTBRAIN, constants.SourceType.YAHOO)

    for campaign_data_row in campaign_data:
        campaign_dict = ad_group_dict[campaign_data_row["campaign_id"]]

        if not campaign_dict:
            raise Exception("No AdGroups for campaign_id %s!" % campaign_data_row["campaign_id"])

        ad_group_stats_dict = _calculate_ad_group_stats(
            budget_data_dict, campaign_data_row, campaign_dict, ad_group_spend_dict, source_id_map
        )

        for ad_group_id in campaign_dict:
            row = campaign_dict[ad_group_id][0].copy()
            row.update(campaign_data_row)
            row.update(ad_group_stats_dict[ad_group_id])

            target_regions, geo_targeting_types = _resolve_geo_targeting(row)
            row["target_regions"] = target_regions
            row["geo_targeting_type"] = geo_targeting_types

            row["world_region"] = (
                demand_report_definitions.WORLD_REGIONS.get(row["target_regions"][0], "N/A")
                if row["target_regions"]
                else "N/A"
            )
            row["type"] = constants.CampaignType.get_name(row["type"])
            row["date"] = date_string
            row["cs_email"] = user_email_dict.get(campaign_data_row["cs_representative_id"], "N/A")
            row["sales_email"] = user_email_dict.get(campaign_data_row["sales_representative_id"], "N/A")

            _normalize_row(row)
            yield row


def _get_ad_group_data_dict():
    ad_group_data = _get_ad_group_data()
    ad_group_dict = {}
    for row in ad_group_data:
        campaign_dict = ad_group_dict.setdefault(row["campaign_id"], {})
        ad_group_list = campaign_dict.setdefault(row["adgroup_id"], [])
        ad_group_list.append(row)

    return ad_group_dict


def _get_budget_data_dict(campaign_ids):
    budget_data = _get_budget_data(campaign_ids)
    budget_dict = {}
    for row in budget_data:
        campaing_list = budget_dict.setdefault(row["campaign_id"], [])
        campaing_list.append(row)

    return budget_dict


def _aggregate_stats(ad_group_spend_dict, ad_group_id):
    impressions, clicks, spend = 0, 0, 0

    if ad_group_id in ad_group_spend_dict:
        ad_group_spend = ad_group_spend_dict[ad_group_id]
        impressions = ad_group_spend["impressions"]
        clicks = ad_group_spend["clicks"]

        costs = [
            ad_group_spend[k] or "0"
            for k in ["effective_cost_nano", "effective_data_cost_nano", "license_fee_nano", "margin_nano"]
        ]
        spend = sum(map(lambda x: float(x) / 1000000000, costs))

    return impressions, clicks, spend


def _calculate_ad_group_stats(budget_data_dict, campaign_data_row, campaign_dict, ad_group_spend_dict, source_id_map):
    if not campaign_dict:
        return {}

    ad_group_dict = {}

    for ad_group_id in campaign_dict:
        impressions, clicks, spend = _aggregate_stats(ad_group_spend_dict, ad_group_id)
        budget, cpc = _calculate_budget_and_cpc(campaign_data_row, campaign_dict[ad_group_id], source_id_map)
        ad_group_dict[ad_group_id] = {
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "calculated_daily_budget": budget,
            "calculated_cpc": cpc,
        }

    campaign_id = campaign_dict[ad_group_id][0]["campaign_id"]

    if campaign_id not in budget_data_dict:
        logger.warning("No budget data for campaign id %s", campaign_id)
        return ad_group_dict

    budget_data = budget_data_dict[campaign_id]

    full_budget_yesterday = Decimal(sum(item["amount"] for item in budget_data))
    spend_until_yesterday = Decimal(sum(item["spend_nano"] for item in budget_data) / 1000000000)
    remaining_budget_yesterday = full_budget_yesterday - spend_until_yesterday

    configured_budget = Decimal(sum(item["calculated_daily_budget"] for item in ad_group_dict.values()))

    if remaining_budget_yesterday < configured_budget:
        if remaining_budget_yesterday > 0:
            # distribute remaining budget according to AdGroup daily budgets
            for ad_group_id in ad_group_dict:
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
            for ad_group_id in ad_group_dict:
                ad_group_dict[ad_group_id]["calculated_daily_budget"] = Decimal(ad_group_dict[ad_group_id]["spend"])

    return ad_group_dict


def _calculate_budget_and_cpc(campaign_data_row, ad_group_source_rows, source_id_map):
    adgroup_row = campaign_data_row.copy()
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


def _get_user_email_dict(campaign_data):
    user_ids = set()
    for campaign_row in campaign_data:
        for field in ("sales_representative_id", "cs_representative_id"):
            uid = campaign_row[field]
            if uid:
                user_ids.add(uid)

    logger.info("Querying User data.")
    rows = dict(User.objects.filter(id__in=user_ids).values_list("id", "email"))
    logger.info("Got %s User data rows.", len(rows))
    return rows


def _get_ad_group_data(date=None):
    if date is None:
        date = datetime.date.today() - datetime.timedelta(days=1)

    field_mapping = {
        "adgroup_id": F("ad_group__id"),
        "campaign_id": F("ad_group__campaign_id"),
        "adgroup_name": F("ad_group__name"),
        "adgroup_created_dt": F("ad_group__created_dt"),
        "adgroup_default_blacklist_id": F("ad_group__default_blacklist_id"),
        "start_date": F("ad_group__settings__start_date"),
        "end_date": F("ad_group__settings__end_date"),
        "cpc_cc": F("ad_group__settings__cpc_cc"),
        "target_devices": F("ad_group__settings__target_devices"),
        "target_regions": F("ad_group__settings__target_regions"),
        "autopilot_daily_budget": F("ad_group__settings__autopilot_daily_budget"),
        "autopilot_state": F("ad_group__settings__autopilot_state"),
        "retargeting_ad_groups": F("ad_group__settings__retargeting_ad_groups"),
        "exclusion_retargeting_ad_groups": F("ad_group__settings__exclusion_retargeting_ad_groups"),
        "bluekai_targeting": F("ad_group__settings__bluekai_targeting"),
        "exclusion_interest_targeting": F("ad_group__settings__exclusion_interest_targeting"),
        "interest_targeting": F("ad_group__settings__interest_targeting"),
        "audience_targeting": F("ad_group__settings__audience_targeting"),
        "exclusion_audience_targeting": F("ad_group__settings__exclusion_audience_targeting"),
        "b1_sources_group_daily_budget": F("ad_group__settings__b1_sources_group_daily_budget"),
        "b1_sources_group_enabled": F("ad_group__settings__b1_sources_group_enabled"),
        "b1_sources_group_state": F("ad_group__settings__b1_sources_group_state"),
        "dayparting": F("ad_group__settings__dayparting"),
        "adgroupsettings_blacklist_publisher_groups": F("ad_group__settings__blacklist_publisher_groups"),
        "adgroupsettings_whitelist_publisher_groups": F("ad_group__settings__whitelist_publisher_groups"),
        "b1_sources_group_cpc_cc": F("ad_group__settings__b1_sources_group_cpc_cc"),
        "exclusion_target_regions": F("ad_group__settings__exclusion_target_regions"),
        "target_os": F("ad_group__settings__target_os"),
        "target_placements": F("ad_group__settings__target_placements"),
        "delivery_type": F("ad_group__settings__delivery_type"),
        "click_capping_daily_ad_group_max_clicks": F("ad_group__settings__click_capping_daily_ad_group_max_clicks"),
        "b1_sources_group_cpm": F("ad_group__settings__b1_sources_group_cpm"),
        "adgroupsettings_frequency_capping": F("ad_group__settings__frequency_capping"),
        "adgroupsource_source_id": F("source_id"),
        "adgroupsourcesettings_cpc_cc": F("settings__cpc_cc"),
        "adgroupsourcesettings_daily_budget_cc": F("settings__daily_budget_cc"),
    }

    logger.info("Querying AdGroupSource data.")
    rows = list(
        models.AdGroupSource.objects.filter(
            ad_group__settings__archived=False,
            ad_group__settings__state=constants.AdGroupSettingsState.ACTIVE,
            settings__state=constants.AdGroupSourceSettingsState.ACTIVE,
            ad_group__campaign__settings__archived=False,
            ad_group__settings__start_date__lte=date,
        )
        .filter(Q(ad_group__settings__end_date__gte=date) | Q(ad_group__settings__end_date__isnull=True))
        .filter(
            Q(
                ad_group__campaign__real_time_campaign_stop=True,
                ad_group__campaign__campaignstopstate__state=campaignstop_constants.CampaignStopState.ACTIVE,
            )
            | Q(ad_group__campaign__real_time_campaign_stop=False)
        )
        .select_related("ad_group", "ad_group__settings", "settings")
        .annotate(**field_mapping)
        .values(*field_mapping.keys())
    )
    logger.info("Got %s AdGroupSource data rows.", len(rows))
    return rows


def _get_campaign_data(campaign_ids):
    field_mapping = {
        "agency_id": F("account__agency__id"),
        "agency_name": F("account__agency__name"),
        "agency_created_dt": F("account__agency__created_dt"),
        "sales_representative_id": F("account__agency__sales_representative_id"),
        "cs_representative_id": F("account__agency__cs_representative_id"),
        "whitelabel": F("account__agency__whitelabel"),
        "agency_default_blacklist_id": F("account__agency__default_blacklist_id"),
        "whitelist_publisher_groups": F("account__agency__settings__whitelist_publisher_groups"),
        "blacklist_publisher_groups": F("account__agency__settings__blacklist_publisher_groups"),
        "account_name": F("account__name"),
        "account_created_dt": F("account__created_dt"),
        "account_default_blacklist_id": F("account__default_blacklist_id"),
        "currency": F("account__currency"),
        "account_type": F("account__settings__account_type"),
        "accountsettings_blacklist_publisher_groups": F("account__settings__blacklist_publisher_groups"),
        "accountsettings_whitelist_publisher_groups": F("account__settings__whitelist_publisher_groups"),
        "auto_add_new_sources": F("account__settings__auto_add_new_sources"),
        "frequency_capping": F("account__settings__frequency_capping"),
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

    logger.info("Querying Campaign data.")
    rows = list(
        models.Campaign.objects.filter(id__in=campaign_ids, account__settings__archived=False, settings__archived=False)
        .select_related("account__agency", "account__agency__settings", "account", "account__settings", "settings")
        .annotate(**field_mapping)
        .values(*output_values)
    )
    logger.info("Got %s Campaign data rows.", len(rows))
    return rows


def _get_budget_data(campaign_ids, date=None):
    if date is None:
        date = datetime.date.today() - datetime.timedelta(days=1)

    logger.info("Querying budget data.")
    rows = list(
        bcm.BudgetLineItem.objects.filter(statements__date__lte=date, campaign_id__in=campaign_ids)
        .annotate_spend_data()
        .annotate(
            spend_nano=(
                F("spend_data_media") + F("spend_data_data") + F("spend_data_license_fee") + F("spend_data_margin")
            )
        )
        .values("id", "amount", "campaign_id", "spend_nano")
    )
    logger.info("Got %s budget data rows.", len(rows))
    return rows


def _get_ad_group_spend():
    logger.info("Querying AdGroup spend.")

    sql = """
SELECT
  ad_group_id,
  sum(impressions) AS impressions,
  sum(clicks) AS clicks,
  sum(effective_cost_nano) AS effective_cost_nano,
  sum(effective_data_cost_nano) AS effective_data_cost_nano,
  sum(license_fee_nano) AS license_fee_nano,
  sum(margin_nano) AS margin_nano
FROM mv_adgroup
WHERE
  date = date(CURRENT_DATE - interval '1 day')
GROUP BY ad_group_id
    """

    with db.get_stats_cursor() as cursor:
        cursor.execute(sql)
        rows = db.dictfetchall(cursor)

    logger.info("Got %s AdGroup spend rows.", len(rows))
    return rows
