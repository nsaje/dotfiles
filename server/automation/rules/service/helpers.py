from collections import defaultdict
from typing import Dict
from typing import List
from typing import Sequence

import core.models

from .. import models


def get_rules_by_ad_group_map(
    rules: Sequence[models.Rule], *, filter_active: bool = True
) -> Dict[core.models.AdGroup, List[models.Rule]]:
    rules_map: Dict[core.models.AdGroup, List[models.Rule]] = defaultdict(list)
    for rule in rules:
        ad_groups = rule.ad_groups_included.exclude_archived()
        if filter_active:
            ad_groups = ad_groups.filter_active()

        for ad_group in ad_groups:
            rules_map[ad_group].append(rule)

    return rules_map
