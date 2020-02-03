
from django.urls import reverse

import core.common
import core.features.bcm
import core.features.history
import core.models
import dash.constants
import utils.dates_helper
import utils.email_helper
import utils.exc
import utils.k1_helper
import utils.numbers


class AdGroupSourceInstanceMixin:
    def set_initial_settings(self, request, ad_group, skip_notification=False, write_history=True, **updates):
        from dash.views import helpers

        if "cpc_cc" not in updates:
            updates["cpc_cc"] = self.source.default_cpc_cc
            if ad_group.settings.is_mobile_only():
                updates["cpc_cc"] = self.source.default_mobile_cpc_cc
            if (
                ad_group.settings.b1_sources_group_enabled
                and ad_group.settings.b1_sources_group_cpc_cc > 0.0
                and self.source.source_type.type == dash.constants.SourceType.B1
            ):
                updates["cpc_cc"] = ad_group.settings.b1_sources_group_cpc_cc
            if ad_group.settings.cpc:
                updates["cpc_cc"] = min(ad_group.settings.cpc, updates["cpc_cc"])
        if "cpm" not in updates:
            updates["cpm"] = self.source.default_cpm
            if ad_group.settings.is_mobile_only():
                updates["cpm"] = self.source.default_mobile_cpm
            if (
                ad_group.settings.b1_sources_group_enabled
                and ad_group.settings.b1_sources_group_cpm > 0.0
                and self.source.source_type.type == dash.constants.SourceType.B1
            ):
                updates["cpm"] = ad_group.settings.b1_sources_group_cpm
            if ad_group.settings.cpm:
                updates["cpm"] = min(ad_group.settings.cpm, updates["cpm"])
        if "state" not in updates:
            if helpers.get_source_initial_state(self):
                updates["state"] = dash.constants.AdGroupSourceSettingsState.ACTIVE
            else:
                updates["state"] = dash.constants.AdGroupSourceSettingsState.INACTIVE
        if "daily_budget_cc" not in updates:
            updates["daily_budget_cc"] = self.source.default_daily_budget_cc

        enabling_autopilot_sources_allowed = helpers.enabling_autopilot_sources_allowed(ad_group, [self])
        if not enabling_autopilot_sources_allowed:
            updates["state"] = dash.constants.AdGroupSourceSettingsState.INACTIVE

        self.settings.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            skip_notification=skip_notification,
            write_history=write_history,
            **updates
        )

    def set_cloned_settings(self, request, source_ad_group_source):
        source_ad_group_source_settings = source_ad_group_source.get_current_settings()
        self.settings.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            daily_budget_cc=source_ad_group_source_settings.daily_budget_cc,
            cpc_cc=source_ad_group_source_settings.cpc_cc,
            cpm=source_ad_group_source_settings.cpm,
            state=source_ad_group_source_settings.state,
        )

    def get_tracking_ids(self):
        msid = self.source.tracking_slug or ""
        if self.source.source_type and self.source.source_type.type in [
            dash.constants.SourceType.ZEMANTA,
            dash.constants.SourceType.B1,
            dash.constants.SourceType.OUTBRAIN,
        ]:
            msid = "{sourceDomain}"

        return "_z1_adgid={}&_z1_msid={}".format(self.ad_group_id, msid)

    def get_external_name(self, new_adgroup_name=None):
        account_name = self.ad_group.campaign.account.name
        campaign_name = self.ad_group.campaign.name
        if new_adgroup_name is None:
            ad_group_name = self.ad_group.name
        else:
            ad_group_name = new_adgroup_name
        ad_group_id = self.ad_group.id
        source_name = self.source.name
        return "ONE: {} / {} / {} / {} / {}".format(
            core.models.helpers.shorten_name(account_name),
            core.models.helpers.shorten_name(campaign_name),
            core.models.helpers.shorten_name(ad_group_name),
            ad_group_id,
            source_name,
        )

    def get_supply_dash_url(self):
        if not self.source.has_3rd_party_dashboard():
            return None

        return "{}?ad_group_id={}&source_id={}".format(
            reverse("supply_dash_redirect"), self.ad_group.id, self.source.id
        )

    def get_current_settings(self):
        return self.settings

    def migrate_to_bcm_v2(self, request, fee, margin):
        current_settings = self.get_current_settings()
        changes = {
            "daily_budget_cc": self._transform_daily_budget_cc(current_settings.daily_budget_cc, fee, margin),
            "cpc_cc": self._transform_cpc_cc(current_settings.cpc_cc, fee, margin),
        }

        self.settings.update(
            request=request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            skip_notification=True,
            **changes
        )

    def _transform_daily_budget_cc(self, daily_budget_cc, fee, margin):
        if not daily_budget_cc:
            return daily_budget_cc
        new_daily_budget_cc = core.features.bcm.calculations.apply_fee_and_margin(daily_budget_cc, fee, margin)
        return utils.numbers.round_decimal_ceiling(new_daily_budget_cc, places=0)

    def _transform_cpc_cc(self, cpc_cc, fee, margin):
        if not cpc_cc:
            return cpc_cc
        new_cpc_cc = core.features.bcm.calculations.apply_fee_and_margin(cpc_cc, fee, margin)
        return utils.numbers.round_decimal_half_down(new_cpc_cc, places=3)

    def save(self, request=None, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} - {}".format(self.ad_group, self.source)
