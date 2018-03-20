from django.db import transaction

from dash import constants
from dash import retargeting_helper
from utils import email_helper
from utils import k1_helper
from utils import redirector_helper
from utils import exc

import core.audiences
import core.common
import core.entity
import core.history
import core.source
import core.signals


class AdGroupSettingsMixin(object):

    @transaction.atomic
    def update(self, request, skip_validation=False, system_user=None, **updates):
        self._update_ad_group(request, updates)
        updates = self._filter_and_remap_input(request, updates)
        if updates:
            new_settings = self.copy_settings()
            self._apply_updates(new_settings, updates)
            if not skip_validation:
                self.clean(new_settings)
            self._handle_and_set_change_consequences(new_settings)
            changes = self.get_setting_changes(new_settings)
            self._save_and_propagate(request, new_settings, system_user)
            # autopilot reloads settings so changes have to be saved when it is called
            self._handle_initialize_budget_autopilot(changes)

    def _update_ad_group(self, request, updates):
        if 'name' in updates:
            self.ad_group.name = updates['name']
        self.ad_group.save(request)

    def _filter_and_remap_input(self, request, updates):
        updates = self._remove_unsupported_fields(updates)
        updates = self._remap_fields_for_compatibility(updates)
        updates = self._remove_disallowed_fields(request, updates)
        return updates

    def _remove_unsupported_fields(self, updates):
        ad_group_sources = self.ad_group.adgroupsource_set.all().select_related('source', 'settings')
        if not retargeting_helper.supports_retargeting(ad_group_sources):
            updates.pop('retargeting_ad_groups', None)
            updates.pop('exclusion_retargeting_ad_groups', None)
            updates.pop('audience_targeting', None)
            updates.pop('exclusion_audience_targeting', None)
        return updates

    @staticmethod
    def _remap_fields_for_compatibility(updates):
        if 'name' in updates:
            updates['ad_group_name'] = updates['name']
        return updates

    def _remove_disallowed_fields(self, request, updates):
        user = request.user if request else None
        special_case_fields = {'autopilot_state'}
        valid_fields = set(self._settings_fields) - special_case_fields

        new_updates = {}

        for field, value in list(updates.items()):
            required_permission = self._permissioned_fields.get(field)
            if required_permission and not user.has_perm(required_permission):
                continue
            if field in valid_fields:
                new_updates[field] = value

        if 'autopilot_state' in updates and not self.landing_mode:
            new_updates['autopilot_state'] = updates['autopilot_state']

        return new_updates

    @staticmethod
    def _apply_updates(new_settings, updates):
        for key, value in updates.items():
            setattr(new_settings, key, value)

    def _handle_and_set_change_consequences(self, new_settings):
        self._handle_b1_sources_group_adjustments(new_settings)
        self._handle_cpc_autopilot_initial_cpcs(new_settings)
        self._handle_cpc_constraints(new_settings)

    def _handle_b1_sources_group_adjustments(self, new_settings):
        import dash.views.helpers
        changes = self.get_setting_changes(new_settings)
        # Turning on RTB-as-one
        if 'b1_sources_group_enabled' in changes and changes['b1_sources_group_enabled']:
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

            if 'b1_sources_group_cpc_cc' not in changes:
                new_settings.b1_sources_group_cpc_cc = core.source.AllRTBSource.default_cpc_cc

            if 'b1_sources_group_daily_budget' not in changes:
                new_settings.b1_sources_group_daily_budget = core.source.AllRTBSource.default_daily_budget_cc

        # Changing adgroup max cpc
        if 'cpc_cc' in changes and new_settings.b1_sources_group_enabled:
            new_settings.b1_sources_group_cpc_cc = min(changes.get('cpc_cc'), new_settings.b1_sources_group_cpc_cc)

        new_settings.b1_sources_group_cpc_cc = dash.views.helpers.adjust_max_cpc(
            new_settings.b1_sources_group_cpc_cc,
            new_settings
        )

    def _handle_cpc_autopilot_initial_cpcs(self, new_settings):
        import dash.views.helpers

        if not self._should_set_cpc_autopilot_initial_cpcs(new_settings):
            return

        all_b1_sources = self.ad_group.adgroupsource_set.filter(
            source__source_type__type=constants.SourceType.B1
        )
        active_b1_sources = all_b1_sources.filter_active()
        active_b1_sources_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=active_b1_sources
        ).group_current_settings()

        if active_b1_sources.count() < 1:
            return

        avg_cpc_cc = (
            sum(agss.cpc_cc for agss in active_b1_sources_settings) /
            len(active_b1_sources_settings)
        )

        new_settings.b1_sources_group_cpc_cc = avg_cpc_cc
        new_ad_group_sources_cpcs = {ad_group_source: avg_cpc_cc for ad_group_source in all_b1_sources}
        dash.views.helpers.set_ad_group_sources_cpcs(new_ad_group_sources_cpcs, self.ad_group, new_settings)

    def _should_set_cpc_autopilot_initial_cpcs(self, new_settings):
        return self.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
            new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC and\
            new_settings.b1_sources_group_enabled

    def _handle_cpc_constraints(self, new_settings):
        import dash.views.helpers
        ad_group_sources_cpcs = dash.views.helpers.get_adjusted_ad_group_sources_cpcs(self.ad_group, new_settings)
        if self.b1_sources_group_cpc_cc != new_settings.b1_sources_group_cpc_cc:
            bcm_modifiers = self.ad_group.campaign.get_bcm_modifiers()
            try:
                dash.views.helpers.validate_ad_group_sources_cpc_constraints(
                    bcm_modifiers, ad_group_sources_cpcs, self.ad_group)
            except dash.cpc_constraints.ValidationError as err:
                raise exc.ValidationError(errors={
                    'b1_sources_group_cpc_cc': list(set(err))
                })
        dash.views.helpers.set_ad_group_sources_cpcs(
            ad_group_sources_cpcs, self.ad_group, new_settings, skip_validation=True)

    def _handle_initialize_budget_autopilot(self, changes):
        if self.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            return

        ap_budget_fields = ['autopilot_daily_budget', 'autopilot_state', 'b1_sources_group_state']
        if not any(field in changes for field in ap_budget_fields):
            return

        from automation import autopilot
        autopilot.initialize_budget_autopilot_on_ad_group(self, send_mail=True)

    def _save_and_propagate(self, request, new_settings, system_user):
        changes = self.get_setting_changes(new_settings)
        new_settings.save(request, update_fields=list(changes.keys()), system_user=system_user)

        core.signals.settings_change.send_robust(
            sender=self.__class__, request=request, instance=new_settings,
            changes=changes)

        if 'tracking_code' in changes or 'click_capping_daily_ad_group_max_clicks' in changes:
            redirector_helper.insert_adgroup(self.ad_group)
        k1_helper.update_ad_group(self.ad_group.pk, msg='AdGroupSettings.put')

        self._send_notification_email(request, new_settings)

    def _send_notification_email(self, request, new_settings):
        if not request:
            return
        user = request.user if request else None
        changes_text = self.get_changes_text(self, new_settings, user, separator='\n')
        email_helper.send_ad_group_notification_email(self.ad_group, request, changes_text)

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)
        self.ad_group.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user
        )

    def get_external_max_cpm(self, account, license_fee, margin):
        if self.max_cpm is None:
            return self.max_cpm

        max_cpm = self.max_cpm
        if account.uses_bcm_v2:
            max_cpm = core.bcm.calculations.subtract_fee_and_margin(
                max_cpm,
                license_fee,
                margin,
            )
        return max_cpm

    def get_external_b1_sources_group_daily_budget(self, account, license_fee, margin):
        b1_sources_group_daily_budget = self.b1_sources_group_daily_budget
        if account.uses_bcm_v2:
            b1_sources_group_daily_budget = core.bcm.calculations.subtract_fee_and_margin(
                b1_sources_group_daily_budget,
                license_fee,
                margin,
            )
        return b1_sources_group_daily_budget

    def get_external_b1_sources_group_cpc_cc(self, account, license_fee, margin):
        b1_sources_group_cpc_cc = self.b1_sources_group_cpc_cc
        if account.uses_bcm_v2:
            b1_sources_group_cpc_cc = core.bcm.calculations.subtract_fee_and_margin(
                b1_sources_group_cpc_cc,
                license_fee,
                margin,
            )
        return b1_sources_group_cpc_cc

    def get_currency(self):
        return self.ad_group.campaign.account.currency
