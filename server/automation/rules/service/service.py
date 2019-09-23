
import collections
from typing import DefaultDict
from typing import List
from typing import Sequence

import core.models

from .. import Rule
from .. import constants
from .apply import apply_rule


def process_rules() -> None:
    for target in constants.TargetType.get_all():
        rules = Rule.objects.filter(target=target).prefetch_related("ad_groups_included")
        rules_map = _get_rules_by_ad_group_map(rules)

        ad_groups = list(rules_map.keys())
        ad_groups_stats = _get_ad_groups_stats(ad_groups)

        for ad_group in ad_groups:
            relevant_rules = rules_map[ad_group]

            for rule in relevant_rules:
                apply_rule(ad_group, ad_groups_stats[ad_group.id], rule)


def _get_rules_by_ad_group_map(rules: Sequence[Rule]) -> DefaultDict[core.models.AdGroup, List[Rule]]:
    rules_map: DefaultDict[core.models.AdGroup, List[Rule]] = collections.defaultdict(list)

    for rule in rules:
        for ad_group in rule.ad_groups_included.all():
            rules_map[ad_group].append(rule)

    return rules_map


def _get_ad_groups_stats(ad_groups: Sequence[core.models.AdGroup]):
    return {}
