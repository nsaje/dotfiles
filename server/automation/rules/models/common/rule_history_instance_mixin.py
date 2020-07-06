from ... import constants
from ..rule_history import formatters
from ..rule_history import mapping

FORMATTED_CHANGES_TEMPLATES = {
    constants.TargetType.AD: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "on ads with IDs", mapping.get_empty_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "on ads with IDs", mapping.get_empty_map
        ),
        constants.ActionType.TURN_OFF: formatters.get_paused_formatter("ads with IDs", mapping.get_empty_map),
    },
    constants.TargetType.AD_GROUP: {
        constants.ActionType.INCREASE_BID: formatters.get_bid_formatter("Increased", "ad group"),
        constants.ActionType.DECREASE_BID: formatters.get_bid_formatter("Decreased", "ad group"),
        constants.ActionType.INCREASE_BUDGET: formatters.get_budget_formatter("Increased", "ad group"),
        constants.ActionType.DECREASE_BUDGET: formatters.get_budget_formatter("Decreased", "ad group"),
        constants.ActionType.TURN_OFF: formatters.get_paused_formatter("ad group", mapping.get_empty_map),
        constants.ActionType.SEND_EMAIL: formatters.get_email_formatter("ad group"),
    },
    constants.TargetType.PUBLISHER: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "on publishers", mapping.get_empty_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "on publishers", mapping.get_empty_map
        ),
        constants.ActionType.BLACKLIST: formatters.get_blacklist_formatter("publishers", mapping.get_empty_map),
        constants.ActionType.ADD_TO_PUBLISHER_GROUP: formatters.get_add_to_publisher_formatter(mapping.get_empty_map),
    },
    constants.TargetType.DEVICE: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "on devices", mapping.get_device_types_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "on devices", mapping.get_device_types_map
        ),
    },
    constants.TargetType.COUNTRY: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for countries", mapping.get_geolocations_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for countries", mapping.get_geolocations_map
        ),
    },
    constants.TargetType.STATE: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for states", mapping.get_geolocations_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for states", mapping.get_geolocations_map
        ),
    },
    constants.TargetType.DMA: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for DMAs", mapping.get_geolocations_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for DMAs", mapping.get_geolocations_map
        ),
    },
    constants.TargetType.OS: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for operating systems", mapping.get_operating_systems_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for operating systems", mapping.get_operating_systems_map
        ),
    },
    constants.TargetType.ENVIRONMENT: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for environments", mapping.get_environments_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for environments", mapping.get_environments_map
        ),
    },
    constants.TargetType.SOURCE: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "on media sources", mapping.get_sources_map
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "on media sources", mapping.get_sources_map
        ),
        constants.ActionType.TURN_OFF: formatters.get_paused_formatter("media sources", mapping.get_sources_map),
    },
}


class RuleHistoryInstanceMixin:
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise AssertionError("Updating rule history object is not allowed.")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssertionError("Deleting rule history object is not allowed.")

    def get_formatted_changes(self):
        if self.status == constants.ApplyStatus.SUCCESS:
            try:
                return FORMATTED_CHANGES_TEMPLATES[self.rule.target_type][self.rule.action_type](
                    self.rule.change_step, self.changes
                )
            except KeyError:
                return "N/A"
        else:
            return "N/A"
