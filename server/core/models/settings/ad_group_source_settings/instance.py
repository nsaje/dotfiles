from django.db import transaction

import core.features.bcm
import dash.constants
import utils.k1_helper
from core.features import bid_modifiers


class AdGroupSourceSettingsMixin(object):
    @transaction.atomic
    def update(
        self,
        request=None,
        k1_sync=True,
        system_user=None,
        skip_automation=False,
        skip_validation=False,
        skip_notification=False,
        write_history=True,
        is_create=False,
        **updates,
    ):
        if not updates:
            return None

        updates = self._filter_and_remap_input(updates)

        new_settings = self.copy_settings()
        for key, value in updates.items():
            if key == "state" and self.ad_group_source.ad_review_only:
                value = dash.constants.AdGroupSourceSettingsState.INACTIVE
            setattr(new_settings, key, value)

        changes = self.get_setting_changes(new_settings)
        if not changes:
            return None

        is_pause = len(changes) == 1 and changes.get("state") == dash.constants.AdGroupSourceSettingsState.INACTIVE
        if not skip_validation and not is_pause:
            self.clean(new_settings, is_create)

        if not skip_automation:
            self.validate_ad_group_source_autopilot(new_settings)

        old_settings = self.get_settings_dict()
        changes = self.get_setting_changes(new_settings)
        new_settings.save(request, system_user=system_user, write_history=write_history)
        if hasattr(self, "bid_modifier"):
            del self.bid_modifier

        self._update_ad_group_daily_budget(request, changes, is_create)

        if k1_sync:
            utils.k1_helper.update_ad_group(self.ad_group_source.ad_group, "AdGroupSource.update")

        if not skip_notification:
            self._notify_ad_group_source_settings_changed(request, old_settings, new_settings)

        return changes

    @transaction.atomic()
    def update_unsafe(self, request, system_user=None, write_history=True, **kwargs):
        kwargs_copy = kwargs.copy()
        kwargs_copy.pop("history_changes_text", None)
        changes = self.get_changes(kwargs_copy)
        super().update_unsafe(request, system_user=system_user, write_history=write_history, **kwargs)

        user = request.user if request else None

        agency_uses_realtime_autopilot = self.ad_group_source.ad_group.campaign.account.agency_uses_realtime_autopilot()
        autopilot_active = (
            self.ad_group_source.ad_group.settings.autopilot_state
            != dash.constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        if agency_uses_realtime_autopilot and autopilot_active:
            return

        bid_modifiers.source.handle_ad_group_source_settings_change(self, changes, user=user, system_user=system_user)

    def _filter_and_remap_input(self, updates):
        if self.ad_group_source.ad_group.bidding_type == dash.constants.BiddingType.CPM:
            self._remove_no_change_fields(updates, "cpc_cc")
            if "local_cpm_proxy" in updates:
                updates["local_cpm"] = updates.pop("local_cpm_proxy")
        else:
            self._remove_no_change_fields(updates, "cpm")
            if "local_cpc_cc_proxy" in updates:
                updates["local_cpc_cc"] = updates.pop("local_cpc_cc_proxy")
        return updates

    def _remove_no_change_fields(self, updates, field):
        local_field = "local_" + field
        if field in updates and updates[field] is None or local_field in updates and updates[local_field] is None:
            updates.pop(field, None)
            updates.pop(local_field, None)

    def _update_ad_group_daily_budget(self, request, changes, is_create):
        if is_create or "local_daily_budget_cc" not in changes:
            return

        self.ad_group_source.ad_group.settings.update_daily_budget(request)

    def _notify_ad_group_source_settings_changed(self, request, old_settings, new_settings):
        if not request:
            return

        changes = self.get_setting_changes(new_settings)
        changes_text_parts = []
        for key, val in list(changes.items()):
            if val is None:
                continue
            field = self.get_human_prop_name(key)
            val = self.get_human_value(key, val)
            source_name = self.ad_group_source.source.name
            old_val = old_settings[key]
            if old_val is None:
                text = "%s %s set to %s" % (source_name, field, val)
            else:
                old_val = self.get_human_value(key, old_val)
                text = "%s %s set from %s to %s" % (source_name, field, old_val, val)
            changes_text_parts.append(text)

        utils.email_helper.send_ad_group_notification_email(
            self.ad_group_source.ad_group, request, "\n".join(changes_text_parts)
        )

    def add_to_history(self, user, action_type, changes):
        if self.ad_group_source.ad_group.bidding_type == dash.constants.BiddingType.CPM:
            changes.pop("local_cpc_cc", None)
        else:
            changes.pop("local_cpm", None)

        _, changes_text = self.construct_changes(
            "Created settings.", "Source: {}.".format(self.ad_group_source.source.name), changes
        )
        self.ad_group_source.ad_group.write_history(
            changes_text, changes=changes, user=user, action_type=action_type, system_user=self.system_user
        )

    def get_external_daily_budget_cc(self, service_fee, license_fee, margin):
        return core.features.bcm.calculations.subtract_fees_and_margin(
            self.daily_budget_cc, service_fee, license_fee, margin
        )

    def get_currency(self):
        return self.ad_group_source.ad_group.campaign.account.currency

    def recalculate_multicurrency_values(self):
        fields = ["local_" + field for field in self.ad_group_source.settings.multicurrency_fields]
        updates = {
            field: getattr(self.ad_group_source.settings, field)
            for field in fields
            if getattr(self.ad_group_source.settings, field) is not None
        }
        changes = self.ad_group_source.settings.update(
            None, skip_automation=True, skip_validation=True, skip_notification=True, **updates
        )
        return changes
