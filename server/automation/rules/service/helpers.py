from collections import defaultdict
from typing import DefaultDict
from typing import List
from typing import Sequence

import core.models

from .. import models


def get_rules_by_ad_group_map(rules: Sequence[models.Rule]) -> DefaultDict[core.models.AdGroup, List[models.Rule]]:
    rules_map: DefaultDict[core.models.AdGroup, List[models.Rule]] = defaultdict(list)
    for rule in rules:
        for ad_group in rule.ad_groups_included.filter_active().exclude_archived():
            rules_map[ad_group].append(rule)

    return rules_map
