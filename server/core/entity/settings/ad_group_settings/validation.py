import decimal
from dash import constants
from utils import exc

import dash.features.bluekai


# should inherit from core.common.BaseValidator so that full_clean is called on save,
# but until the refactoring is completed let's call clean() manually
class AdGroupSettingsValidatorMixin(object):

    @classmethod
    def clean(cls, request, ad_group, current_settings, new_settings, campaign_settings):
        cls._validate_state_change(ad_group, current_settings, new_settings, campaign_settings)
        cls._validate_autopilot_settings(request, ad_group, current_settings, new_settings)
        cls._validate_all_rtb_state(request, current_settings, new_settings)
        cls._validate_yahoo_desktop_targeting(ad_group, current_settings, new_settings)
        cls._validate_all_rtb_campaign_stop(ad_group, current_settings, new_settings, campaign_settings)
        cls._validate_autopilot_campaign_stop(ad_group, current_settings, new_settings, campaign_settings)
        cls._validate_bluekai_targeting_change(current_settings, new_settings)

    @staticmethod
    def _validate_autopilot_settings(request, ad_group, settings, new_settings):
        from automation import autopilot
        if new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            if not new_settings.b1_sources_group_enabled:
                msg = 'To enable Daily Cap Autopilot, RTB Sources have to be managed as a group.'
                raise exc.ValidationError(errors={
                    'autopilot_state': msg
                })

            if settings.b1_sources_group_daily_budget != new_settings.b1_sources_group_daily_budget:
                msg = 'Autopilot has to be disabled in order to manage Daily Cap of RTB Sources'
                raise exc.ValidationError(errors={
                    'b1_sources_group_daily_budget': msg,
                })

        if new_settings.autopilot_state in (
                constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
                constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        ):
            if settings.b1_sources_group_cpc_cc != new_settings.b1_sources_group_cpc_cc:
                msg = 'Autopilot has to be disabled in order to manage Daily Cap of RTB Sources'
                raise exc.ValidationError(errors={
                    'b1_sources_group_daily_budget': msg,
                })

        min_autopilot_daily_budget = autopilot.get_adgroup_minimum_daily_budget(
            ad_group, new_settings
        )
        if new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
           new_settings.autopilot_daily_budget < min_autopilot_daily_budget:
            msg = 'Total Daily Spend Cap must be at least ${min_budget}. Autopilot '\
                  'requires ${min_per_source} or more per active media source.'
            raise exc.ValidationError(errors={
                'autopilot_daily_budget': msg.format(
                    min_budget=min_autopilot_daily_budget,
                    min_per_source=autopilot.settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC,
                )
            })

    @staticmethod
    def _validate_autopilot_campaign_stop(ad_group, current_settings, new_settings, campaign_settings):
        from automation import campaign_stop
        if new_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            return

        if current_settings.autopilot_daily_budget >= new_settings.autopilot_daily_budget:
            return

        max_settable = campaign_stop.get_max_settable_autopilot_budget(
            ad_group,
            ad_group.campaign,
            new_settings,
            campaign_settings,
        )
        if max_settable is not None and new_settings.autopilot_daily_budget > max_settable:
            msg = 'Total Daily Spend Cap is too high. Maximum daily spend can be up to ${}'.format(max_settable)
            raise exc.ValidationError(errors={
                'autopilot_daily_budget': msg
            })

    @staticmethod
    def _validate_all_rtb_state(request, settings, new_settings):
        # MVP for all-RTB-sources-as-one
        # Ensure that AdGroup is paused when enabling/disabling All RTB functionality
        # For now this is the easiest solution to avoid conflicts with ad group budgets and state validations
        if new_settings.state == constants.AdGroupSettingsState.INACTIVE:
            return

        if settings.b1_sources_group_enabled != new_settings.b1_sources_group_enabled:
            msg = 'To manage Daily Spend Cap for All RTB as one, ad group must be paused first.'
            if not new_settings.b1_sources_group_enabled:
                'To disable managing Daily Spend Cap for All RTB as one, ad group must be paused first.'
            raise exc.ValidationError(errors={'b1_sources_group_enabled': [msg]})

    @staticmethod
    def _validate_all_rtb_campaign_stop(ad_group, current_settings, new_settings, campaign_settings):
        from automation import campaign_stop
        changes = current_settings.get_setting_changes(new_settings)
        if 'b1_sources_group_daily_budget' in changes:
            new_daily_budget = decimal.Decimal(changes['b1_sources_group_daily_budget'])
            max_daily_budget = campaign_stop.get_max_settable_b1_sources_group_budget(
                ad_group,
                ad_group.campaign,
                new_settings,
                campaign_settings,
            )
            if max_daily_budget is not None and new_daily_budget > max_daily_budget:
                raise exc.ValidationError(errors={
                    'daily_budget_cc': [
                        'Daily Spend Cap is too high. Maximum daily spend '
                        'cap can be up to ${max_daily_budget}.'.format(
                            max_daily_budget=max_daily_budget
                        )
                    ]
                })

        if 'b1_sources_group_state' in changes:
            can_enable_b1_sources_group = campaign_stop.can_enable_b1_sources_group(
                ad_group,
                ad_group.campaign,
                new_settings,
                campaign_settings,
            )
            if not can_enable_b1_sources_group:
                raise exc.ValidationError(errors={
                    'state': ['Please add additional budget to your campaign to make changes.']
                })

    @staticmethod
    def _validate_state_change(ad_group, current_settings, new_settings, campaign_settings):
        import dash.views.helpers
        if current_settings.state == new_settings.state:
            return

        dash.views.helpers.validate_ad_groups_state(
            [ad_group],
            ad_group.campaign,
            campaign_settings,
            new_settings.state,
        )

    @classmethod
    def _validate_bluekai_tageting(cls, bluekai_targeting):
        if isinstance(bluekai_targeting, list):
            for subexp in bluekai_targeting[1:]:
                cls._validate_bluekai_tageting(subexp)
        else:
            typ, id_ = bluekai_targeting.split(':', 1)
            if typ == 'bluekai' and not dash.features.bluekai.models.\
               BlueKaiCategory.objects.active().filter(category_id=id_):
                raise exc.ValidationError(
                    'Invalid BlueKai category id: "{}"'.format(id_)
                )

    @classmethod
    def _validate_bluekai_targeting_change(cls, current_settings, new_settings):
        if current_settings.bluekai_targeting == new_settings.bluekai_targeting:
            return

        cls._validate_bluekai_tageting(new_settings.bluekai_targeting)

    @staticmethod
    def _validate_yahoo_desktop_targeting(ad_group, settings, new_settings):
        # optimization: only check when targeting is changed to desktop only
        if not (settings.target_devices != new_settings.target_devices and
                new_settings.target_devices == [constants.AdTargetDevice.DESKTOP]):
            return

        for ags in ad_group.adgroupsource_set.all():
            if ags.source.source_type.type != constants.SourceType.YAHOO:
                continue
            curr_ags_settings = ags.get_current_settings()
            if curr_ags_settings.state != constants.AdGroupSettingsState.ACTIVE:
                continue
            min_cpc = ags.source.source_type.get_min_cpc(new_settings)
            if min_cpc and curr_ags_settings.cpc_cc < min_cpc:
                msg = 'CPC on Yahoo is too low for desktop-only targeting. Please set it to at least $0.25.'
                raise exc.ValidationError(errors={'target_devices': [msg]})
