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

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)
        self.ad_group.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user
        )

    @transaction.atomic
    def update(self, request, skip_validation=False, **kwargs):
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
        kwargs = self._remove_unsupported_fields(kwargs, latest_ad_group_source_settings)
        kwargs = self._remap_fields_for_compatibility(kwargs)
        self._set_settings(
            request,
            new_settings,
            kwargs
        )

        campaign_settings = ad_group.campaign.get_current_settings()

        if not skip_validation:
            self.clean(request, ad_group, current_settings, new_settings, campaign_settings)

        changes = current_settings.get_setting_changes(new_settings)
        changes, current_settings, new_settings = self._b1_sources_group_adjustments(
            changes, current_settings, new_settings)

        if current_settings.bluekai_targeting != new_settings.bluekai_targeting:
            influx.incr('dash.agency.bluekai_targeting_change', 1, adgroup=str(ad_group.id))

        # save
        ad_group.save(request)
        if self.pk is None or changes:
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
                bcm_modifiers = self.ad_group.campaign.get_bcm_modifiers()
                try:
                    dash.views.helpers.validate_ad_group_sources_cpc_constraints(
                        bcm_modifiers, ad_group_sources_cpcs)
                except dash.cpc_constraints.ValidationError as err:
                    raise exc.ValidationError(errors={
                        'b1_sources_group_cpc_cc': list(set(err))
                    })
            dash.views.helpers.set_ad_group_sources_cpcs(
                ad_group_sources_cpcs, ad_group, new_settings, skip_validation=skip_validation)

            changes_text = core.entity.settings.AdGroupSettings.get_changes_text(
                current_settings, new_settings, request.user if request else None, separator='\n')

            if new_settings.pk is None:
                new_settings.save(request)
            else:
                new_settings.save(request, update_fields=changes.keys())
            k1_helper.update_ad_group(ad_group.pk, msg='AdGroupSettings.put')

            if self._should_initialize_budget_autopilot(changes, new_settings):
                autopilot_plus.initialize_budget_autopilot_on_ad_group(new_settings, send_mail=True)

            if request is not None:
                email_helper.send_ad_group_notification_email(ad_group, request, changes_text)

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

    @staticmethod
    def _set_ad_group(ad_group, resource):
        if 'name' in resource:
            ad_group.name = resource['name']

    @staticmethod
    def _remove_unsupported_fields(kwargs, latest_ad_group_source_settings):
        if not retargeting_helper.supports_retargeting(latest_ad_group_source_settings):
            kwargs.pop('retargeting_ad_groups', None)
            kwargs.pop('exclusion_retargeting_ad_groups', None)
            kwargs.pop('audience_targeting', None)
            kwargs.pop('exclusion_audience_targeting', None)
        return kwargs

    @staticmethod
    def _remap_fields_for_compatibility(kwargs):
        if 'name' in kwargs:
            kwargs['ad_group_name'] = kwargs['name']
        return kwargs

    @classmethod
    def _set_settings(cls, request, new_settings, kwargs):
        user = request.user if request else None
        special_case_fields = {'autopilot_state', 'autopilot_daily_budget'}
        valid_fields = set(cls._settings_fields) - special_case_fields

        for field, value in kwargs.items():
            required_permission = cls._permissioned_fields.get(field)
            if required_permission and not user.has_perm(required_permission):
                continue
            if field in valid_fields:
                setattr(new_settings, field, value)

        if 'autopilot_state' in kwargs and not new_settings.landing_mode:
            new_settings.autopilot_state = kwargs['autopilot_state']
        if 'autopilot_daily_budget' in kwargs:
            new_settings.autopilot_daily_budget = kwargs['autopilot_daily_budget']

        if 'b1_sources_group_cpc_cc' in kwargs and new_settings.b1_sources_group_enabled:
            new_settings.b1_sources_group_cpc_cc = kwargs['b1_sources_group_cpc_cc']

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

    @staticmethod
    def _set_cpc_autopilot_initial_cpcs(request, ad_group, new_ad_group_settings):
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

    @staticmethod
    def _should_initialize_budget_autopilot(changes, new_settings):
        if new_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            return False

        ap_budget_fields = ['autopilot_daily_budget', 'autopilot_state', 'b1_sources_group_state']
        if not any(field in changes for field in ap_budget_fields):
            return False

        return True

    @staticmethod
    def _should_set_cpc_autopilot_initial_cpcs(current_settings, new_settings):
        return current_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
            new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC and\
            new_settings.b1_sources_group_enabled

    @staticmethod
    def _should_validate_cpc_constraints(changes, new_settings):
        return 'b1_sources_group_cpc_cc' in changes
