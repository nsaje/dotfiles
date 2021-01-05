import decimal
import re

import rfc3987

import core.features.audiences
import core.features.multicurrency
import core.features.publisher_groups
import core.models.settings.ad_group_source_settings.validation_helpers
import dash.features.bluekai
import utils.dates_helper
import utils.exc
import utils.validation_helper
from dash import constants

from . import exceptions

ARBITRARY_BLUEKAI_CATEGORIES_AGENCIES = {33}  # inPowered


# should inherit from core.common.BaseValidator so that full_clean is called on save,
# but until the refactoring is completed let's call clean() manually
class AdGroupSettingsValidatorMixin(object):
    def clean(self, new_settings, is_create=False):
        utils.validation_helper.validate_multiple(
            self._validate_cpc,
            self._validate_cpm,
            self._validate_end_date,
            self._validate_tracking_code,
            self._validate_daily_budget,
            changes=self.get_setting_changes(new_settings),
        )
        self._validate_state_change(new_settings)
        self._validate_autopilot_settings(new_settings)
        self._validate_all_rtb_state(new_settings)
        self._validate_bluekai_targeting_change(new_settings)
        self._validate_publisher_groups(new_settings)
        self._validate_custom_audiences(new_settings)
        self._validate_b1_sources_group_cpc_cc(new_settings)
        self._validate_b1_sources_group_cpm(new_settings)
        self._validate_b1_sources_group_daily_budget(new_settings, is_create)
        self._validate_target_browsers(new_settings)
        self._validate_bid(new_settings)

    def _get_currency_symbol(self):
        currency = self.ad_group.campaign.account.currency
        return core.features.multicurrency.get_currency_symbol(currency)

    def _get_exchange_rate(self):
        currency = self.ad_group.campaign.account.currency
        return core.features.multicurrency.get_current_exchange_rate(currency)

    def _validate_cpc(self, changes):
        is_cpm_buying = self.ad_group.bidding_type == constants.BiddingType.CPM
        if is_cpm_buying and "local_cpc" in changes:
            raise exceptions.CannotSetCPC("Cannot set ad group CPC when ad group bidding type is CPM")

        if "local_cpc" not in changes:
            return

        cpc = changes["local_cpc"]

        if cpc is None:
            return

        currency_symbol = self._get_currency_symbol()
        min_cpc = self.MIN_CPC_VALUE * self._get_exchange_rate()
        max_cpc = self.MAX_CPC_VALUE * self._get_exchange_rate()

        if cpc < min_cpc:
            raise exceptions.CPCTooLow("CPC can't be lower than {}{:.3f}.".format(currency_symbol, min_cpc))
        elif cpc > max_cpc:
            raise exceptions.CPCTooHigh("CPC can't be higher than {}{:.2f}.".format(currency_symbol, max_cpc))

    def _validate_cpm(self, changes):
        is_cpm_buying = self.ad_group.bidding_type == constants.BiddingType.CPM
        if not is_cpm_buying and "local_cpm" in changes:
            raise exceptions.CannotSetCPM("Cannot set ad group CPM when ad group bidding type is CPC")

        if "local_cpm" not in changes:
            return

        cpm = changes["local_cpm"]

        if cpm is None:
            return

        currency_symbol = self._get_currency_symbol()
        min_cpm = self.MIN_CPM_VALUE * self._get_exchange_rate()
        max_cpm = self.MAX_CPM_VALUE * self._get_exchange_rate()

        if cpm < min_cpm:
            raise exceptions.CPMTooLow("CPM can't be lower than {}{:.2f}.".format(currency_symbol, min_cpm))
        elif cpm > max_cpm:
            raise exceptions.CPMTooHigh("CPM can't be higher than {}{:.2f}.".format(currency_symbol, max_cpm))

    def _validate_end_date(self, changes):
        end_date = changes.get("end_date")
        if end_date:
            start_date = changes.get("start_date", self.start_date)
            state = changes.get("state", self.state)

            if start_date and end_date < start_date:
                raise exceptions.EndDateBeforeStartDate("End date must not occur before start date.")
            if end_date < utils.dates_helper.local_today() and state == constants.AdGroupSettingsState.ACTIVE:
                raise exceptions.EndDateInThePast("End date cannot be set in the past.")

    def _validate_tracking_code(self, changes):
        tracking_code = changes.get("tracking_code")
        if tracking_code:
            # This is a bit of a hack we're doing here but if we don't prepend 'http:' to
            # the provided tracking code, then rfc3987 doesn't know how to parse it.
            if not tracking_code.startswith("?"):
                tracking_code = "?" + tracking_code

            test_url = "http:{0}".format(tracking_code)
            # We use { } for macros which rfc3987 doesn't allow so here we replace macros
            # with a single world so that it can still be correctly validated.
            test_url = re.sub("{[^}]+}", "MACRO", test_url)

            try:
                rfc3987.parse(test_url, rule="IRI")
            except ValueError:
                raise exceptions.TrackingCodeInvalid("Tracking code structure is not valid.")

    def _validate_daily_budget(self, changes):
        if "daily_budget" in changes and changes["daily_budget"] is None:
            raise exceptions.CannotSetDailyBudgetToUndefined("Cannot set daily budget to undefined.")

    def _validate_state_change(self, new_settings):
        import dash.views.helpers

        if self.state == new_settings.state:
            return
        try:
            dash.views.helpers.validate_ad_groups_state(
                [self.ad_group], self.ad_group.campaign, self.ad_group.campaign.settings, new_settings.state
            )
        except utils.exc.ValidationError as err:
            raise exceptions.CannotChangeAdGroupState(str(err))

    def _validate_autopilot_settings(self, new_settings):
        from automation import autopilot_legacy

        # TODO: RTAP: LEGACY
        if self.ad_group.campaign.account.agency_uses_realtime_autopilot():
            return

        if new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            if not new_settings.b1_sources_group_enabled:
                msg = "To enable Daily Cap Autopilot, RTB Sources have to be managed as a group."
                raise exceptions.AutopilotB1SourcesNotEnabled(msg)

            if self.local_b1_sources_group_daily_budget != new_settings.local_b1_sources_group_daily_budget:
                msg = "Autopilot has to be disabled in order to manage Daily Cap of RTB Sources"
                raise exceptions.DailyBudgetAutopilotNotDisabled(msg)

        if new_settings.autopilot_state in (
            constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        ):
            if self.local_b1_sources_group_cpc_cc != new_settings.local_b1_sources_group_cpc_cc:
                msg = "Autopilot has to be disabled in order to manage group CPC of RTB Sources"
                raise exceptions.CPCAutopilotNotDisabled(msg)

            if self.local_b1_sources_group_cpm != new_settings.local_b1_sources_group_cpm:
                msg = "Autopilot has to be disabled in order to manage group CPM of RTB Sources"
                raise exceptions.CPMAutopilotNotDisabled(msg)

        if (
            new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            and self.autopilot_daily_budget != new_settings.autopilot_daily_budget
        ):
            min_autopilot_daily_budget = autopilot_legacy.get_adgroup_minimum_daily_budget(self.ad_group, new_settings)

            if new_settings.autopilot_daily_budget < min_autopilot_daily_budget:
                msg = "Total Daily Spend Cap must be at least {symbol}{min_budget:.2f}. Autopilot " "requires {symbol}{min_per_source:.2f} or more per active media source."
                exchange_rate = self._get_exchange_rate()
                raise exceptions.AutopilotDailyBudgetTooLow(
                    msg.format(
                        symbol=self._get_currency_symbol(),
                        min_budget=min_autopilot_daily_budget * exchange_rate,
                        min_per_source=autopilot_legacy.settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC
                        * exchange_rate,
                    )
                )

    def _validate_all_rtb_state(self, new_settings):
        # MVP for all-RTB-sources-as-one

        # TODO: remove after migration
        if not self.ad_group.campaign.account.agency_uses_realtime_autopilot():
            # Ensure that AdGroup is paused when enabling/disabling All RTB functionality
            # For now this is the easiest solution to avoid conflicts with ad group budgets and state validations
            if new_settings.state == constants.AdGroupSettingsState.INACTIVE:
                return

            if self.b1_sources_group_enabled != new_settings.b1_sources_group_enabled:
                msg = "To manage Daily Spend Cap for All RTB as one, ad group must be paused first."
                if not new_settings.b1_sources_group_enabled:
                    msg = "To disable managing Daily Spend Cap for All RTB as one, ad group must be paused first."
                raise exceptions.AdGroupNotPaused(msg)

            return

        if self.b1_sources_group_enabled == new_settings.b1_sources_group_enabled:
            return

        if not new_settings.b1_sources_group_enabled:
            raise exceptions.SeparateSourceManagementDeprecated(
                "The option of managing Daily Spend Caps of individual sources is deprecated."
            )

        # Ensure that AdGroup is paused when enabling All RTB functionality
        # For now this is the easiest solution to avoid conflicts with ad group budgets and state validations
        if new_settings.state == constants.AdGroupSettingsState.ACTIVE:
            raise exceptions.AdGroupNotPaused(
                "To manage Daily Spend Cap for All RTB as one, ad group must be paused first."
            )

    def _validate_bluekai_tageting(self, bluekai_targeting):
        if isinstance(bluekai_targeting, list):
            for subexp in bluekai_targeting[1:]:
                self._validate_bluekai_tageting(subexp)
        else:
            typ, id_ = bluekai_targeting.split(":", 1)
            if typ == "bluekai":
                try:
                    b_id = int(id_)
                except ValueError:
                    raise exceptions.BluekaiCategoryInvalid('Invalid BlueKai category id format: "{}"'.format(id_))
                should_validate_category = (
                    self.ad_group.campaign.account.agency_id not in ARBITRARY_BLUEKAI_CATEGORIES_AGENCIES
                )
                if should_validate_category and not dash.features.bluekai.models.BlueKaiCategory.objects.active().filter(
                    category_id=b_id
                ):
                    raise exceptions.BluekaiCategoryInvalid('Invalid BlueKai category id: "{}"'.format(b_id))

    def _validate_bluekai_targeting_change(self, new_settings):
        if self.bluekai_targeting == new_settings.bluekai_targeting:
            return

        self._validate_bluekai_tageting(new_settings.bluekai_targeting)

    def _validate_publisher_groups(self, new_settings):
        if self.whitelist_publisher_groups != new_settings.whitelist_publisher_groups:
            whitelist_count = (
                core.features.publisher_groups.PublisherGroup.objects.all()
                .filter_by_account(self.ad_group.campaign.account)
                .filter(pk__in=new_settings.whitelist_publisher_groups)
                .count()
            )
            if whitelist_count != len(new_settings.whitelist_publisher_groups):
                raise exceptions.PublisherWhitelistInvalid("Invalid whitelist publisher group selection.")

        if self.blacklist_publisher_groups != new_settings.blacklist_publisher_groups:
            blacklist_count = (
                core.features.publisher_groups.PublisherGroup.objects.all()
                .filter_by_account(self.ad_group.campaign.account)
                .filter(pk__in=new_settings.blacklist_publisher_groups)
                .count()
            )
            if blacklist_count != len(new_settings.blacklist_publisher_groups):
                raise exceptions.PublisherBlacklistInvalid("Invalid blacklist publisher group selection.")

    def _validate_custom_audiences(self, new_settings):
        if self.audience_targeting != new_settings.audience_targeting:
            audience_targeting_count = core.features.audiences.Audience.objects.filter(
                pixel__account=self.ad_group.campaign.account, id__in=new_settings.audience_targeting
            ).count()
            if audience_targeting_count != len(new_settings.audience_targeting):
                raise exceptions.AudienceTargetingInvalid("Invalid included custom audience targeting selection.")

        if self.exclusion_audience_targeting != new_settings.exclusion_audience_targeting:
            exclusion_audience_targeting_count = core.features.audiences.Audience.objects.filter(
                pixel__account=self.ad_group.campaign.account, id__in=new_settings.exclusion_audience_targeting
            ).count()
            if exclusion_audience_targeting_count != len(new_settings.exclusion_audience_targeting):
                raise exceptions.ExclusionAudienceTargetingInvalid(
                    "Invalid excluded custom audience targeting selection."
                )

    def _validate_b1_sources_group_cpc_cc(self, new_settings):
        is_cpm_buying = self.ad_group.bidding_type == constants.BiddingType.CPM
        if is_cpm_buying and self.local_b1_sources_group_cpc_cc != new_settings.local_b1_sources_group_cpc_cc:
            raise exceptions.CannotSetB1SourcesCPC(
                "Cannot set all RTB sources group CPC when ad group bidding type is CPM"
            )
        if self.local_b1_sources_group_cpc_cc == new_settings.local_b1_sources_group_cpc_cc:
            return
        if (
            self.ad_group.campaign.account.agency_uses_realtime_autopilot()
            and new_settings.local_b1_sources_group_cpc_cc is None
        ):
            return
        assert isinstance(new_settings.local_b1_sources_group_cpc_cc, decimal.Decimal)
        core.models.settings.ad_group_source_settings.validation_helpers.validate_b1_sources_group_cpc_cc(
            new_settings.b1_sources_group_cpc_cc, new_settings, self.ad_group.campaign.get_bcm_modifiers()
        )

    def _validate_b1_sources_group_cpm(self, new_settings):
        is_cpm_buying = self.ad_group.bidding_type == constants.BiddingType.CPM
        if not is_cpm_buying and self.local_b1_sources_group_cpm != new_settings.local_b1_sources_group_cpm:
            raise exceptions.CannotSetB1SourcesCPM(
                "Cannot set all RTB sources group CPM when ad group bidding type is CPC"
            )
        if self.local_b1_sources_group_cpm == new_settings.local_b1_sources_group_cpm:
            return
        if (
            self.ad_group.campaign.account.agency_uses_realtime_autopilot()
            and new_settings.local_b1_sources_group_cpm is None
        ):
            return
        assert isinstance(new_settings.local_b1_sources_group_cpm, decimal.Decimal)
        core.models.settings.ad_group_source_settings.validation_helpers.validate_b1_sources_group_cpm(
            new_settings.b1_sources_group_cpm, new_settings, self.ad_group.campaign.get_bcm_modifiers()
        )

    def _validate_b1_sources_group_daily_budget(self, new_settings, is_create):
        if self.local_b1_sources_group_daily_budget == new_settings.local_b1_sources_group_daily_budget:
            return
        if not is_create and not new_settings.b1_sources_group_enabled:
            raise exceptions.B1SourcesBudgetUpdateWhileSourcesGroupDisabled(
                "Can not set RTB sources group daily budget while managing RTB sources separately"
            )
        assert isinstance(new_settings.local_b1_sources_group_daily_budget, decimal.Decimal)
        core.models.settings.ad_group_source_settings.validation_helpers.validate_b1_sources_group_daily_budget(
            new_settings.b1_sources_group_daily_budget, new_settings, self.ad_group.campaign.get_bcm_modifiers()
        )

    def _validate_target_browsers(self, new_settings):
        if new_settings.target_browsers is None or new_settings.exclusion_target_browsers is None:
            return

        if len(new_settings.target_browsers) != 0 and len(new_settings.exclusion_target_browsers) != 0:
            raise exceptions.TargetBrowsersInvalid("Cannot set both included and excluded browser targeting")

    def _validate_bid(self, new_settings):
        agency_uses_realtime_autopilot = self.ad_group.campaign.account.agency_uses_realtime_autopilot()

        if (new_settings.ad_group.bidding_type == constants.BiddingType.CPC and new_settings.cpc is None) or (
            new_settings.ad_group.bidding_type == constants.BiddingType.CPM and new_settings.cpm is None
        ):
            if not agency_uses_realtime_autopilot:
                # In the legacy logic, the bid gets set to 0.45 by default if the user deletes it, so this should never happen
                raise exceptions.CannotSetBidToUndefined("Cannot set bid to undefined.")
            elif new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.INACTIVE:
                raise exceptions.CannotSetBidToUndefined("Cannot set bid to undefined when using Target bid.")
