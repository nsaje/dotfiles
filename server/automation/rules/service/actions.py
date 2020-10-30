import dataclasses
from decimal import Decimal
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import core.features.bid_modifiers
import core.features.publisher_groups
import core.models
import dash.constants
import utils.email_helper
from dash import publisher_helpers

from .. import Rule
from .. import config
from .. import constants
from ..common import macros
from . import helpers


@dataclasses.dataclass
class ValueChangeData:
    target: str
    old_value: Optional[Union[str, float]] = None
    new_value: Optional[Union[str, float]] = None

    def has_changes(self) -> bool:
        return self.new_value != self.old_value

    def to_dict(self) -> Dict[str, Optional[Union[str, float]]]:
        return {"old_value": self.old_value, "new_value": self.new_value}


def adjust_bid(target: str, rule: Rule, ad_group: core.models.AdGroup, **kwargs) -> ValueChangeData:
    if int(target) != ad_group.id:
        raise Exception("Invalid ad group bid adjustment target")

    if rule.action_type == constants.ActionType.INCREASE_BID:
        limiter, change = min, rule.change_step
    elif rule.action_type == constants.ActionType.DECREASE_BID:
        limiter, change = max, -rule.change_step
    else:
        raise Exception("Invalid bid action type")

    old_value = ad_group.settings.local_bid
    new_value = limiter(old_value + Decimal(str(change)), Decimal(str(rule.change_limit)))

    ad_group.settings.update(None, local_bid=new_value)

    return ValueChangeData(target=target, old_value=float(old_value), new_value=float(new_value))


def adjust_autopilot_daily_budget(target: str, rule: Rule, ad_group: core.models.AdGroup, **kwargs) -> ValueChangeData:
    if int(target) != ad_group.id:
        raise Exception("Invalid ad group autopilot budget adjustment target")

    if rule.action_type == constants.ActionType.INCREASE_BUDGET:
        limiter, change = min, rule.change_step
    elif rule.action_type == constants.ActionType.DECREASE_BUDGET:
        limiter, change = max, -rule.change_step
    else:
        raise Exception("Invalid budget action type")

    helpers.ensure_ad_group_valid(rule, ad_group)

    # TODO: RTAP: update on migration; need to decide which field to use, as the functionality like it is now won't exist anymore.
    # Rule validation will also have to be fixed as the conditions are very specific.
    base_budget = ad_group.settings.local_autopilot_daily_budget
    budget = limiter(base_budget + Decimal(change), Decimal(rule.change_limit))

    ad_group.settings.update(None, local_autopilot_daily_budget=budget)

    return ValueChangeData(target=target, old_value=float(base_budget), new_value=float(budget))


def adjust_bid_modifier(target: str, rule: Rule, ad_group: core.models.AdGroup, **kwargs) -> ValueChangeData:
    if rule.action_type == constants.ActionType.INCREASE_BID_MODIFIER:
        limiter, change = min, rule.change_step
    elif rule.action_type == constants.ActionType.DECREASE_BID_MODIFIER:
        limiter, change = max, -rule.change_step
    else:
        raise Exception("Invalid bid modifier action type")

    helpers.ensure_ad_group_valid(rule, ad_group)

    if rule.target_type == constants.TargetType.PUBLISHER:
        target, source_id = target.split("__")

    if rule.target_type == constants.TargetType.PLACEMENT:
        source_id = target.split("__")[1]

    bid_modifier_type = constants.TARGET_TYPE_BID_MODIFIER_TYPE_MAPPING[rule.target_type]
    target = core.features.bid_modifiers.StatsConverter.to_target(
        bid_modifier_type, int(target) if target.isdigit() else target
    )

    source = None
    if rule.target_type in [constants.TargetType.PUBLISHER, constants.TargetType.PLACEMENT]:
        source = core.models.Source.objects.get(id=source_id)

    try:
        base_modifier = core.features.bid_modifiers.BidModifier.objects.values_list("modifier", flat=True).get(
            ad_group=ad_group, type=bid_modifier_type, target=target, source=source
        )

    except core.features.bid_modifiers.BidModifier.DoesNotExist:
        base_modifier = 1.0

    modifier = limiter(base_modifier + change, rule.change_limit)

    core.features.bid_modifiers.set(
        ad_group, bid_modifier_type, target, source, modifier, write_history=False, propagate_to_k1=False
    )

    return ValueChangeData(target=target, old_value=base_modifier, new_value=modifier)


