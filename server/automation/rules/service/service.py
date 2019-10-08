
from collections import defaultdict
from typing import Callable
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Sequence
from typing import Union

import automation.rules.constants
import core.models
import redshiftapi.api_rules

from .. import Rule
from .. import constants
from .apply import apply_rule


def process_rules() -> None:
    for target in [constants.TargetType.PUBLISHER]:
        rules = Rule.objects.filter(target=target).prefetch_related("ad_groups_included", "conditions")
        rules_map = _get_rules_by_ad_group_map(rules)

        ad_groups = list(rules_map.keys())
        raw_stats = redshiftapi.api_rules.query(target, ad_groups)
        stats = _format_stats(target, raw_stats)

        for ad_group in ad_groups:
            relevant_rules = rules_map[ad_group]

            for rule in relevant_rules:
                apply_rule(ad_group, stats.get(ad_group.id), rule)


def _get_rules_by_ad_group_map(rules: Sequence[Rule]) -> DefaultDict[core.models.AdGroup, List[Rule]]:
    rules_map: DefaultDict[core.models.AdGroup, List[Rule]] = defaultdict(list)

    for rule in rules:
        for ad_group in rule.ad_groups_included.all():
            rules_map[ad_group].append(rule)

    return rules_map


def _format_stats(
    target: int, stats: Sequence[Dict]
) -> DefaultDict[int, DefaultDict[str, DefaultDict[str, DefaultDict[int, Union[None, int, float]]]]]:

    dict_tree: Callable[[], DefaultDict] = lambda: defaultdict(dict_tree)  # noqa
    formatted_stats = dict_tree()

    target_column_keys = automation.rules.constants.TARGET_MV_COLUMNS_MAPPING[target]

    for row in stats:
        ad_group_id = row.pop("ad_group_id", None)
        target_key = row.pop(target_column_keys[0], None)
        target_extra_keys = {key: row.pop(key, None) for key in target_column_keys[1:]}
        window_key = row.pop("window_key", None)

        if None in (ad_group_id, window_key, target_key):
            continue

        for metric, value in row.items():
            formatted_stats[ad_group_id][target_key][metric][window_key] = value

        for key, value in target_extra_keys.items():
            formatted_stats[ad_group_id][target_key][key] = value

    return formatted_stats
