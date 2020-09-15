import traceback
from typing import Dict
from typing import List
from typing import Sequence
from typing import Union

from django.db.models import Exists
from django.db.models import OuterRef

import core.features.bid_modifiers.constants
import core.features.goals
import core.models
import dash.constants
import etl.materialization_run
from utils import dates_helper
from utils import zlogging

from .. import Rule
from .. import RuleHistory
from .. import RulesDailyJobLog
from .. import constants
from . import exceptions
from . import fetch
from . import helpers
from .actions import ValueChangeData
from .apply import apply_rule
from .notification_emails import send_notification_email_if_enabled

logger = zlogging.getLogger(__name__)


def execute_rules(rules: Sequence[Rule]) -> None:
    rules_by_target_type: Dict[int, List[Rule]] = {}
    for rule in rules:
        rules_by_target_type.setdefault(rule.target_type, [])
        rules_by_target_type[rule.target_type].append(rule)

    for target_type, rules in rules_by_target_type.items():
        rules_map = helpers.get_rules_by_ad_group_map(rules, filter_active=False)
        _apply_rules(target_type, rules_map)


def execute_rules_daily_run() -> None:
    if RulesDailyJobLog.objects.filter(created_dt__gte=dates_helper.local_midnight_to_utc_time()).exists():
        logger.info("Execution of rules was aborted since the daily run was already completed.")
        return

    if not etl.materialization_run.etl_data_complete_for_date(dates_helper.local_yesterday()):
        logger.info("Execution of rules was aborted since materialized data is not yet available.")
        return

    for target_type in constants.TargetType.get_all():
        rules = (
            Rule.objects.annotate(
                rule_history_exists_today=Exists(
                    RuleHistory.objects.filter(
                        rule_id=OuterRef("id"), created_dt__gte=dates_helper.local_midnight_to_utc_time()
                    )
                )
            )
            .filter(rule_history_exists_today=False, state=constants.RuleState.ENABLED, target_type=target_type)
            .exclude_archived()
            .prefetch_related("ad_groups_included", "campaigns_included", "accounts_included", "conditions")
        )

        rules_map = helpers.get_rules_by_ad_group_map(rules, exclude_inactive_yesterday=True)
        _apply_rules(target_type, rules_map)

    RulesDailyJobLog.objects.create()


def _apply_rules(target_type: int, rules_map: Dict[core.models.AdGroup, List[Rule]]):
    ad_groups = list(rules_map.keys())
    stats = fetch.query_stats(target_type, rules_map)
    ad_group_settings_map = _fetch_ad_group_settings(target_type, ad_groups, rules_map)
    campaign_budgets_map = fetch.prepare_budgets(ad_groups)
    content_ad_settings_map = {}
    if target_type == constants.TargetType.AD:
        content_ad_settings_map = fetch.prepare_content_ad_settings(ad_groups)

    for ad_group in ad_groups:
        relevant_rules = rules_map[ad_group]

        for rule in relevant_rules:
            try:
                changes = apply_rule(
                    rule,
                    ad_group,
                    stats.get(ad_group.id, {}),
                    ad_group_settings_map.get(ad_group.id, {}),
                    content_ad_settings_map.get(ad_group.id, {}),
                    campaign_budgets_map.get(ad_group.campaign_id, {}),
                )
            except exceptions.RuleArchived:
                continue
            except exceptions.ApplyFailedBase as e:
                history = _write_fail_history(rule, ad_group, exception=e)
            except Exception as e:
                history = _write_fail_history(rule, ad_group, exception=e, stack_trace=traceback.format_exc())
            else:
                history = _write_history(rule, ad_group, changes)

            send_notification_email_if_enabled(rule, ad_group, history)


def _fetch_ad_group_settings(
    target_type: int, ad_groups: Sequence[core.models.AdGroup], rules_map: Dict[core.models.AdGroup, List[Rule]]
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


def _write_history(rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData]):
    changes_dict = {c.target: c.to_dict() for c in changes}
    status = constants.ApplyStatus.SUCCESS if changes_dict else constants.ApplyStatus.SUCCESS_NO_CHANGES
    history = RuleHistory.objects.create(rule=rule, ad_group=ad_group, status=status, changes=changes_dict)

    ad_group.write_history(
        history.get_formatted_changes(),
        changes=changes_dict,
        system_user=dash.constants.SystemUserType.RULES,
        action_type=dash.constants.HistoryActionType.RULE_RUN,
    )
    return history


def _write_fail_history(
    rule: Rule, ad_group: core.models.AdGroup, *, exception: Exception, stack_trace: str = None
) -> RuleHistory:
    return RuleHistory.objects.create(
        rule=rule,
        ad_group=ad_group,
        failure_reason=_get_failure_reason(exception),
        status=constants.ApplyStatus.FAILURE,
    )


def _get_failure_reason(exception):
    if isinstance(exception, exceptions.CampaignAutopilotActive):
        return constants.RuleFailureReason.CAMPAIGN_AUTOPILOT_ACTIVE
    elif isinstance(exception, exceptions.BudgetAutopilotInactive):
        return constants.RuleFailureReason.BUDGET_AUTOPILOT_INACTIVE
    elif exception:
        return constants.RuleFailureReason.UNEXPECTED_ERROR
    else:
        return None


def _get_exception_text(exception: Exception) -> str:
    if isinstance(exception, exceptions.CampaignAutopilotActive):
        return "Automation rule can’t change the daily cap when campaign budget optimization is turned on."
    elif isinstance(exception, exceptions.BudgetAutopilotInactive):
        return "Automation rule can’t change the daily cap when daily cap autopilot is turned off."
    else:
        return "An error has occurred."
