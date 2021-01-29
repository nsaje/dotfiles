import operator
from collections import defaultdict
from typing import Any
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Sequence

import automation.models
import automation.rules.constants
import core.features.bid_modifiers.constants
import core.features.goals
import core.models
import dash.constants
import dash.features.geolocation
from utils import sort_helper

from ... import config
from ... import constants
from ... import models


def query_stats(
    target_type: int, rules_map: Dict[core.models.AdGroup, List[models.Rule]]
) -> Dict[int, Dict[str, Dict[str, Dict[int, Any]]]]:
    import redshiftapi.api_rules

    ad_groups = list(rules_map.keys())
    stats = redshiftapi.api_rules.query(target_type, ad_groups)
    cpa_ad_groups = _get_cpa_ad_groups(rules_map)
    conversion_stats = redshiftapi.api_rules.query_conversions(target_type, cpa_ad_groups)
    _augment_with_conversion_stats(target_type, cpa_ad_groups, stats, conversion_stats)
    formatted_stats = _format(target_type, stats)
    return _add_missing_targets(target_type, ad_groups, formatted_stats)


def _get_cpa_ad_groups(rules_map):
    cpa_ad_groups = []
    for ad_group, rules in rules_map.items():
        for rule in rules:
            if ad_group not in cpa_ad_groups and rule.requires_cpa_stats:
                cpa_ad_groups.append(ad_group)
    return cpa_ad_groups


def _augment_with_conversion_stats(target_type, cpa_ad_groups, stats, conversion_stats):
    target_column_keys = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]
    conversion_stats_by_pixel_breakdown = sort_helper.group_rows_by_breakdown_key(
        target_column_keys + ["window_key", "ad_group_id"], conversion_stats
    )
    cpa_ad_groups_map = {ad_group.id: ad_group for ad_group in cpa_ad_groups}

    for stats_row in stats:
        ad_group_id = stats_row["ad_group_id"]
        if ad_group_id in cpa_ad_groups_map:
            pixel_rows = conversion_stats_by_pixel_breakdown.get(
                tuple(stats_row[col] for col in target_column_keys) + (stats_row["window_key"], ad_group_id)
            )
            stats_row["conversions"] = _aggregate_conversions(stats_row, pixel_rows)


def _aggregate_conversions(stats_row, pixel_rows):
    conversions = {}
    if not pixel_rows:
        return conversions

    all_conversion_windows = dash.constants.ConversionWindows.get_all()
    for pixel_row in sorted(pixel_rows, key=operator.itemgetter("slug", "window")):
        slug = pixel_row["slug"]
        row_window = pixel_row["window"]
        conversions.setdefault(slug, {})
        for window in all_conversion_windows:
            if window >= row_window:
                conversions[slug].setdefault(
                    window,
                    {
                        "conversion_count_click": 0,
                        "conversion_count_view": 0,
                        "conversion_count_total": 0,
                        "conversion_value_click": 0,
                        "conversion_value_view": 0,
                        "conversion_value_total": 0,
                    },
                )
                conversions[slug][window]["conversion_count_click"] += pixel_row["count"]
                conversions[slug][window]["conversion_count_view"] += pixel_row["count_view"]
                conversions[slug][window]["conversion_count_total"] += pixel_row["count"] + pixel_row["count_view"]

                conversions[slug][window]["conversion_value_click"] += float(pixel_row["conversion_value"])
                conversions[slug][window]["conversion_value_view"] += float(pixel_row["conversion_value_view"])
                conversions[slug][window]["conversion_value_total"] += float(
                    pixel_row["conversion_value"] + pixel_row["conversion_value_view"]
                )

    for slug in conversions:
        for window in conversions[slug]:
            conversions[slug][window]["local_avg_etfm_cost_per_conversion_click"] = (
                (stats_row["local_etfm_cost"] / conversions[slug][window]["conversion_count_click"])
                if conversions[slug][window]["conversion_count_click"]
                else None
            )
            conversions[slug][window]["local_avg_etfm_cost_per_conversion_view"] = (
                (stats_row["local_etfm_cost"] / conversions[slug][window]["conversion_count_view"])
                if conversions[slug][window]["conversion_count_view"]
                else None
            )
            conversions[slug][window]["local_avg_etfm_cost_per_conversion_total"] = (
                (stats_row["local_etfm_cost"] / conversions[slug][window]["conversion_count_total"])
                if conversions[slug][window]["conversion_count_total"]
                else None
            )

            conversions[slug][window]["roas_click"] = (
                (conversions[slug][window]["conversion_value_click"] / stats_row["local_etfm_cost"])
                if stats_row["local_etfm_cost"]
                else None
            )
            conversions[slug][window]["roas_view"] = (
                (conversions[slug][window]["conversion_value_view"] / stats_row["local_etfm_cost"])
                if stats_row["local_etfm_cost"]
                else None
            )
            conversions[slug][window]["roas_total"] = (
                (conversions[slug][window]["conversion_value_total"] / stats_row["local_etfm_cost"])
                if stats_row["local_etfm_cost"]
                else None
            )

    return conversions


