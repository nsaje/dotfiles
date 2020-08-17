from django.conf import settings

from ... import constants
from ..common import RuleHistoryInstanceMixin
from . import formatters
from . import mapping

FORMATTED_CHANGES_TEMPLATES = {
    constants.TargetType.AD: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "on ads with IDs", mapping.get_empty_map, "Automation rule didn’t match for any ad."
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "on ads with IDs", mapping.get_empty_map, "Automation rule didn’t match for any ad."
        ),
        constants.ActionType.TURN_OFF: formatters.get_paused_formatter(
            "ads with IDs", mapping.get_empty_map, "Automation rule didn’t match for any ad."
        ),
    },
    constants.TargetType.AD_GROUP: {
        constants.ActionType.INCREASE_BID: formatters.get_bid_formatter(
            "Increased", "ad group", "Automation rule didn’t match for the ad group."
        ),
        constants.ActionType.DECREASE_BID: formatters.get_bid_formatter(
            "Decreased", "ad group", "Automation rule didn’t match for the ad group."
        ),
        constants.ActionType.INCREASE_BUDGET: formatters.get_budget_formatter(
            "Increased", "ad group", "Automation rule didn’t match for the ad group."
        ),
        constants.ActionType.DECREASE_BUDGET: formatters.get_budget_formatter(
            "Decreased", "ad group", "Automation rule didn’t match for the ad group."
        ),
        constants.ActionType.TURN_OFF: formatters.get_paused_formatter(
            "ad group", mapping.get_empty_map, "Automation rule didn’t match for the ad group."
        ),
        constants.ActionType.SEND_EMAIL: formatters.get_email_formatter(
            "ad group", "Automation rule didn’t match for the ad group."
        ),
    },
    constants.TargetType.PUBLISHER: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "on publishers", mapping.get_empty_map, "Automation rule didn’t match for any publisher."
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "on publishers", mapping.get_empty_map, "Automation rule didn’t match for any publisher."
        ),
        constants.ActionType.BLACKLIST: formatters.get_blacklist_formatter(
            "publishers", mapping.get_empty_map, "Automation rule didn’t match for any publisher."
        ),
        constants.ActionType.ADD_TO_PUBLISHER_GROUP: formatters.get_add_to_publisher_formatter(
            mapping.get_empty_map, "Automation rule didn’t match for any publisher."
        ),
    },
    constants.TargetType.DEVICE: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "on devices", mapping.get_device_types_map, "Automation rule didn’t match for any device."
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "on devices", mapping.get_device_types_map, "Automation rule didn’t match for any device."
        ),
    },
    constants.TargetType.COUNTRY: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for countries", mapping.get_geolocations_map, "Automation rule didn’t match for any country."
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for countries", mapping.get_geolocations_map, "Automation rule didn’t match for any country."
        ),
    },
    constants.TargetType.STATE: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for regions", mapping.get_geolocations_map, "Automation rule didn’t match for any region."
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for regions", mapping.get_geolocations_map, "Automation rule didn’t match for any region."
        ),
    },
    constants.TargetType.DMA: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased", "for DMAs", mapping.get_geolocations_map, "Automation rule didn’t match for any DMA."
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased", "for DMAs", mapping.get_geolocations_map, "Automation rule didn’t match for any DMA."
        ),
    },
    constants.TargetType.OS: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased",
            "for operating systems",
            mapping.get_operating_systems_map,
            "Automation rule didn’t match for any operating system.",
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased",
            "for operating systems",
            mapping.get_operating_systems_map,
            "Automation rule didn’t match for any operating system.",
        ),
    },
    constants.TargetType.ENVIRONMENT: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased",
            "for environments",
            mapping.get_environments_map,
            "Automation rule didn’t match for any environment.",
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased",
            "for environments",
            mapping.get_environments_map,
            "Automation rule didn’t match for any environment.",
        ),
    },
    constants.TargetType.SOURCE: {
        constants.ActionType.INCREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Increased",
            "on media sources",
            mapping.get_sources_map,
            "Automation rule didn’t match for any media source.",
        ),
        constants.ActionType.DECREASE_BID_MODIFIER: formatters.get_bid_modifier_formatter(
            "Decreased",
            "on media sources",
            mapping.get_sources_map,
            "Automation rule didn’t match for any media source.",
        ),
        constants.ActionType.TURN_OFF: formatters.get_paused_formatter(
            "media sources", mapping.get_sources_map, "Automation rule didn’t match for any media source."
        ),
    },
}


class RuleHistoryInstance(RuleHistoryInstanceMixin):
    def get_dashboard_link(self):
        agency_id = self.rule.agency_id or self.rule.account.agency_id
        return settings.BASE_URL + f"/v2/rules/history?agencyId={agency_id}&ruleId={self.rule.id}"

    def get_formatted_changes(self):
        if self.status == constants.ApplyStatus.SUCCESS:
            try:
                return FORMATTED_CHANGES_TEMPLATES[self.rule.target_type][self.rule.action_type](
                    self.rule.change_step, self.changes
                )
            except KeyError:
                return "N/A"
        else:
            return self.get_failure_reason()

    def get_failure_reason(self):
        if self.failure_reason == constants.RuleFailureReason.CAMPAIGN_AUTOPILOT_ACTIVE:
            return "Automation rule can't change the daily cap when campaign budget optimisation is turned on."
        elif self.failure_reason == constants.RuleFailureReason.BUDGET_AUTOPILOT_INACTIVE:
            return "Automation rule can't change the daily cap when budget autopilot is turned off."
        elif self.failure_reason == constants.RuleFailureReason.UNEXPECTED_ERROR:
            return "Automation rule failed to be applied because of an unforeseen error."
        else:
            "N/A"
