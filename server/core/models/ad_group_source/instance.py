from django.urls import reverse

import core.common
import core.features.bcm
import core.features.history
import core.models
import dash.constants


class AdGroupSourceInstanceMixin:
    def set_initial_settings(
        self, request, ad_group, skip_notification=False, write_history=True, is_adgroup_creation=False, **updates
    ):
        from dash.views import helpers

        self.settings = core.models.settings.AdGroupSourceSettings(ad_group_source=self)
        self.settings_id = self.settings.id

        if "cpc_cc" not in updates and "local_cpc_cc" not in updates:
            updates["cpc_cc"] = self.source.default_cpc_cc
            if ad_group.settings.is_mobile_only():
                updates["cpc_cc"] = self.source.default_mobile_cpc_cc
            if (
                ad_group.settings.b1_sources_group_enabled
                and ad_group.settings.b1_sources_group_cpc_cc is not None
                and ad_group.settings.b1_sources_group_cpc_cc > 0.0
                and self.source.source_type.type == dash.constants.SourceType.B1
            ):
                updates["cpc_cc"] = ad_group.settings.b1_sources_group_cpc_cc
            if ad_group.settings.cpc:
                updates["cpc_cc"] = min(ad_group.settings.cpc, updates["cpc_cc"])
        if "cpm" not in updates and "local_cpm" not in updates:
            updates["cpm"] = self.source.default_cpm
            if ad_group.settings.is_mobile_only():
                updates["cpm"] = self.source.default_mobile_cpm
            if (
                ad_group.settings.b1_sources_group_enabled
                and ad_group.settings.b1_sources_group_cpm is not None
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
        if "daily_budget_cc" not in updates and "local_daily_budget_cc" not in updates:
            updates["daily_budget_cc"] = self.source.default_daily_budget_cc

        if not is_adgroup_creation:
            enabling_autopilot_sources_allowed = (
                ad_group.campaign.account.agency_uses_realtime_autopilot()
                or helpers.enabling_autopilot_sources_allowed(ad_group, [self])
            )
            if not enabling_autopilot_sources_allowed:
                updates["state"] = dash.constants.AdGroupSourceSettingsState.INACTIVE

        self.settings.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            skip_notification=skip_notification,
            write_history=write_history,
            is_create=True,
            **updates,
        )
        self.save(None)

    def set_cloned_settings(self, request, source_ad_group_source):
        source_ad_group_source_settings = source_ad_group_source.settings
        self.settings = core.models.settings.AdGroupSourceSettings(ad_group_source=self)
        self.settings.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            is_create=True,
            daily_budget_cc=source_ad_group_source_settings.daily_budget_cc,
            cpc_cc=source_ad_group_source_settings.cpc_cc,
            cpm=source_ad_group_source_settings.cpm,
            state=source_ad_group_source_settings.state,
        )
        self.save(None)

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

    def save(self, request=None, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} - {}".format(self.ad_group, self.source)
