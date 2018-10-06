from django.db import transaction

from dash import constants
from dash import retargeting_helper
from utils import email_helper
from utils import k1_helper
from utils import redirector_helper
from utils import exc

import core.features.audiences
import core.common
import core.models
import core.features.history
import core.signals


class AdGroupSettingsMixin(object):
    @transaction.atomic
    def update(
        self,
        request,
        skip_validation=False,
        skip_automation=False,
        skip_permission_check=False,
        system_user=None,
        **updates
    ):
        updates = self._filter_and_remap_input(request, updates, skip_permission_check)
        self._update_ad_group(request, updates)
        if updates:
            new_settings = self.copy_settings()
            self._apply_updates(new_settings, updates)
            is_pause = len(updates) == 1 and updates.get("state") == constants.AdGroupSettingsState.INACTIVE
            if not skip_validation and not is_pause:
                self._validate_changes(new_settings)
                self.clean(new_settings)
            self._handle_and_set_change_consequences(new_settings)
            changes = self.get_setting_changes(new_settings)
            if changes:
                self._save_and_propagate(request, new_settings, system_user)
                # autopilot reloads settings so changes have to be saved when it is called
                if not skip_automation:
                    self._handle_budget_autopilot(changes)

    def _update_ad_group(self, request, updates):
        if "ad_group_name" in updates:
            self.ad_group.name = updates["ad_group_name"]
        self.ad_group.save(request)

    def _filter_and_remap_input(self, request, updates, skip_permission_check):
        updates = self._remove_unsupported_fields(updates)
        updates = self._remap_fields_for_compatibility(updates)
        updates = self._remove_disallowed_fields(request, updates, skip_permission_check)
        return updates

    def _remove_unsupported_fields(self, updates):
        ad_group_sources = self.ad_group.adgroupsource_set.all().select_related("source", "settings")
        if not retargeting_helper.supports_retargeting(ad_group_sources):
            updates.pop("retargeting_ad_groups", None)
            updates.pop("exclusion_retargeting_ad_groups", None)
            updates.pop("audience_targeting", None)
            updates.pop("exclusion_audience_targeting", None)
        return updates

    @staticmethod
    def _remap_fields_for_compatibility(updates):
        if "name" in updates:
            updates["ad_group_name"] = updates["name"]
        return updates

    def _remove_disallowed_fields(self, request, updates, skip_permission_check):
        user = request.user if request else None

        new_updates = {}

        for field, value in list(updates.items()):
            required_permission = not skip_permission_check and self._permissioned_fields.get(field)
            if required_permission and not (user and user.has_perm(required_permission)):
                continue
            if field in set(self._settings_fields):
                new_updates[field] = value

        return new_updates

    @staticmethod
    def _apply_updates(new_settings, updates):
        for key, value in updates.items():
            setattr(new_settings, key, value)

    def _validate_changes(self, new_settings):
        if "archived" in new_settings.get_updates():
            if new_settings.archived:
                if not self.ad_group.can_archive():
                    raise exc.ForbiddenError("An ad group has to be paused for 3 days in order to archive it.")
            else:
                if not self.ad_group.can_restore():
                    raise exc.ForbiddenError(
                        "Account and campaign must not be archived in order to restore an ad group."
                    )

    def _handle_and_set_change_consequences(self, new_settings):
        self._handle_b1_sources_group_adjustments(new_settings)
        self._handle_cpc_autopilot_initial_cpcs(new_settings)
        self._handle_cpc_constraints(new_settings)

    def _handle_b1_sources_group_adjustments(self, new_settings):
        import dash.views.helpers

        changes = self.get_setting_changes(new_settings)
        # Turning on RTB-as-one
        if "b1_sources_group_enabled" in changes and changes["b1_sources_group_enabled"]:
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

            if "b1_sources_group_cpc_cc" not in changes:
                new_settings.b1_sources_group_cpc_cc = core.models.AllRTBSource.default_cpc_cc

            if "b1_sources_group_daily_budget" not in changes:
                new_settings.b1_sources_group_daily_budget = core.models.AllRTBSource.default_daily_budget_cc

        # Changing adgroup max cpc
        if changes.get("cpc_cc") and new_settings.b1_sources_group_enabled:
            new_settings.b1_sources_group_cpc_cc = min(changes.get("cpc_cc"), new_settings.b1_sources_group_cpc_cc)

        adjusted_b1_sources_group_cpc_cc = dash.views.helpers.adjust_max_cpc(
            new_settings.b1_sources_group_cpc_cc, new_settings
        )
        if new_settings.b1_sources_group_cpc_cc != adjusted_b1_sources_group_cpc_cc:
            new_settings.b1_sources_group_cpc_cc = adjusted_b1_sources_group_cpc_cc

    def _handle_cpc_autopilot_initial_cpcs(self, new_settings):
        import dash.views.helpers

        if not self._should_set_cpc_autopilot_initial_cpcs(new_settings):
            return

        all_b1_sources = self.ad_group.adgroupsource_set.filter(source__source_type__type=constants.SourceType.B1)
        active_b1_sources = all_b1_sources.filter_active()
        active_b1_sources_settings = core.models.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=active_b1_sources
        ).group_current_settings()

        if active_b1_sources.count() < 1:
            return

        avg_cpc_cc = sum(agss.cpc_cc for agss in active_b1_sources_settings) / len(active_b1_sources_settings)

        new_settings.b1_sources_group_cpc_cc = avg_cpc_cc
        new_ad_group_sources_cpcs = {ad_group_source: avg_cpc_cc for ad_group_source in all_b1_sources}
        dash.views.helpers.set_ad_group_sources_cpcs(new_ad_group_sources_cpcs, self.ad_group, new_settings)

    def _should_set_cpc_autopilot_initial_cpcs(self, new_settings):
        return (
            self.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            and new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
            and new_settings.b1_sources_group_enabled
        )

    def _handle_cpc_constraints(self, new_settings):
        import dash.views.helpers

        ad_group_sources_cpcs = dash.views.helpers.get_adjusted_ad_group_sources_cpcs(self.ad_group, new_settings)
        if self.b1_sources_group_cpc_cc != new_settings.b1_sources_group_cpc_cc:
            bcm_modifiers = self.ad_group.campaign.get_bcm_modifiers()
            try:
                dash.views.helpers.validate_ad_group_sources_cpc_constraints(
                    bcm_modifiers, ad_group_sources_cpcs, self.ad_group
                )
            except dash.cpc_constraints.ValidationError as err:
                raise exc.ValidationError(errors={"b1_sources_group_cpc_cc": list(set(err))})
        dash.views.helpers.set_ad_group_sources_cpcs(
            ad_group_sources_cpcs, self.ad_group, new_settings, skip_validation=True
        )

    def _should_recalculate_budget_autopilot(self, changes):
        ap_ad_group_budget_fields = ["autopilot_daily_budget", "autopilot_state", "b1_sources_group_state"]
        ap_campaign_budget_fields = ["b1_sources_group_state", "state", "start_date", "end_date"]
        return (
            self.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            and any(field in changes for field in ap_ad_group_budget_fields)
        ) or (
            self.ad_group.campaign.settings.autopilot and any(field in changes for field in ap_campaign_budget_fields)
        )

    def _should_send_autopilot_mail(self, changes):
        if self.ad_group.campaign.settings.autopilot:
            return False
        ap_send_mail_fields = ["autopilot_daily_budget", "autopilot_state", "state"]
        return any(field in changes for field in ap_send_mail_fields)

    def _handle_budget_autopilot(self, changes):
        if not self._should_recalculate_budget_autopilot(changes):
            return

        from automation import autopilot

        autopilot.recalculate_budgets_ad_group(self.ad_group, send_mail=self._should_send_autopilot_mail(changes))

    def _save_and_propagate(self, request, new_settings, system_user):
        changes = self.get_setting_changes(new_settings)
        new_settings.save(request, system_user=system_user)

        core.signals.settings_change.send_robust(
            sender=self.__class__, request=request, instance=new_settings, changes=changes
        )

        if "tracking_code" in changes or "click_capping_daily_ad_group_max_clicks" in changes:
            redirector_helper.insert_adgroup(self.ad_group)
        k1_helper.update_ad_group(self.ad_group.pk, msg="AdGroupSettings.put")

        self._send_notification_email(request, new_settings)

    def _send_notification_email(self, request, new_settings):
        if not request:
            return
        user = request.user if request else None
        changes_text = self.get_changes_text(self, new_settings, user, separator="\n")
        email_helper.send_ad_group_notification_email(self.ad_group, request, changes_text)

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)
        self.ad_group.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user,
        )

    def get_external_max_cpm(self, account, license_fee, margin):
        if self.max_cpm is None:
            return self.max_cpm

        max_cpm = self.max_cpm
        if account.uses_bcm_v2:
            max_cpm = core.features.bcm.calculations.subtract_fee_and_margin(max_cpm, license_fee, margin)
        return max_cpm

    def get_external_b1_sources_group_daily_budget(self, account, license_fee, margin):
        b1_sources_group_daily_budget = self.b1_sources_group_daily_budget
        if account.uses_bcm_v2:
            b1_sources_group_daily_budget = core.features.bcm.calculations.subtract_fee_and_margin(
                b1_sources_group_daily_budget, license_fee, margin
            )
        return b1_sources_group_daily_budget

    def get_external_b1_sources_group_cpc_cc(self, account, license_fee, margin):
        b1_sources_group_cpc_cc = self.b1_sources_group_cpc_cc
        if account.uses_bcm_v2:
            b1_sources_group_cpc_cc = core.features.bcm.calculations.subtract_fee_and_margin(
                b1_sources_group_cpc_cc, license_fee, margin
            )
        return b1_sources_group_cpc_cc

    def get_currency(self):
        return self.ad_group.campaign.account.currency