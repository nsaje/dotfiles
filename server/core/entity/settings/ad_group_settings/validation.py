import re
import decimal
import rfc3987
from dash import constants
from . import exceptions

import core.multicurrency
import dash.features.bluekai

import utils.validation_helper
import utils.dates_helper

import utils.exc


# should inherit from core.common.BaseValidator so that full_clean is called on save,
# but until the refactoring is completed let's call clean() manually
class AdGroupSettingsValidatorMixin(object):

    def clean(self, new_settings):
        utils.validation_helper.validate_multiple(
            self.get_setting_changes(new_settings),
            self._validate_cpc_cc,
            self._validate_max_cpm,
            self._validate_end_date,
            self._validate_tracking_code,
        )
        self._validate_state_change(new_settings)
        self._validate_autopilot_settings(new_settings)
        self._validate_all_rtb_state(new_settings)
        self._validate_yahoo_desktop_targeting(new_settings)
        self._validate_bluekai_targeting_change(new_settings)

    def _get_currency_symbol(self):
        currency = self.ad_group.campaign.account.currency
        return core.multicurrency.get_currency_symbol(currency)

    def _get_exchange_rate(self):
        today = utils.dates_helper.local_today()
        currency = self.ad_group.campaign.account.currency
        return core.multicurrency.get_exchange_rate(today, currency)

    def _validate_cpc_cc(self, changes):
        cpc_cc = changes.get('local_cpc_cc', None)
        if cpc_cc is not None:
            currency_symbol = self._get_currency_symbol()
            min_cpc_cc = decimal.Decimal('0.05') * self._get_exchange_rate()
            max_cpc_cc = decimal.Decimal('10') * self._get_exchange_rate()

            if cpc_cc < min_cpc_cc:
                raise exceptions.MaxCPCTooLow(
                    'Maximum CPC can\'t be lower than {}{:.2f}.'.format(currency_symbol, min_cpc_cc)
                )
            elif cpc_cc > max_cpc_cc:
                raise exceptions.MaxCPCTooHigh(
                    'Maximum CPC can\'t be higher than {}{:.2f}.'.format(currency_symbol, max_cpc_cc)
                )

    def _validate_max_cpm(self, changes):
        max_cpm = changes.get('local_max_cpm')
        if max_cpm is not None:
            currency_symbol = self._get_currency_symbol()
            min_max_cpm = decimal.Decimal('0.05') * self._get_exchange_rate()
            max_max_cpm = decimal.Decimal('10') * self._get_exchange_rate()

            if max_cpm < min_max_cpm:
                raise exceptions.MaxCPMTooLow(
                    'Maximum CPM can\'t be lower than {}{:.2f}.'.format(currency_symbol, min_max_cpm)
                )
            elif max_cpm > max_max_cpm:
                raise exceptions.MaxCPMTooHigh(
                    'Maximum CPM can\'t be higher than {}{:.2f}.'.format(currency_symbol, max_max_cpm)
                )

    def _validate_end_date(self, changes):
        end_date = changes.get('end_date')
        if end_date:
            start_date = changes.get('start_date', self.start_date)
            state = changes.get('state', self.state)

            if start_date and end_date < start_date:
                raise exceptions.EndDateBeforeStartDate(
                    'End date must not occur before start date.'
                )
            if end_date < utils.dates_helper.local_today() and state == constants.AdGroupSettingsState.ACTIVE:
                raise exceptions.EndDateInThePast(
                    'End date cannot be set in the past.'
                )

            if self.landing_mode:  # legacy; no custom exception
                raise exceptions.ValidationError(
                    'End date cannot be set when campaign is in landing mode.'
                )

    def _validate_tracking_code(self, changes):
        tracking_code = changes.get('tracking_code')
        if tracking_code:
            # This is a bit of a hack we're doing here but if we don't prepend 'http:' to
            # the provided tracking code, then rfc3987 doesn't know how to parse it.
            if not tracking_code.startswith('?'):
                tracking_code = '?' + tracking_code

            test_url = 'http:{0}'.format(tracking_code)
            # We use { } for macros which rfc3987 doesn't allow so here we replace macros
            # with a single world so that it can still be correctly validated.
            test_url = re.sub('{[^}]+}', 'MACRO', test_url)

            try:
                rfc3987.parse(test_url, rule='IRI')
            except ValueError:
                raise exceptions.TrackingCodeInvalid(
                    'Tracking code structure is not valid.'
                )

    def _validate_state_change(self, new_settings):
        import dash.views.helpers
        if self.state == new_settings.state:
            return
        try:
            dash.views.helpers.validate_ad_groups_state(
                [self.ad_group],
                self.ad_group.campaign,
                self.ad_group.campaign.settings,
                new_settings.state,
            )
        except utils.exc.ValidationError as err:
            raise exceptions.CannotChangeAdGroupState(str(err))

    def _validate_autopilot_settings(self, new_settings):
        from automation import autopilot
        if new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            if not new_settings.b1_sources_group_enabled:
                msg = 'To enable Daily Cap Autopilot, RTB Sources have to be managed as a group.'
                raise exceptions.AutopilotB1SourcesNotEnabled(msg)

            if self.local_b1_sources_group_daily_budget != new_settings.local_b1_sources_group_daily_budget:
                msg = 'Autopilot has to be disabled in order to manage Daily Cap of RTB Sources'
                raise exceptions.DailyBudgetAutopilotNotDisabled(msg)

        if new_settings.autopilot_state in (
                constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
                constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        ):
            if self.local_b1_sources_group_cpc_cc != new_settings.local_b1_sources_group_cpc_cc:
                msg = 'Autopilot has to be disabled in order to manage Daily Cap of RTB Sources'
                raise exceptions.CPCAutopilotNotDisabled(msg)

        min_autopilot_daily_budget = autopilot.get_adgroup_minimum_daily_budget(
            self.ad_group, new_settings
        )
        if new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
           new_settings.autopilot_daily_budget < min_autopilot_daily_budget:
            msg = 'Total Daily Spend Cap must be at least ${min_budget}. Autopilot '\
                  'requires ${min_per_source} or more per active media source.'
            raise exceptions.AutopilotDailyBudgetTooLow(
                msg.format(
                    min_budget=min_autopilot_daily_budget,
                    min_per_source=autopilot.settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC,
                )
            )

    def _validate_all_rtb_state(self, new_settings):
        # MVP for all-RTB-sources-as-one
        # Ensure that AdGroup is paused when enabling/disabling All RTB functionality
        # For now this is the easiest solution to avoid conflicts with ad group budgets and state validations
        if new_settings.state == constants.AdGroupSettingsState.INACTIVE:
            return

        if self.b1_sources_group_enabled != new_settings.b1_sources_group_enabled:
            msg = 'To manage Daily Spend Cap for All RTB as one, ad group must be paused first.'
            if not new_settings.b1_sources_group_enabled:
                'To disable managing Daily Spend Cap for All RTB as one, ad group must be paused first.'
            raise exceptions.AdGroupNotPaused(msg)

    @classmethod
    def _validate_bluekai_tageting(cls, bluekai_targeting):
        if isinstance(bluekai_targeting, list):
            for subexp in bluekai_targeting[1:]:
                cls._validate_bluekai_tageting(subexp)
        else:
            typ, id_ = bluekai_targeting.split(':', 1)
            if typ == 'bluekai':
                try:
                    b_id = int(id_)
                except ValueError:
                    raise exceptions.BluekaiCategoryInvalid(
                        'Invalid BlueKai category id format: "{}"'.format(id_)
                    )
                if not dash.features.bluekai.models.\
                        BlueKaiCategory.objects.active().filter(category_id=b_id):
                        raise exceptions.BluekaiCategoryInvalid(
                            'Invalid BlueKai category id: "{}"'.format(b_id)
                        )

    def _validate_bluekai_targeting_change(self, new_settings):
        if self.bluekai_targeting == new_settings.bluekai_targeting:
            return

        self._validate_bluekai_tageting(new_settings.bluekai_targeting)

    def _validate_yahoo_desktop_targeting(self, new_settings):
        # optimization: only check when targeting is changed to desktop only
        if not (self.target_devices != new_settings.target_devices and
                new_settings.target_devices == [constants.AdTargetDevice.DESKTOP]):
            return

        for ags in self.ad_group.adgroupsource_set.all():
            if ags.source.source_type.type != constants.SourceType.YAHOO:
                continue
            curr_ags_settings = ags.get_current_settings()
            if curr_ags_settings.state != constants.AdGroupSettingsState.ACTIVE:
                continue
            min_cpc = ags.source.source_type.get_min_cpc(new_settings)
            if min_cpc and curr_ags_settings.cpc_cc < min_cpc:
                msg = 'CPC on Yahoo is too low for desktop-only targeting. Please set it to at least $0.25.'
                raise exceptions.YahooDesktopCPCTooLow(msg)
