import dataclasses
from typing import Dict
from typing import Optional
from typing import Union

import core.features.bid_modifiers
import core.models

from .. import Rule
from .. import constants


@dataclasses.dataclass
class ValueChangeData:
    target: Union[str, int]
    old_value: Optional[Union[str, float]] = None
    new_value: Optional[Union[str, float]] = None

    def has_changes(self) -> bool:
        return self.new_value != self.old_value

    def to_dict(self) -> Dict[Union[str, int], Dict[str, Optional[Union[str, float]]]]:
        return {self.target: {"old_value": self.old_value, "new_value": self.new_value}}


def adjust_bid_modifier(target: str, rule: Rule, ad_group: core.models.AdGroup) -> ValueChangeData:
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

    return ValueChangeData(target=target, old_value=base_modifier, new_value=modifier)