def turn_off(target: str, rule: Rule, ad_group: core.models.AdGroup, **kwargs) -> ValueChangeData:
    if rule.action_type != constants.ActionType.TURN_OFF:
        raise Exception("Invalid action type for turning off")

    if rule.target_type == constants.TargetType.AD_GROUP:
        if int(target) != ad_group.id:
            raise Exception("Invalid ad group turn off target")

        settings, off_state = ad_group.settings, dash.constants.AdGroupSettingsState.INACTIVE

    elif rule.target_type == constants.TargetType.AD:
        try:
            content_ad = core.models.ContentAd.objects.get(id=int(target), ad_group=ad_group)
        except core.models.ContentAd.DoesNotExist:
            raise Exception("Invalid ad turn off target")

        settings, off_state = content_ad, dash.constants.ContentAdSourceState.INACTIVE

    elif rule.target_type == constants.TargetType.SOURCE:
        try:
            ad_group_source = core.models.AdGroupSource.objects.select_related("settings").get(
                source__id=int(target), ad_group=ad_group
            )
        except core.models.AdGroupSource.DoesNotExist:
            raise Exception("Invalid source turn off target")

        settings, off_state = ad_group_source.settings, dash.constants.AdGroupSourceSettingsState.INACTIVE

    state = settings.state
    settings.update(None, state=off_state)

    return ValueChangeData(target=target, old_value=state, new_value=off_state)


def send_email(
    target: str, rule: Rule, ad_group: core.models.AdGroup, *, target_stats: Dict[str, Dict[int, Any]], **kwargs
):
    if rule.action_type != constants.ActionType.SEND_EMAIL:
        raise Exception("Invalid action type")

    if int(target) != ad_group.id:
        raise Exception("Invalid target")

    recipients = rule.send_email_recipients
    subject = macros.expand(rule.send_email_subject, ad_group, target_stats)
    body = macros.expand(rule.send_email_body, ad_group, target_stats)

    utils.email_helper.send_official_email(rule.agency, recipient_list=recipients, subject=subject, body=body)
    return ValueChangeData(target=target, old_value=None, new_value="Email sent.")


def blacklist(target: str, rule: Rule, ad_group: core.models.AdGroup, **kwargs) -> ValueChangeData:
    if rule.action_type != constants.ActionType.BLACKLIST:
        raise Exception("Invalid action type for blacklisting")

    if rule.target_type not in config.VALID_TARGET_TYPES_FOR_ACTION[constants.ActionType.BLACKLIST]:
        raise Exception("Invalid blacklist target")

    entries = _prepare_publisher_placement_entries(target, rule)
    core.features.publisher_groups.blacklist_publishers(None, entries, ad_group, should_write_history=False)
    return ValueChangeData(
        target=target,
        old_value=dash.constants.PublisherStatus.ENABLED,
        new_value=dash.constants.PublisherStatus.BLACKLISTED,
    )


def add_to_publisher_group(target: str, rule: Rule, ad_group: core.models.AdGroup, **kwargs) -> ValueChangeData:
    if rule.action_type != constants.ActionType.ADD_TO_PUBLISHER_GROUP:
        raise Exception("Invalid action type for adding to publisher group")

    if rule.target_type not in config.VALID_TARGET_TYPES_FOR_ACTION[constants.ActionType.ADD_TO_PUBLISHER_GROUP]:
        raise Exception("Invalid add to publisher group target")

    entries = _prepare_publisher_placement_entries(target, rule)
    core.features.publisher_groups.add_publisher_group_entries(
        None, rule.publisher_group, entries, should_write_history=False
    )
    return ValueChangeData(target=target, old_value=None, new_value="Added to publisher group")


def _prepare_publisher_placement_entries(target: str, rule: Rule):
    placement = None
    if rule.target_type == constants.TargetType.PUBLISHER:
        publisher, source_id = publisher_helpers.dissect_publisher_id(target)
    elif rule.target_type == constants.TargetType.PLACEMENT:
        publisher, source_id, placement = publisher_helpers.dissect_placement_id(target)
    else:
        raise Exception("Invalid target type")

    source = core.models.Source.objects.get(id=source_id)

    entry = {"publisher": publisher, "source": source, "include_subdomains": False}
    if placement:
        entry["placement"] = placement
    return [entry]
