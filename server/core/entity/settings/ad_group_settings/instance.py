import influx

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


class AdGroupSettingsMixin(object):

    def save(self,
             request,
             action_type=None,
             changes_text=None,
             *args, **kwargs):
        if self.pk is None:
            if request is None:
                self.created_by = None
            else:
                self.created_by = request.user
        super(AdGroupSettingsMixin, self).save(*args, **kwargs)
        self.add_to_history(request and request.user,
                            action_type, changes_text)

    def add_to_history(self, user, action_type, history_changes_text):
        changes = self.get_model_state_changes(
            self.get_settings_dict()
        )
        changes_text = history_changes_text or self.get_changes_text_from_dict(
            changes)
        self.ad_group.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user
        )

    @transaction.atomic
    def update(self, request, **kwargs):
        import dash.views.helpers
        from automation import autopilot_plus
        ad_group = self.ad_group

        current_settings = self

        self._set_ad_group(ad_group, kwargs)

        new_settings = current_settings.copy_settings()
        latest_ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.all().\
            filter(ad_group_source__ad_group=ad_group).\
            group_current_settings().\
            select_related('ad_group_source')
        self._set_settings(
            ad_group,
            latest_ad_group_source_settings,
            new_settings,
            kwargs,
            request.user
        )

        campaign_settings = ad_group.campaign.get_current_settings()

        self.clean(request, ad_group, current_settings, new_settings, campaign_settings)

        changes = current_settings.get_setting_changes(new_settings)
        changes, current_settings, new_settings = self._b1_sources_group_adjustments(
            changes, current_settings, new_settings)

        if current_settings.bluekai_targeting != new_settings.bluekai_targeting:
            influx.incr('dash.agency.bluekai_targeting_change', 1, adgroup=str(ad_group.id))

        # save
        ad_group.save(request)
        if changes:
            if new_settings.id is None or 'tracking_code' in changes or 'click_capping_daily_ad_group_max_clicks' in changes:
                redirector_helper.insert_adgroup(
                    ad_group,
                    new_settings,
                    campaign_settings,
                )

            if self._should_set_cpc_autopilot_initial_cpcs(current_settings, new_settings):
                self._set_cpc_autopilot_initial_cpcs(request, ad_group, new_settings)

            ad_group_sources_cpcs = dash.views.helpers.get_adjusted_ad_group_sources_cpcs(ad_group, new_settings)
            if self._should_validate_cpc_constraints(changes, new_settings):
                try:
                    dash.views.helpers.validate_ad_group_sources_cpc_constraints(ad_group_sources_cpcs)
                except dash.cpc_constraints.ValidationError as err:
                    raise exc.ValidationError(errors={
                        'b1_sources_group_cpc_cc': list(set(err))
                    })
            dash.views.helpers.set_ad_group_sources_cpcs(ad_group_sources_cpcs, ad_group, new_settings)

            new_settings.save(
                request,
                action_type=constants.HistoryActionType.SETTINGS_CHANGE)
            k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSettings.put')

            if self._should_initialize_budget_autopilot(changes, new_settings):
                autopilot_plus.initialize_budget_autopilot_on_ad_group(new_settings, send_mail=True)

            changes_text = core.entity.settings.AdGroupSettings.get_changes_text(
                current_settings, new_settings, request.user, separator='\n')

            email_helper.send_ad_group_notification_email(ad_group, request, changes_text)

        # when we have a FK to latest settings, this return can be removed
        # since we no longer have to manually replace the object on the parent entity
        return new_settings

    def _set_ad_group(self, ad_group, resource):
        ad_group.name = resource['name']

    def _set_settings(self, ad_group, latest_ad_group_source_settings, settings, resource, user):
        settings.state = resource['state']
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.exclusion_target_regions = resource['exclusion_target_regions']
        settings.interest_targeting = resource['interest_targeting']
        settings.exclusion_interest_targeting = resource['exclusion_interest_targeting']
        settings.ad_group_name = resource['name']
        settings.tracking_code = resource['tracking_code']
        settings.dayparting = resource['dayparting']

        if user.has_perm('zemauth.can_set_click_capping'):
            settings.click_capping_daily_ad_group_max_clicks = resource['click_capping_daily_ad_group_max_clicks']

        if user.has_perm('zemauth.can_set_ad_group_max_cpc'):
            settings.cpc_cc = resource['cpc_cc']

        if user.has_perm('zemauth.can_set_ad_group_max_cpm'):
            settings.max_cpm = resource['max_cpm']

        if not settings.landing_mode and user.has_perm('zemauth.can_set_adgroup_to_auto_pilot'):
            settings.autopilot_state = resource['autopilot_state']
            if resource['autopilot_state'] == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
                settings.autopilot_daily_budget = resource['autopilot_daily_budget']

        if user.has_perm('zemauth.can_view_retargeting_settings') and\
                retargeting_helper.supports_retargeting(latest_ad_group_source_settings):
            settings.retargeting_ad_groups = resource['retargeting_ad_groups']

        if user.has_perm('zemauth.can_target_custom_audiences') and\
                retargeting_helper.supports_retargeting(latest_ad_group_source_settings):
            settings.exclusion_retargeting_ad_groups = resource['exclusion_retargeting_ad_groups']
            settings.audience_targeting = resource['audience_targeting']
            settings.exclusion_audience_targeting = resource['exclusion_audience_targeting']

        settings.b1_sources_group_enabled = resource['b1_sources_group_enabled']
        settings.b1_sources_group_daily_budget = resource['b1_sources_group_daily_budget']
        settings.b1_sources_group_state = resource['b1_sources_group_state']
        if user.has_perm('zemauth.can_set_rtb_sources_as_one_cpc') and settings.b1_sources_group_enabled:
            settings.b1_sources_group_cpc_cc = resource['b1_sources_group_cpc_cc']

        settings.bluekai_targeting = resource['bluekai_targeting']

        if user.has_perm('zemauth.can_set_white_blacklist_publisher_groups'):
            settings.whitelist_publisher_groups = resource['whitelist_publisher_groups']
            settings.blacklist_publisher_groups = resource['blacklist_publisher_groups']

        if user.has_perm('zemauth.can_set_advanced_device_targeting'):
            settings.target_os = resource['target_os']
            settings.target_placements = resource['target_placements']

        if user.has_perm('zemauth.can_set_delivery_type'):
            settings.delivery_type = resource['delivery_type']

    @staticmethod
    def _b1_sources_group_adjustments(changes, current_settings, new_settings):
        import dash.views.helpers
        # Turning on RTB-as-one
        if 'b1_sources_group_enabled' in changes and changes['b1_sources_group_enabled']:
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

            new_b1_sources_group_cpc = constants.SourceAllRTB.DEFAULT_CPC_CC
            if changes.get('b1_sources_group_cpc_cc'):
                new_b1_sources_group_cpc = changes['b1_sources_group_cpc_cc']
            new_settings.b1_sources_group_cpc_cc = new_b1_sources_group_cpc

            if changes.get('b1_sources_group_daily_budget'):
                new_settings.b1_sources_group_daily_budget = changes.get('b1_sources_group_daily_budget')
            else:
                new_settings.b1_sources_group_daily_budget = constants.SourceAllRTB.DEFAULT_DAILY_BUDGET

        # Changing adgroup max cpc
        if changes.get('cpc_cc') and new_settings.b1_sources_group_enabled:
            new_settings.b1_sources_group_cpc_cc = min(changes.get('cpc_cc'), new_settings.b1_sources_group_cpc_cc)

        new_settings.b1_sources_group_cpc_cc = dash.views.helpers.adjust_max_cpc(
            new_settings.b1_sources_group_cpc_cc,
            new_settings
        )
        return current_settings.get_setting_changes(new_settings), current_settings, new_settings

    def _set_cpc_autopilot_initial_cpcs(self, request, ad_group, new_ad_group_settings):
        import dash.views.helpers
        all_b1_sources = ad_group.adgroupsource_set.filter(
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

        new_ad_group_settings.b1_sources_group_cpc_cc = avg_cpc_cc
        new_ad_group_sources_cpcs = {ad_group_source: avg_cpc_cc for ad_group_source in all_b1_sources}
        dash.views.helpers.set_ad_group_sources_cpcs(new_ad_group_sources_cpcs, ad_group, new_ad_group_settings)

    def _should_initialize_budget_autopilot(self, changes, new_settings):
        if new_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            return False

        ap_budget_fields = ['autopilot_daily_budget', 'autopilot_state', 'b1_sources_group_state']
        if not any(field in changes for field in ap_budget_fields):
            return False

        return True

    def _should_set_cpc_autopilot_initial_cpcs(self, current_settings, new_settings):
        return current_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
            new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC and\
            new_settings.b1_sources_group_enabled

    def _should_validate_cpc_constraints(self, changes, new_settings):
        return 'b1_sources_group_cpc_cc' in changes
