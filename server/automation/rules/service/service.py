
import collections
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Sequence

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
        stats = format_stats(raw_stats)

        for ad_group in ad_groups:
            relevant_rules = rules_map[ad_group]

            for rule in relevant_rules:
                apply_rule(ad_group, stats[ad_group.id], rule)


def _get_rules_by_ad_group_map(rules: Sequence[Rule]) -> DefaultDict[core.models.AdGroup, List[Rule]]:
    rules_map: DefaultDict[core.models.AdGroup, List[Rule]] = collections.defaultdict(list)

    for rule in rules:
        for ad_group in rule.ad_groups_included.all():
            rules_map[ad_group].append(rule)

    return rules_map


def format_stats(stats: Sequence[Dict]) -> Dict:
    return {}
