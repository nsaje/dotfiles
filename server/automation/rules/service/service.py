import traceback
from collections import ChainMap
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from django.conf import settings

import core.features.bid_modifiers.constants
import core.features.goals
import core.models
import dash.constants
import etl.materialization_run
from utils import dates_helper
from utils import email_helper
from utils import zlogging

from .. import Rule
from .. import RuleHistory
from .. import RulesDailyJobLog
from .. import constants
from . import exceptions
from . import fetch
from . import helpers
from .actions import ValueChangeData
from .apply import ErrorData
from .apply import apply_rule

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
        rules = Rule.objects.filter(state=constants.RuleState.ENABLED, target_type=target_type).prefetch_related(
            "ad_groups_included", "conditions"
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
            exception: Optional[Exception] = None
            changes, errors = [], []
            try:
                changes, errors = apply_rule(
                    rule,
                    ad_group,
                    stats.get(ad_group.id, {}),
                    ad_group_settings_map.get(ad_group.id, {}),
                    content_ad_settings_map.get(ad_group.id, {}),
                    campaign_budgets_map.get(ad_group.campaign_id, {}),
                )
                _write_history(rule, ad_group, changes, errors)
            except exceptions.ApplyFailedBase as e:
                exception = e
                _write_fail_history(rule, ad_group, exception=e)
            except Exception as e:
                exception = e
                _write_fail_history(rule, ad_group, exception=e, stack_trace=traceback.format_exc())

            _send_notification_email_if_enabled(rule, ad_group, changes, errors, exception)


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


def _write_history(
    rule: Rule, ad_group: core.models.AdGroup, changes: Sequence[ValueChangeData], errors: Sequence[ErrorData]
):
    changes_dict = dict(ChainMap(*[c.to_dict() for c in changes]))
    changes_text = _get_changes_text(rule, ad_group, changes)

    if errors:
        changes_text += " " + _get_errors_text(errors)

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
    rule: Rule,
    ad_group: core.models.AdGroup,
    changes: Sequence[ValueChangeData],
    errors: Sequence[ErrorData],
    exception: Optional[Exception],
):
    if rule.notification_type == constants.NotificationType.NONE:
        return

    if changes:
        _send_changes_email(rule, ad_group, changes, errors)
    elif errors:
        _send_errors_email(rule, ad_group, errors)
    elif rule.notification_type == constants.NotificationType.ON_RULE_RUN:
        if exception:
            _send_exception_email(rule, ad_group, exception)
        else:
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


def _send_exception_email(rule: Rule, ad_group: core.models.AdGroup, exception: Exception):
    errors_text = _get_exception_text(exception)

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
    if not changes:
        return "No target updated."
    dashboard_targets = _get_changes_dashboard_targets(rule, ad_group, changes)
    return "Updated targets: {}".format(", ".join(dashboard_targets))


def _get_errors_text(errors: Sequence[ErrorData]) -> str:
    if not errors:
        return ""
    return f"Error occurred while trying to update {len(errors)} targets."


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


def _write_fail_history(
    rule: Rule, ad_group: core.models.AdGroup, *, exception: Exception, stack_trace: str = None
) -> RuleHistory:
    return RuleHistory.objects.create(
        rule=rule,
        ad_group=ad_group,
        status=constants.ApplyStatus.FAILURE,
        changes_text=_get_exception_text(exception),
        stack_trace=stack_trace,
    )


def _get_exception_text(exception: Exception) -> str:
    if isinstance(exception, exceptions.CampaignAutopilotActive):
        return "Automation rule can't change the daily cap when campaign budget optimisation is turned on."
    elif isinstance(exception, exceptions.BudgetAutopilotInactive):
        return "Automation rule can't change the daily cap when daily cap autopilot is turned off."
    else:
        return "An error has occurred."