def _format(target_type: int, stats: Sequence[Dict]) -> Dict[int, Dict[str, Dict[str, Dict[int, Any]]]]:
    target_column_keys = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]
    formatted_stats: Dict[int, Dict[str, Dict[str, Dict[int, Any]]]] = {}
    for row in stats:
        ad_group_id = row.pop("ad_group_id", None)
        default_key = ad_group_id if target_type == constants.TargetType.AD_GROUP else None
        target_key_group = tuple(row.pop(t, default_key) for t in target_column_keys)
        window_key = row.pop("window_key", None)

        if (
            not all([ad_group_id, all(target_key_group), window_key])
            or target_key_group[0] in core.features.bid_modifiers.constants.UNSUPPORTED_TARGETS
        ):
            continue

        target_key = "__".join(map(str, target_key_group))

        for metric, value in row.items():
            formatted_stats.setdefault(ad_group_id, {})
            formatted_stats[ad_group_id].setdefault(target_key, {})
            formatted_stats[ad_group_id][target_key].setdefault(metric, {})
            formatted_stats[ad_group_id][target_key][metric][window_key] = value

    return formatted_stats


def _add_missing_targets(
    target_type: int, ad_groups: List[core.models.AdGroup], stats: Dict[int, Dict[str, Dict[str, Dict[int, Any]]]]
):
    all_possible_targets = _get_all_possible_targets_per_ad_group(target_type, ad_groups)
    for ad_group in ad_groups:
        possible_targets = set(all_possible_targets[ad_group.id])
        actual_targets = set(stats[ad_group.id].keys() if ad_group.id in stats else [])
        for target_key in possible_targets - actual_targets:
            for metric_type, value in config.STATS_FIELDS_DEFAULTS.items():
                metric = constants.METRIC_STATS_MAPPING[metric_type]
                for window_key in constants.MetricWindow.get_all():
                    stats.setdefault(ad_group.id, {})
                    stats[ad_group.id].setdefault(target_key, {})
                    stats[ad_group.id][target_key].setdefault(metric, {})
                    stats[ad_group.id][target_key][metric][window_key] = value
    return stats


def _get_all_possible_targets_per_ad_group(target_type: int, ad_groups: List[core.models.AdGroup]):
    if target_type == constants.TargetType.AD_GROUP:
        return {ad_group.id: [str(ad_group.id)] for ad_group in ad_groups}
    elif target_type == constants.TargetType.AD:
        content_ads = (
            core.models.ContentAd.objects.filter(ad_group_id__in=[ag.id for ag in ad_groups])
            .exclude_archived()
            .filter_active()
            .values("id", "ad_group_id")
        )
        content_ad_ids_map: DefaultDict[int, List[str]] = defaultdict(list)
        for content_ad in content_ads:
            content_ad_ids_map[content_ad["ad_group_id"]].append(str(content_ad["id"]))
        return content_ad_ids_map
    elif target_type == constants.TargetType.SOURCE:
        ad_group_sources = (
            core.models.AdGroupSource.objects.filter(ad_group_id__in=[ag.id for ag in ad_groups])
            .filter_active()
            .values("source_id", "ad_group_id")
        )
        source_ids_map: DefaultDict[int, List[str]] = defaultdict(list)
        for ad_group_source in ad_group_sources:
            source_ids_map[ad_group_source["ad_group_id"]].append(str(ad_group_source["source_id"]))
        return source_ids_map
    elif target_type in [
        constants.TargetType.PUBLISHER,
        constants.TargetType.DEVICE,
        constants.TargetType.COUNTRY,
        constants.TargetType.STATE,
        constants.TargetType.DMA,
        constants.TargetType.OS,
        constants.TargetType.ENVIRONMENT,
        constants.TargetType.PLACEMENT,
        constants.TargetType.BROWSER,
        constants.TargetType.CONNECTION_TYPE,
    ]:
        # NOTE:  not known in advance
        return defaultdict(list)
    else:
        raise Exception("Unknown target type - should not be left unhandled")
