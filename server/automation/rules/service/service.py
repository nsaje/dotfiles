import datetime
import traceback
from collections import ChainMap
from collections import defaultdict
from typing import Callable
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence

import automation.models
import automation.rules.constants
import core.models
import etl.models
import redshiftapi.api_rules
from utils import dates_helper
from utils import zlogging

from .. import Rule
from .. import RuleHistory
from .. import constants
from .actions import ValueChangeData
from .apply import apply_rule

logger = zlogging.getLogger(__name__)


def execute_rules() -> None:
    if automation.models.RulesDailyJobLog.objects.filter(created_dt__gte=dates_helper.utc_today()).exists():
        logger.info("Execution of rules was aborted since the daily run was already completed.")
        return

    # after EST midnight wait 2h for data to be available + 3h for refresh_etl to complete
    from_date_time = dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5)

    if not etl.models.MaterializationRun.objects.filter(finished_dt__gte=from_date_time).exists():
        logger.info("Execution of rules was aborted since materialized data is not yet available.")
        return

    for target_type in [constants.TargetType.PUBLISHER]:
        rules = Rule.objects.filter(state=constants.RuleState.ENABLED, target_type=target_type).prefetch_related(
            "ad_groups_included", "conditions"
        )

        rules_map = _get_rules_by_ad_group_map(rules)

        ad_groups = list(rules_map.keys())
        raw_stats = redshiftapi.api_rules.query(target_type, ad_groups)
        stats = _format_stats(target_type, raw_stats)

        for ad_group in ad_groups:
            relevant_rules = rules_map[ad_group]

            for rule in relevant_rules:
                try:
                    changes = apply_rule(rule, ad_group, stats.get(ad_group.id, {}))
                    if changes:
                        _write_history(rule, ad_group, constants.ApplyStatus.SUCCESS, changes=changes)

                except Exception as e:
                    logger.warning(
                        "Rule application failed: {}".format(str(e)), ad_group_id=str(ad_group), rule_id=str(rule)
                    )
                    _write_history(rule, ad_group, constants.ApplyStatus.FAILURE, changes_text=traceback.format_exc())

    automation.models.RulesDailyJobLog.objects.create()


def _get_rules_by_ad_group_map(rules: Sequence[Rule]) -> DefaultDict[core.models.AdGroup, List[Rule]]:
    rules_map: DefaultDict[core.models.AdGroup, List[Rule]] = defaultdict(list)

    for rule in rules:
        for ad_group in rule.ad_groups_included.all():
            rules_map[ad_group].append(rule)

    return rules_map


def _format_stats(
    target_type: int, stats: Sequence[Dict]
) -> DefaultDict[int, DefaultDict[str, DefaultDict[str, DefaultDict[int, Optional[float]]]]]:

    dict_tree: Callable[[], DefaultDict] = lambda: defaultdict(dict_tree)  # noqa
    formatted_stats = dict_tree()

    target_column_keys = automation.rules.constants.TARGET_TYPE_MV_COLUMNS_MAPPING[target_type]

    for row in stats:
        ad_group_id = row.pop("ad_group_id", None)
        target_key_group = tuple(row.pop(t, None) for t in target_column_keys)
        window_key = row.pop("window_key", None)

        if not all([ad_group_id, all(target_key_group), window_key]):
            continue

        target_key = "__".join(map(str, target_key_group))

        for metric, value in row.items():
            formatted_stats[ad_group_id][target_key][metric][window_key] = value

    return formatted_stats


def _write_history(
    rule: Rule,
    ad_group: core.models.AdGroup,
    status: int,
    changes: Optional[Sequence[ValueChangeData]] = None,
    changes_text: Optional[str] = None,
) -> None:
    if changes and changes_text is None:
        # TODO: text formatting
        changes_text = "Updated targets: {}".format(", ".join([str(change.target) for change in changes]))

    RuleHistory.objects.create(
        rule=rule,
        ad_group=ad_group,
        status=status,
        changes=dict(ChainMap(*[c.to_dict() for c in changes])) if changes else None,
        changes_text=changes_text,
    )
