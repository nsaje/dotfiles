from collections import ChainMap
from collections import defaultdict
from typing import Callable
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from django.conf import settings

import automation.models
import automation.rules.constants
import core.features.bid_modifiers.constants
import core.features.goals
import core.models
import dash.constants
import etl.materialization_run
import redshiftapi.api_rules
from utils import dates_helper
from utils import email_helper
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
        campaign_budgets_map = fetch.prepare_budgets(ad_groups)
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
                    campaign_budgets_map.get(ad_group.campaign_id, {}),
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

                _send_notification_email_if_enabled(rule, ad_group, changes, errors)

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


def _write_history(rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData]):
    changes_dict = dict(ChainMap(*[c.to_dict() for c in changes]))
    changes_text = _get_changes_text(rule, ad_group, changes)

    ad_group.write_history(
        changes_text,
        changes=changes_dict,
        system_user=dash.constants.SystemUserType.RULES,
        action_type=dash.constants.HistoryActionType.RULE_RUN,
    )
    RuleHistory.objects.create(
        rule=rule,
        ad_group=ad_group,
        status=constants.ApplyStatus.SUCCESS,
        changes=changes_dict,
        changes_text=changes_text,
    )


def _send_notification_email_if_enabled(
    rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData], errors: Sequence[ErrorData]
):
    if rule.notification_type == constants.NotificationType.NONE:
        return

    if changes:
        _send_changes_email(rule, ad_group, changes, errors)
    elif errors:
        _send_errors_email(rule, ad_group, errors)
    elif rule.notification_type == constants.NotificationType.ON_RULE_ACTION_TRIGGERED:
        _send_no_action_email(rule, ad_group)


def _send_changes_email(
    rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData], errors: Sequence[ErrorData]
):
    changes_text = _get_changes_text(rule, ad_group, changes)
    errors_text = _get_errors_text(errors)

    _send_email_from_template(
        ad_group.campaign.account.agency,
        rule.notification_recipients,
        dash.constants.EmailTemplateType.AUTOMATION_RULE_RUN,
        {
            "rule_name": rule.name,
            "ad_group_name": ad_group.name,
            "ad_group_link": settings.BASE_URL + f"/v2/analytics/adgroup/{ad_group.id}",
            "changes_text": changes_text,
            "errors_text": errors_text,
        },
    )


def _send_errors_email(rule: Rule, ad_group: core.models.AdGroup, errors: Sequence[ErrorData]):
    errors_text = _get_errors_text(errors)

    _send_email_from_template(
        ad_group.campaign.account.agency,
        rule.notification_recipients,
        dash.constants.EmailTemplateType.AUTOMATION_RULE_ERRORS,
        {
            "rule_name": rule.name,
            "ad_group_name": ad_group.name,
            "ad_group_link": settings.BASE_URL + f"/v2/analytics/adgroup/{ad_group.id}",
            "errors_text": errors_text,
        },
    )


def _send_no_action_email(rule: Rule, ad_group: core.models.AdGroup):
    _send_email_from_template(
        ad_group.campaign.account.agency,
        rule.notification_recipients,
        dash.constants.EmailTemplateType.AUTOMATION_RULE_NO_CHANGES,
        {
            "rule_name": rule.name,
            "ad_group_name": ad_group.name,
            "ad_group_link": settings.BASE_URL + f"/v2/analytics/adgroup/{ad_group.id}",
        },
    )


def _send_email_from_template(
    agency: core.models.Agency, recipient_list: List[str], template_type: int, template_params: Dict[str, str]
):
    for recipient in recipient_list:
        email_helper.send_official_email(
            agency_or_user=agency,
            recipient_list=[recipient],
            **email_helper.params_from_template(template_type, **template_params),
        )


def _get_changes_text(rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData]) -> str:
    dashboard_targets = _get_changes_dashboard_targets(rule, ad_group, changes)
    return "Updated targets: {}".format(", ".join(dashboard_targets))


def _get_changes_dashboard_targets(
    rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData]
) -> List[str]:
    if rule.target_type in constants.TARGET_TYPE_BID_MODIFIER_TYPE_MAPPING:
        bid_modifier_type = constants.TARGET_TYPE_BID_MODIFIER_TYPE_MAPPING[rule.target_type]
        return [
            str(core.features.bid_modifiers.converters.TargetConverter.from_target(bid_modifier_type, c.target))
            for c in changes
        ]
    else:
        return [str(c.target) for c in changes]


def _write_fail_history(rule: Rule, ad_group: core.models.AdGroup, errors: Sequence[ErrorData]) -> RuleHistory:
    return RuleHistory.objects.create(
        rule=rule,
        ad_group=ad_group,
        status=constants.ApplyStatus.FAILURE,
        changes=dict(ChainMap(*[e.to_dict() for e in errors])),
        changes_text=_get_errors_text(errors),
    )


def _get_errors_text(errors: Sequence[ErrorData], include_generic_error=True) -> str:
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
    if has_generic_errors and include_generic_error:
        messages.append("An error has occured.")

    return " ".join(messages)
