import core.features.bid_modifiers
import core.models

from .. import Rule
from .. import constants


def adjust_bid_modifier(target: str, rule: Rule, ad_group: core.models.AdGroup) -> bool:
    if rule.action_type == constants.ActionType.INCREASE_BID_MODIFIER:
        limiter, change = min, rule.change_step
    elif rule.action_type == constants.ActionType.DECREASE_BID_MODIFIER:
        limiter, change = max, -rule.change_step
    else:
        raise Exception("Invalid action type")

    if rule.target_type == constants.TargetType.PUBLISHER:
        target, source_id = target.split("__")

    bid_modifier_type = constants.TARGET_TYPE_BID_MODIFIER_TYPE_MAPPING[rule.target_type]
    target = core.features.bid_modifiers.TargetConverter.to_target(bid_modifier_type, target)
    source = (
        core.models.Source.objects.get(id=source_id) if rule.target_type == constants.TargetType.PUBLISHER else None
    )

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

    return modifier != base_modifier
