from django.db import transaction

import core.common
import core.features.audiences
import core.features.history
import core.models
import core.signals
import dash.cpc_constraints
from core.features import bid_modifiers
from dash import constants
from dash import retargeting_helper
from utils import email_helper
from utils import exc
from utils import k1_helper
from utils import redirector_helper

from . import helpers

REDIRECTOR_UPDATE_FIELDS = ("tracking_code", "click_capping_daily_ad_group_max_clicks")
PRIORITY_UPDATE_FIELDS = ("state", "cpm", "cpc", "b1_sources_group_cpc_cc", "b1_sources_group_cpm")


class AdGroupSettingsMixin(object):
    @transaction.atomic
    def update(
        self,
        request,
        skip_validation=False,
        skip_automation=False,
        skip_permission_check=False,
        skip_notification=False,
        system_user=None,
        write_history=True,
        write_source_history=True,
        **updates
    ):
        updates = self._filter_and_remap_input(request, updates, skip_permission_check)
        if not skip_validation:
            self._validate_update(updates)
        updates = self._ensure_bid_default_if_necessary(updates)

        if updates:
            new_settings = self.copy_settings()
            self._apply_updates(new_settings, updates)
            is_pause = len(updates) == 1 and updates.get("state") == constants.AdGroupSettingsState.INACTIVE
            if not skip_validation and not is_pause:
                self.clean(new_settings)
            self._handle_and_set_change_consequences(
                new_settings, skip_notification=skip_notification, write_source_history=write_source_history
            )
            changes = self.get_setting_changes(new_settings)
            if changes:
                self._save_and_propagate(
                    request, new_settings, system_user, write_history=write_history, skip_notification=skip_notification
                )
                self._update_ad_group(request, changes)
                # autopilot reloads settings so changes have to be saved when it is called
                if not skip_automation:
                    self._handle_budget_autopilot(changes)

    @transaction.atomic()
    def update_unsafe(self, request, system_user=None, write_history=True, **kwargs):
        # TEMP(tkusterle) keep the new fields up-to-date with the old ones.
        if "cpc_cc" in kwargs and kwargs["cpc_cc"] is not None:
            kwargs["cpc"] = kwargs["cpc_cc"]
        if "local_cpc_cc" in kwargs and kwargs["local_cpc_cc"] is not None:
            kwargs["local_cpc"] = kwargs["local_cpc_cc"]
        if "max_cpm" in kwargs and kwargs["max_cpm"] is not None:
            kwargs["cpm"] = kwargs["max_cpm"]
        if "local_max_cpm" in kwargs and kwargs["local_max_cpm"] is not None:
            kwargs["local_cpm"] = kwargs["local_max_cpm"]

        kwargs_copy = kwargs.copy()
        kwargs_copy.pop("history_changes_text", None)
        changes = self.get_changes(kwargs_copy)

        super().update_unsafe(request, system_user=system_user, write_history=write_history, **kwargs)

        user = request.user if request else None
        bid_modifiers.source.handle_ad_group_settings_change(self, changes, user=user, system_user=system_user)

    def _ensure_bid_default_if_necessary(self, updates):
        if (
            "cpc_cc" in updates
            and updates["cpc_cc"] is None
            or "local_cpc_cc" in updates
            and updates["local_cpc_cc"] is None
        ):
            updates["cpc"] = core.models.settings.ad_group_settings.model.DEFAULT_CPC_VALUE
        if (
            "max_cpm" in updates
            and updates["max_cpm"] is None
            or "local_max_cpm" in updates
            and updates["local_max_cpm"] is None
        ):
            updates["cpm"] = core.models.settings.ad_group_settings.model.DEFAULT_CPM_VALUE
        return updates

    def _update_ad_group(self, request, changes):
        if any(field in changes for field in ["ad_group_name", "archived"]):
            if "ad_group_name" in changes:
                self.ad_group.name = changes["ad_group_name"]
            if "archived" in changes:
                self.ad_group.archived = changes["archived"]
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

    def _remap_fields_for_compatibility(self, updates):
        if "name" in updates:
            updates["ad_group_name"] = updates["name"]

        if self.ad_group.bidding_type == constants.BiddingType.CPM:
            self._remove_no_change_fields(updates, "cpc_cc")
        else:
            self._remove_no_change_fields(updates, "max_cpm")

        self._remove_no_change_fields(updates, "b1_sources_group_cpc_cc")
        self._remove_no_change_fields(updates, "b1_sources_group_cpm")

        return updates

    def _remove_no_change_fields(self, updates, field):
        local_field = "local_" + field
        if field in updates and updates[field] is None or local_field in updates and updates[local_field] is None:
            updates.pop(field, None)
            updates.pop(local_field, None)

    def _remove_disallowed_fields(self, request, updates, skip_permission_check):
        user = request.user if request else None

        new_updates = {}

        for field, value in list(updates.items()):
            required_permission = not skip_permission_check and self._permissioned_fields.get(field)
            if required_permission and not (user is None or user.has_perm(required_permission)):
                continue
            if field in set(self._settings_fields):
                new_updates[field] = value

        return new_updates

    @staticmethod
    def _apply_updates(new_settings, updates):
        for key, value in updates.items():
            setattr(new_settings, key, value)

    def _validate_update(self, updates):
        if self.archived:
            if updates.get("archived") is False:
                if not self.ad_group.can_restore():
                    raise exc.ForbiddenError("Ad group can not be restored.")

            elif not (updates.get("archived") and len(updates) == 1):
                raise exc.ForbiddenError("Ad group must not be archived in order to update it.")

        elif self.ad_group.campaign.is_archived():
            raise exc.ForbiddenError("Account and campaign must not be archived in order to update an ad group.")

        else:
            if updates.get("archived"):
                if not self.ad_group.can_archive():
                    raise exc.ForbiddenError("Ad group can not be archived.")

    def _handle_and_set_change_consequences(self, new_settings, skip_notification=False, write_source_history=True):
        self._handle_archived(new_settings)
        self._handle_b1_sources_group_adjustments(new_settings)
        self._handle_bid_autopilot_initial_bids(
            new_settings, skip_notification=skip_notification, write_source_history=write_source_history
        )
        self._handle_bid_constraints(new_settings, write_source_history=write_source_history)

    def _handle_archived(self, new_settings):
        if new_settings.archived:
            new_settings.state = constants.AdGroupSettingsState.INACTIVE

    def _handle_b1_sources_group_adjustments(self, new_settings):
        changes = self.get_setting_changes(new_settings)

        # Turning on RTB-as-one
        if "b1_sources_group_enabled" in changes and changes["b1_sources_group_enabled"]:
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

            if "b1_sources_group_cpc_cc" not in changes and self.ad_group.bidding_type == constants.BiddingType.CPC:
                new_settings.b1_sources_group_cpc_cc = core.models.AllRTBSource.default_cpc_cc

            if "b1_sources_group_cpm" not in changes and self.ad_group.bidding_type == constants.BiddingType.CPM:
                new_settings.b1_sources_group_cpm = core.models.AllRTBSource.default_cpm

            if "b1_sources_group_daily_budget" not in changes:
                new_settings.b1_sources_group_daily_budget = core.models.AllRTBSource.default_daily_budget_cc

        if self.ad_group.bidding_type == constants.BiddingType.CPM:
            # Changing adgroup max cpm
            if changes.get("max_cpm") and new_settings.b1_sources_group_enabled:
                new_settings.b1_sources_group_cpm = changes.get("max_cpm")  # reset to max, as implemented in #3353

            if self.b1_sources_group_cpm != new_settings.b1_sources_group_cpm:
                adjusted_b1_sources_group_cpm = helpers.adjust_max_bid(new_settings.b1_sources_group_cpm, new_settings)
                adjusted_b1_sources_group_cpm = helpers._adjust_ad_group_source_bid_to_max(
                    self.ad_group, new_settings, adjusted_b1_sources_group_cpm
                )

                if new_settings.b1_sources_group_cpm != adjusted_b1_sources_group_cpm:
                    new_settings.b1_sources_group_cpm = adjusted_b1_sources_group_cpm
        else:
            # Changing adgroup max cpc
            if changes.get("cpc_cc") and new_settings.b1_sources_group_enabled:
                new_settings.b1_sources_group_cpc_cc = changes.get("cpc_cc")  # reset to max, as implemented in #3353

            if self.b1_sources_group_cpc_cc != new_settings.b1_sources_group_cpc_cc:
                adjusted_b1_sources_group_cpc_cc = helpers.adjust_max_bid(
                    new_settings.b1_sources_group_cpc_cc, new_settings
                )
                adjusted_b1_sources_group_cpc_cc = helpers._adjust_ad_group_source_bid_to_max(
                    self.ad_group, new_settings, adjusted_b1_sources_group_cpc_cc
                )

                if new_settings.b1_sources_group_cpc_cc != adjusted_b1_sources_group_cpc_cc:
                    new_settings.b1_sources_group_cpc_cc = adjusted_b1_sources_group_cpc_cc

    def _handle_bid_autopilot_initial_bids(self, new_settings, skip_notification=False, write_source_history=True):
        if not self._should_set_bid_autopilot_initial_bids(new_settings):
            return

        all_b1_sources = self.ad_group.adgroupsource_set.filter(source__source_type__type=constants.SourceType.B1)
        active_b1_sources = all_b1_sources.filter_active()
        active_b1_sources_settings = core.models.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=active_b1_sources
        ).group_current_settings()

        if active_b1_sources.count() < 1:
            return

        ags_bid_field = "cpm" if self.ad_group.bidding_type == constants.BiddingType.CPM else "cpc_cc"
        avg_bid = sum(getattr(agss, ags_bid_field) for agss in active_b1_sources_settings) / len(
            active_b1_sources_settings
        )
        new_ad_group_sources_bids = {ad_group_source: avg_bid for ad_group_source in all_b1_sources}

        if self.ad_group.bidding_type == constants.BiddingType.CPM:
            new_settings.b1_sources_group_cpm = avg_bid
            helpers.set_ad_group_sources_cpms(
                new_ad_group_sources_bids,
                self.ad_group,
                new_settings,
                skip_notification=skip_notification,
                write_source_history=write_source_history,
            )
        else:
            new_settings.b1_sources_group_cpc_cc = avg_bid
            helpers.set_ad_group_sources_cpcs(
                new_ad_group_sources_bids,
                self.ad_group,
                new_settings,
                skip_notification=skip_notification,
                write_source_history=write_source_history,
            )

    def _should_set_bid_autopilot_initial_bids(self, new_settings):
        return (
            self.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            and new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
            and new_settings.b1_sources_group_enabled
        )

    def _handle_bid_constraints(self, new_settings, skip_notification=False, write_source_history=True):
        ad_group_sources_bids = helpers.get_adjusted_ad_group_sources_bids(self.ad_group, new_settings)
        if self.ad_group.bidding_type == constants.BiddingType.CPM:
            self._handle_cpm_constraints(
                new_settings,
                ad_group_sources_bids,
                skip_notification=skip_notification,
                write_source_history=write_source_history,
            )
        else:
            self._handle_cpc_constraints(
                new_settings,
                ad_group_sources_bids,
                skip_notification=skip_notification,
                write_source_history=write_source_history,
            )

    def _handle_cpm_constraints(
        self, new_settings, ad_group_sources_cpms, skip_notification=False, write_source_history=True
    ):
        helpers.set_ad_group_sources_cpms(
            ad_group_sources_cpms,
            self.ad_group,
            new_settings,
            skip_validation=True,
            skip_notification=skip_notification,
            write_source_history=write_source_history,
        )

    def _handle_cpc_constraints(
        self, new_settings, ad_group_sources_cpcs, skip_notification=False, write_source_history=True
    ):
        if self.b1_sources_group_cpc_cc != new_settings.b1_sources_group_cpc_cc:
            bcm_modifiers = self.ad_group.campaign.get_bcm_modifiers()
            try:
                helpers.validate_ad_group_sources_cpc_constraints(bcm_modifiers, ad_group_sources_cpcs, self.ad_group)
            except dash.cpc_constraints.ValidationError as err:
                raise exc.ValidationError(errors={"b1_sources_group_cpc_cc": list(set(err))})
        helpers.set_ad_group_sources_cpcs(
            ad_group_sources_cpcs,
            self.ad_group,
            new_settings,
            skip_validation=True,
            skip_notification=skip_notification,
            write_source_history=write_source_history,
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

    def _handle_budget_autopilot(self, changes):
        if not self._should_recalculate_budget_autopilot(changes):
            return

        from automation import autopilot

        autopilot.recalculate_budgets_ad_group(self.ad_group)

    def _save_and_propagate(self, request, new_settings, system_user, write_history=True, skip_notification=False):
        changes = self.get_setting_changes(new_settings)
        new_settings.save(request, system_user=system_user, write_history=write_history)

        core.signals.settings_change.send_robust(
            sender=self.__class__, request=request, instance=new_settings, changes=changes
        )

        if any(field in changes for field in REDIRECTOR_UPDATE_FIELDS):
            redirector_helper.insert_adgroup(self.ad_group)

        priority = any(field in changes for field in PRIORITY_UPDATE_FIELDS)
        k1_helper.update_ad_group(self.ad_group, msg="AdGroupSettings.put", priority=priority)

        if not skip_notification:
            self._send_notification_email(request, new_settings)

    def _send_notification_email(self, request, new_settings):
        if not request:
            return
        user = request.user if request else None
        changes_text = self.get_changes_text(self, new_settings, user, separator="\n")
        email_helper.send_ad_group_notification_email(self.ad_group, request, changes_text)

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        # TEMP(tkusterle) remove the new fields from histroy
        changes.pop("cpc", None)
        changes.pop("local_cpc", None)
        changes.pop("cpm", None)
        changes.pop("local_cpm", None)

        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)
        self.ad_group.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user,
        )

    def get_external_b1_sources_group_daily_budget(self, account, license_fee, margin):
        b1_sources_group_daily_budget = self.b1_sources_group_daily_budget
        if account.uses_bcm_v2:
            b1_sources_group_daily_budget = core.features.bcm.calculations.subtract_fee_and_margin(
                b1_sources_group_daily_budget, license_fee, margin
            )
        return b1_sources_group_daily_budget

    def get_currency(self):
        return self.ad_group.campaign.account.currency
