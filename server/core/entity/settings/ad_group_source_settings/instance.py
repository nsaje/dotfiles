from django.db import transaction

import dash.constants
import core.bcm
import utils.k1_helper


class AdGroupSourceSettingsMixin(object):

    @transaction.atomic
    def update(self, request=None, k1_sync=True, system_user=None,
               skip_automation=False, skip_validation=False, skip_notification=False,
               **updates):
        result = {
            'autopilot_changed_sources_text': '',
        }

        if not updates:
            return result

        new_settings = self.copy_settings()
        for key, value in updates.items():
            setattr(new_settings, key, value)

        changes = self.get_setting_changes(new_settings)
        if not changes:
            return result

        # TODO (multicurrency): Handle multiple currencies in clean method correctly
        if not skip_validation:
            self.clean(new_settings)

        # TODO (multicurrency): Handle multiple currencies in validate_ad_group_source_campaign_stop method correctly
        if not skip_automation:
            self.validate_ad_group_source_campaign_stop(new_settings)

        old_settings = self.get_settings_dict()
        changes = self.get_setting_changes(new_settings)
        new_settings.save(request, system_user=system_user, update_fields=list(changes.keys()))

        if not skip_automation:
            # autopilot reloads settings so changes have to be saved when it is called
            autopilot_changed_sources = self._handle_budget_autopilot(changes)
            result['autopilot_changed_sources_text'] = ', '.join(autopilot_changed_sources)

        if k1_sync:
            utils.k1_helper.update_ad_group(self.ad_group_source.ad_group.pk, 'AdGroupSource.update')

        if not skip_notification:
            self._notify_ad_group_source_settings_changed(request, changes, old_settings, new_settings)

        return result

    def _handle_budget_autopilot(self, changes):
        ad_group_settings = self.ad_group_source.ad_group.settings
        if ('state' in changes and (
                ad_group_settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET or
                self.ad_group_source.ad_group.campaign.settings.autopilot)):
            from automation import autopilot
            changed_sources = autopilot.recalculate_budgets_ad_group(self.ad_group_source.ad_group, send_mail=False)
            return [s.source.name for s in changed_sources]
        return []

    def _notify_ad_group_source_settings_changed(self, request, changes, old_settings, new_settings):
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
                text = '%s %s set to %s' % (source_name, field, val)
            else:
                old_val = self.get_human_value(key, old_val)
                text = '%s %s set from %s to %s' % (source_name, field, old_val, val)
            changes_text_parts.append(text)

        utils.email_helper.send_ad_group_notification_email(
            self.ad_group_source.ad_group, request, '\n'.join(changes_text_parts))

    def add_to_history(self, user, action_type, changes):
        _, changes_text = self.construct_changes(
            'Created settings.',
            'Source: {}.'.format(self.ad_group_source.source.name),
            changes
        )
        self.ad_group_source.ad_group.write_history(
            changes_text,
            changes=changes,
            user=user,
            action_type=action_type,
            system_user=self.system_user,
        )

    def get_external_daily_budget_cc(self, account, license_fee, margin):
        daily_budget_cc = self.daily_budget_cc
        if account.uses_bcm_v2:
            daily_budget_cc = core.bcm.calculations.subtract_fee_and_margin(
                daily_budget_cc,
                license_fee,
                margin,
            )
        return daily_budget_cc

    def get_external_cpc_cc(self, account, license_fee, margin):
        cpc_cc = self.cpc_cc
        if account.uses_bcm_v2:
            cpc_cc = core.bcm.calculations.subtract_fee_and_margin(
                cpc_cc,
                license_fee,
                margin,
            )
        return cpc_cc

    def get_currency(self):
        return self.ad_group_source.ad_group.campaign.account.currency
