from collections import ChainMap
from collections import defaultdict
from typing import Callable
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

import automation.models
import automation.rules.constants
import core.features.bid_modifiers.constants
import core.features.goals
import core.models
import etl.materialization_run
import redshiftapi.api_rules
from utils import dates_helper
from utils import zlogging

from .. import Rule
from .. import RuleHistory
from .. import constants
from . import exceptions
from . import fetch
from .actions import ValueChangeData
from .apply import ErrorData
from .apply import apply_rule

logger = zlogging.getLogger(__name__)


def execute_rules() -> None:
    if automation.models.RulesDailyJobLog.objects.filter(created_dt__gte=dates_helper.utc_today()).exists():
        logger.info("Execution of rules was aborted since the daily run was already completed.")
        return

    if not etl.materialization_run.materialization_completed_for_local_today():
        logger.info("Execution of rules was aborted since materialized data is not yet available.")
        return

    for target_type in constants.TargetType.get_all():
        rules = Rule.objects.filter(state=constants.RuleState.ENABLED, target_type=target_type).prefetch_related(
            "ad_groups_included", "conditions"
        )

        rules_map = _get_rules_by_ad_group_map(rules)

        ad_groups = list(rules_map.keys())
        raw_stats = redshiftapi.api_rules.query(target_type, ad_groups)
        stats = _format_stats(target_type, raw_stats)
        ad_group_settings_map = _fetch_ad_group_settings(target_type, ad_groups, rules_map)
        content_ad_settings_map = {}
        if target_type == constants.TargetType.AD:
            content_ad_settings_map = fetch.prepare_content_ad_settings(ad_groups)

        for ad_group in ad_groups:
            relevant_rules = rules_map[ad_group]

            for rule in relevant_rules:
                changes, errors = apply_rule(
                    rule,
                    ad_group,
                    stats.get(ad_group.id, {}),
                    ad_group_settings_map.get(ad_group.id, {}),
                    content_ad_settings_map.get(ad_group.id, {}),
                )

                if changes:
                    _write_history(rule, ad_group, changes)

                if errors:
                    fail_history = _write_fail_history(rule, ad_group, errors)
                    logger.warning(
                        "Rule application failed.",
                        rule_id=str(rule),
                        ad_group_id=str(ad_group),
                        fail_history_id=str(fail_history),
                    )

    automation.models.RulesDailyJobLog.objects.create()


def _get_rules_by_ad_group_map(rules: Sequence[Rule]) -> DefaultDict[core.models.AdGroup, List[Rule]]:
    rules_map: DefaultDict[core.models.AdGroup, List[Rule]] = defaultdict(list)
    for rule in rules:
        for ad_group in rule.ad_groups_included.filter_active().exclude_archived():
            rules_map[ad_group].append(rule)

    return rules_map


def _format_stats(
    target_type: int, stats: Sequence[Dict]
) -> DefaultDict[int, DefaultDict[str, DefaultDict[str, DefaultDict[int, Optional[float]]]]]:

    dict_tree: Callable[[], DefaultDict] = lambda: defaultdict(dict_tree)  # noqa
    formatted_stats = dict_tree()

    target_column_keys = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]

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
            formatted_stats[ad_group_id][target_key][metric][window_key] = value

    return formatted_stats


def _fetch_ad_group_settings(
    target_type: int, ad_groups: Sequence[core.models.AdGroup], rules_map: DefaultDict[core.models.AdGroup, List[Rule]]
) -> Dict[int, Dict[str, Union[int, str]]]:
    include_campaign_goals = _any_condition_of_types(
        [
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL,
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE,
            constants.ValueType.CAMPAIGN_PRIMARY_GOAL_VALUE,
        ],
        ad_groups,
        rules_map,
    )
    include_ad_group_daily_cap = _any_condition_of_types(
        [constants.MetricType.AD_GROUP_DAILY_CAP, constants.ValueType.AD_GROUP_DAILY_CAP], ad_groups, rules_map
    )
    return fetch.prepare_ad_group_settings(
        ad_groups, include_campaign_goals=include_campaign_goals, include_ad_group_daily_cap=include_ad_group_daily_cap
    )


def _any_condition_of_types(target_types, ad_groups, rules_map) -> bool:
    for ad_group in ad_groups:
        for rule in rules_map[ad_group]:
            for rule_condition in rule.conditions.all():
                if (
                    rule_condition.left_operand_type in target_types
                    or rule_condition.right_operand_type in target_types
                ):
                    return True
    return False


def _write_history(rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData]) -> RuleHistory:
    if rule.target_type != constants.TargetType.AD_GROUP:
        bid_modifier_type = constants.TARGET_TYPE_BID_MODIFIER_TYPE_MAPPING[rule.target_type]
        dashboard_targets = [
            str(core.features.bid_modifiers.converters.TargetConverter.from_target(bid_modifier_type, c.target))
            for c in changes
        ]
    else:
        dashboard_targets = [str(c.target) for c in changes]

    return RuleHistory.objects.create(
        rule=rule,
        ad_group=ad_group,
        status=constants.ApplyStatus.SUCCESS,
        changes=dict(ChainMap(*[c.to_dict() for c in changes])),
        changes_text="Updated targets: {}".format(", ".join(dashboard_targets)),
    )


def _write_fail_history(rule: Rule, ad_group: core.models.AdGroup, errors: Sequence[ErrorData]) -> RuleHistory:
    return RuleHistory.objects.create(
        rule=rule,
        ad_group=ad_group,
        status=constants.ApplyStatus.FAILURE,
        changes=dict(ChainMap(*[e.to_dict() for e in errors])),
        changes_text=_get_fail_history_message(errors),
    )


def _get_fail_history_message(errors: Sequence[ErrorData]) -> str:
    has_campaign_autopilot_errors = has_budget_autopilot_errors = has_generic_errors = False
    autopilot_error_count = 0

    for error in errors:
        if isinstance(error.exc, exceptions.CampaignAutopilotActive):
            has_campaign_autopilot_errors = True
        elif isinstance(error.exc, exceptions.BudgetAutopilotInactive):
            has_budget_autopilot_errors = True
        elif isinstance(error.exc, exceptions.AutopilotActive):
            autopilot_error_count += 1
        else:
            has_generic_errors = True

    messages = []

    if has_campaign_autopilot_errors:
        messages.append("To change the autopilot daily budget the campaign budget optimization must not be active.")
    if has_budget_autopilot_errors:
        messages.append("To change the autopilot daily budget the autopilot goal optimization must be active.")
    if autopilot_error_count > 0:
        messages.append(
            (
                "To change the source bid modifier the campaign budget optimization and autopilot goal optimization must "
                "not be active; rule failed to make changes on {count} source{suffix}."
            ).format(count=autopilot_error_count, suffix="" if autopilot_error_count == 1 else "s")
        )
    if has_generic_errors:
        messages.append("An error has occured.")

    return " ".join(messages)
