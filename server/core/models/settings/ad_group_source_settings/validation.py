import decimal

from dash import constants

from . import exceptions
from . import validation_helpers


class AdGroupSourceSettingsValidatorMixin(object):
    def clean(self, new_settings, is_create):
        bcm_modifiers = self.ad_group_source.ad_group.campaign.get_bcm_modifiers()
        self._validate_ad_group_source_cpc(new_settings, bcm_modifiers)
        self._validate_ad_group_source_cpm(new_settings, bcm_modifiers)
        self._validate_ad_group_source_daily_budget(new_settings, bcm_modifiers, is_create)

    def _validate_ad_group_source_cpc(self, new_settings, bcm_modifiers):
        is_cpm_buying = self.ad_group_source.ad_group.bidding_type == constants.BiddingType.CPM
        if is_cpm_buying and new_settings.cpc_cc != self.cpc_cc:
            raise exceptions.CannotSetCPC("Cannot set ad group source CPC when ad group bidding type is CPM")
        if new_settings.cpc_cc is None or is_cpm_buying and new_settings.cpc_cc == self.cpc_cc:
            return
        assert isinstance(new_settings.cpc_cc, decimal.Decimal)
        validation_helpers.validate_ad_group_source_cpc_cc(new_settings.cpc_cc, self.ad_group_source, bcm_modifiers)

    def _validate_ad_group_source_cpm(self, new_settings, bcm_modifiers):
        is_cpm_buying = self.ad_group_source.ad_group.bidding_type == constants.BiddingType.CPM
        if not is_cpm_buying and new_settings.cpm != self.cpm:
            raise exceptions.CannotSetCPM("Cannot set ad group source CPM when ad group bidding type is CPC")
        if new_settings.cpm is None or not is_cpm_buying and new_settings.cpm == self.cpm:
            return
        assert isinstance(new_settings.cpm, decimal.Decimal)
        validation_helpers.validate_ad_group_source_cpm(new_settings.cpm, self.ad_group_source, bcm_modifiers)

    def _validate_ad_group_source_daily_budget(self, new_settings, bcm_modifiers, is_create):
        if (
            not is_create
            and new_settings.daily_budget_cc != self.daily_budget_cc
            and self.ad_group_source.ad_group.settings.b1_sources_group_enabled
        ):
            raise exceptions.BudgetUpdateWhileSourcesGroupEnabled(
                "Can not set individual source daily budgets while managing RTB sources as a group"
            )
        if new_settings.daily_budget_cc is None:
            return
        assert isinstance(new_settings.daily_budget_cc, decimal.Decimal)
        validation_helpers.validate_daily_budget_cc(
            new_settings.daily_budget_cc, self.ad_group_source.source.source_type, bcm_modifiers
        )

    def validate_ad_group_source_autopilot(self, new_settings):
        from dash.views import helpers

        campaign = self.ad_group_source.ad_group.campaign
        if not campaign.real_time_campaign_stop:
            return

        changes = self.get_setting_changes(new_settings)
        if "state" not in changes:
            return

        if new_settings.state != constants.AdGroupSourceSettingsState.ACTIVE:
            return

        enabling_autopilot_sources_allowed = self.ad_group_source.ad_group.campaign.account.agency_uses_realtime_autopilot() or helpers.enabling_autopilot_sources_allowed(
            self.ad_group_source.ad_group, [self.ad_group_source]
        )
        if not enabling_autopilot_sources_allowed:
            raise exceptions.AutopilotDailySpendCapTooLow(
                "Please increase Autopilot Daily Spend Cap to enable this source."
            )
