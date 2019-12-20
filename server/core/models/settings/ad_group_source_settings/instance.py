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
            self.clean(new_settings)

        if not skip_automation:
            self.validate_ad_group_source_autopilot(new_settings)

        old_settings = self.get_settings_dict()
        changes = self.get_setting_changes(new_settings)
        new_settings.save(request, system_user=system_user, write_history=write_history)

        if not skip_automation:
            # autopilot reloads settings so changes have to be saved when it is called
            autopilot_changed_sources = self._handle_budget_autopilot(changes)
            if autopilot_changed_sources:
                changes["autopilot_changed_sources"] = autopilot_changed_sources

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

        bid_modifiers.source.handle_ad_group_source_settings_change(self, changes, user=user, system_user=system_user)

    def _filter_and_remap_input(self, updates):
        if self.ad_group_source.ad_group.bidding_type == dash.constants.BiddingType.CPM:
            self._remove_no_change_fields(updates, "cpc_cc")
        else:
            self._remove_no_change_fields(updates, "cpm")
        return updates

    def _remove_no_change_fields(self, updates, field):
        local_field = "local_" + field
        if field in updates and updates[field] is None or local_field in updates and updates[local_field] is None:
            updates.pop(field, None)
            updates.pop(local_field, None)

    def _handle_budget_autopilot(self, changes):
        ad_group_settings = self.ad_group_source.ad_group.settings
        if "state" in changes and (
            ad_group_settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            or self.ad_group_source.ad_group.campaign.settings.autopilot
        ):
            from automation import autopilot

            changed_sources = autopilot.recalculate_budgets_ad_group(self.ad_group_source.ad_group)
            return [s.source.name for s in changed_sources]
        return []

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

    def get_external_daily_budget_cc(self, account, license_fee, margin):
        daily_budget_cc = self.daily_budget_cc
        if account.uses_bcm_v2:
            daily_budget_cc = core.features.bcm.calculations.subtract_fee_and_margin(
                daily_budget_cc, license_fee, margin
            )
        return daily_budget_cc

    def get_external_cpc_cc(self, account, license_fee, margin):
        cpc_cc = self.cpc_cc
        if account.uses_bcm_v2:
            cpc_cc = core.features.bcm.calculations.subtract_fee_and_margin(cpc_cc, license_fee, margin)
        return cpc_cc

    def get_external_cpm(self, account, license_fee, margin):
        cpm = self.cpm
        if cpm and account.uses_bcm_v2:
            cpm = core.features.bcm.calculations.subtract_fee_and_margin(cpm, license_fee, margin)
        return cpm

    def get_currency(self):
        return self.ad_group_source.ad_group.campaign.account.currency
