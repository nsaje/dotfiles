import decimal
import logging

from django.db import transaction
from django.db.models import Sum

import core.common
import core.features.audiences
import core.features.history
import core.models
import core.signals
from dash import constants
from utils import email_helper
from utils import exc
from utils import k1_helper
from utils import redirector_helper

from . import helpers

REDIRECTOR_UPDATE_FIELDS = ("tracking_code", "click_capping_daily_ad_group_max_clicks")
PRIORITY_UPDATE_FIELDS = ("state", "cpm", "cpc", "b1_sources_group_cpc_cc", "b1_sources_group_cpm")

logger = logging.getLogger(__name__)


class AdGroupSettingsMixin(object):
    @transaction.atomic
    def update(
        self,
        request,
        skip_validation=False,
        skip_automation=False,
        skip_permission_check=False,
        skip_notification=False,
        skip_field_change_validation_autopilot=False,
        system_user=None,
        write_history=True,
        write_source_history=True,
        k1_sync=True,
        **updates
    ):
        updates = self._filter_and_remap_input(request, updates, skip_permission_check)
        if not skip_validation:
            self._validate_update(updates)

        updates = self._set_bid_defaults(updates)
        if updates:
            new_settings = self.copy_settings()
            self._apply_updates(new_settings, updates)
            self._sync_legacy_fields(new_settings)
            is_pause = len(updates) == 1 and updates.get("state") == constants.AdGroupSettingsState.INACTIVE
            if not skip_validation and not is_pause:
                self.clean(new_settings)
            self._handle_archived(new_settings)
            self._handle_max_autopilot_bid_change(new_settings)
            self._handle_b1_sources_group_adjustments(new_settings)
            self._handle_bid_autopilot_initial_bids(
                new_settings, skip_notification=skip_notification, write_source_history=write_source_history
            )
            self.keep_old_and_new_bid_values_in_sync(new_settings)
            changes = self.get_setting_changes(new_settings)
            if changes:
                if not skip_field_change_validation_autopilot:
                    self._check_if_fields_are_allowed_to_be_changed_with_autopilot_on(changes)
                new_settings.save(request, system_user=system_user, write_history=write_history)
                max_autopilot_bid_changed = helpers.check_max_autopilot_bid_changed(self, changes)
                b1_sources_group_bid_changed = helpers.check_b1_sources_group_bid_changed(self, changes)
                self.apply_bids_to_sources(
                    max_autopilot_bid_changed=max_autopilot_bid_changed,
                    b1_sources_group_bid_changed=b1_sources_group_bid_changed,
                    write_source_history=write_source_history,
                )
                self._propagate_changes(
                    request, new_settings, changes, system_user, k1_sync, skip_notification=skip_notification
                )
                self._update_ad_group(request, changes)
                # autopilot reloads settings so changes have to be saved when it is called
                if not skip_automation:
                    self._handle_budget_autopilot(changes)
                self._recalculate_multicurrency_values_if_necessary(changes)
                return changes
        return None

    # TODO: RTAP: remove after migration
    def update_daily_budget(self, request):
        if self.b1_sources_group_enabled:
            return

        ad_group_budget_data = self.ad_group.adgroupsource_set.filter_active().aggregate(
            total_local_daily_budget=Sum("settings__local_daily_budget_cc")
        )
        self.update(
            request,
            local_daily_budget=ad_group_budget_data["total_local_daily_budget"],
            skip_validation=True,
            skip_automation=True,
            skip_permission_check=True,
            skip_notification=True,
            skip_field_change_validation_autopilot=True,
            write_history=False,
            write_source_history=False,
            k1_sync=False,
        )

    def _sync_legacy_fields(self, new_settings):
        if not self.ad_group.campaign.account.agency_uses_realtime_autopilot():
            return

        changes = self.get_setting_changes(new_settings)

        # TODO: RTAP: add validation that at most one budget field is updated at once
        budget = (
            changes.get("daily_budget")
            or (new_settings.b1_sources_group_enabled and changes.get("b1_sources_group_daily_budget"))
            or changes.get("autopilot_daily_budget")
        )
        if budget:
            new_settings.daily_budget = budget
            new_settings.autopilot_daily_budget = budget

            if new_settings.b1_sources_group_enabled:
                new_settings.b1_sources_group_daily_budget = budget

        bid_field, b1_sources_group_bid_field = (
            ("cpc", "b1_sources_group_cpc_cc")
            if self.ad_group.bidding_type == constants.BiddingType.CPC
            else ("cpm", "b1_sources_group_cpm")
        )
        bid = (
            changes.get(bid_field)
            or (new_settings.b1_sources_group_enabled and changes.get(b1_sources_group_bid_field))
            or changes.get("max_autopilot_bid")
        )
        if bid:
            setattr(new_settings, bid_field, bid)
            new_settings.max_autopilot_bid = bid

            if new_settings.b1_sources_group_enabled:
                setattr(new_settings, b1_sources_group_bid_field, bid)

    def keep_old_and_new_bid_values_in_sync(self, update_object):
        changes = update_object.__dict__

        # copy old settings (if used) into new ones so that we do not lose any changes done with old settings
        if "cpc_cc" in changes and changes["cpc_cc"] is not None:
            update_object.cpc = changes["cpc_cc"]
        if "local_cpc_cc" in changes and changes["local_cpc_cc"] is not None:
            update_object.local_cpc = changes["local_cpc_cc"]
        if "max_cpm" in changes and changes["max_cpm"] is not None:
            update_object.cpm = changes["max_cpm"]
        if "local_max_cpm" in changes and changes["local_max_cpm"] is not None:
            update_object.local_cpm = changes["local_max_cpm"]

        # copy new settings into old ones so that we do not lose any changes if we need to roll back
        if changes.get("autopilot_state", self.autopilot_state) == constants.AdGroupSettingsAutopilotState.INACTIVE:
            update_object.cpc_cc = changes.get("cpc", self.cpc)
            update_object.local_cpc_cc = changes.get("local_cpc", self.local_cpc)
            update_object.max_cpm = changes.get("cpm", self.cpm)
            update_object.local_max_cpm = changes.get("local_cpm", self.local_cpm)
        else:
            if self.ad_group.bidding_type == constants.BiddingType.CPC:
                update_object.cpc_cc = changes.get("max_autopilot_bid", self.max_autopilot_bid)
                update_object.local_cpc_cc = changes.get("local_max_autopilot_bid", self.local_max_autopilot_bid)
            else:
                update_object.max_cpm = changes.get("max_autopilot_bid", self.max_autopilot_bid)
                update_object.local_max_cpm = changes.get("local_max_autopilot_bid", self.local_max_autopilot_bid)

    def _update_ad_group(self, request, changes):
        if any(field in changes for field in ["ad_group_name", "archived"]):
            if "ad_group_name" in changes:
                self.ad_group.name = changes["ad_group_name"]
            if "archived" in changes:
                self.ad_group.archived = changes["archived"]
            self.ad_group.save(request)

    def _filter_and_remap_input(self, request, updates, skip_permission_check):
        updates = self._remap_fields_for_compatibility(updates)
        updates = self._remove_disallowed_fields(request, updates, skip_permission_check)
        return updates

    # TODO: RTAP: remove this after Phase 1
    def _set_bid_defaults(self, updates):
        agency_uses_realtime_autopilot = self.ad_group.campaign.account.agency_uses_realtime_autopilot()

        if agency_uses_realtime_autopilot:
            return updates

        if self.ad_group.bidding_type == constants.BiddingType.CPC and (
            "cpc" in updates and updates["cpc"] is None or "local_cpc" in updates and updates["local_cpc"] is None
        ):
            updates["cpc"] = self.DEFAULT_CPC_VALUE
            updates.pop("local_cpc", None)
        if self.ad_group.bidding_type == constants.BiddingType.CPM and (
            "cpm" in updates and updates["cpm"] is None or "local_cpm" in updates and updates["local_cpm"] is None
        ):
            updates["cpm"] = self.DEFAULT_CPM_VALUE
            updates.pop("local_cpm", None)
        return updates

    def _remap_fields_for_compatibility(self, updates):
        if "name" in updates:
            updates["ad_group_name"] = updates["name"]

        self._remap_bid_fields(updates)

        if self.ad_group.bidding_type == constants.BiddingType.CPM:
            self._remove_no_change_fields(updates, "cpc_cc")
            self._remove_no_change_fields(updates, "cpc")
        else:
            self._remove_no_change_fields(updates, "max_cpm")
            self._remove_no_change_fields(updates, "cpm")

        self._remove_no_change_fields(updates, "b1_sources_group_cpc_cc")
        self._remove_no_change_fields(updates, "b1_sources_group_cpm")

        return updates

    def _remap_bid_fields(self, updates):
        bidding_type = updates.get("bidding_type", self.ad_group.bidding_type)
        autopilot_active = (
            updates.get("autopilot_state", self.autopilot_state) != constants.AdGroupSettingsAutopilotState.INACTIVE
        )
        if "max_cpc_legacy" in updates and bidding_type == constants.BiddingType.CPC:
            if autopilot_active:
                updates["local_max_autopilot_bid"] = updates.pop("max_cpc_legacy")
            else:
                updates["local_cpc"] = updates.pop("max_cpc_legacy")
        if "max_cpm_legacy" in updates and bidding_type == constants.BiddingType.CPM:
            if autopilot_active:
                updates["local_max_autopilot_bid"] = updates.pop("max_cpm_legacy")
            else:
                updates["local_cpm"] = updates.pop("max_cpm_legacy")

        updates.pop("max_cpc_legacy", None)
        updates.pop("max_cpm_legacy", None)

        if "bid" in updates:
            if self.ad_group.bidding_type == constants.BiddingType.CPC:
                updates["cpc"] = updates.pop("bid")
            elif self.ad_group.bidding_type == constants.BiddingType.CPM:
                updates["cpm"] = updates.pop("bid")
        if "local_bid" in updates:
            if self.ad_group.bidding_type == constants.BiddingType.CPC:
                updates["local_cpc"] = updates.pop("local_bid")
            elif self.ad_group.bidding_type == constants.BiddingType.CPM:
                updates["local_cpm"] = updates.pop("local_bid")

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

            elif not self._can_update_archived_ad_group(updates):
                raise exc.EntityArchivedError("Ad group must not be archived in order to update it.")

        elif self.ad_group.campaign.is_archived():
            raise exc.EntityArchivedError("Account and campaign must not be archived in order to update an ad group.")

    def _can_update_archived_ad_group(self, updates):
        updated_fields = set(updates.keys())
        if not updated_fields.issubset({"archived", "whitelist_publisher_groups", "blacklist_publisher_groups"}):
            return False

        # it should be possible to delete a publisher group, even if it's linked to an archived ad group
        if "whitelist_publisher_groups" in updates and not set(updates["whitelist_publisher_groups"]).issubset(
            self.whitelist_publisher_groups
        ):
            return False
        if "blacklist_publisher_groups" in updates and not set(updates["blacklist_publisher_groups"]).issubset(
            self.blacklist_publisher_groups
        ):
            return False
        return True

    def _handle_archived(self, new_settings):
        if new_settings.archived:
            new_settings.state = constants.AdGroupSettingsState.INACTIVE

    # TODO: RTAP: Remove this after local_max_autopilot_bid is removed
    def _handle_max_autopilot_bid_change(self, new_settings):
        changes = self.get_setting_changes(new_settings)
        if (
            helpers.check_max_autopilot_bid_changed(new_settings, changes)
            and changes["local_max_autopilot_bid"] is not None
        ):
            if self.ad_group.bidding_type == constants.BiddingType.CPC:
                new_settings.local_cpc = changes["local_max_autopilot_bid"]
            elif self.ad_group.bidding_type == constants.BiddingType.CPM:
                new_settings.local_cpm = changes["local_max_autopilot_bid"]

    def _handle_b1_sources_group_adjustments(self, new_settings):
        changes = self.get_setting_changes(new_settings)

        # Turning on RTB-as-one
        if "b1_sources_group_enabled" in changes and changes["b1_sources_group_enabled"]:
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

            if "b1_sources_group_cpc_cc" not in changes and self.ad_group.bidding_type == constants.BiddingType.CPC:
                new_settings.b1_sources_group_cpc_cc = self.cpc or core.models.AllRTBSource.default_cpc_cc

            if "b1_sources_group_cpm" not in changes and self.ad_group.bidding_type == constants.BiddingType.CPM:
                new_settings.b1_sources_group_cpm = self.cpm or core.models.AllRTBSource.default_cpm

            if "b1_sources_group_daily_budget" not in changes:
                new_settings.b1_sources_group_daily_budget = core.models.AllRTBSource.default_daily_budget_cc
                new_settings.daily_budget = core.models.AllRTBSource.default_daily_budget_cc

        # TODO: RTAP: remove after migration
        if (
            not self.ad_group.campaign.account.agency_uses_realtime_autopilot()
            and "b1_sources_group_daily_budget" in changes
        ):
            new_settings.daily_budget = new_settings.b1_sources_group_daily_budget

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

        if self.ad_group.bidding_type == constants.BiddingType.CPM:
            new_settings.b1_sources_group_cpm = avg_bid
        else:
            new_settings.b1_sources_group_cpc_cc = avg_bid

    def _should_set_bid_autopilot_initial_bids(self, new_settings):
        return (
            self.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            and new_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
            and new_settings.b1_sources_group_enabled
        )

    def apply_bids_to_sources(
        self,
        max_autopilot_bid_changed=False,
        b1_sources_group_bid_changed=False,
        skip_notification=False,
        write_source_history=True,
    ):
        agency_uses_realtime_autopilot = self.ad_group.campaign.account.agency_uses_realtime_autopilot()
        autopilot_active = self.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE

        if agency_uses_realtime_autopilot and autopilot_active:
            return

        ad_group_sources_bids = helpers.calculate_ad_group_sources_bids(
            self,
            max_autopilot_bid_changed=max_autopilot_bid_changed,
            b1_sources_group_bid_changed=b1_sources_group_bid_changed,
        )
        # if source bid values change as consequence of ad group bid value change we skip source settings validation to avoid errors
        helpers.set_ad_group_sources_bids(
            self.ad_group.bidding_type,
            ad_group_sources_bids,
            self.ad_group,
            self,
            skip_validation=True,
            skip_notification=skip_notification,
            write_source_history=write_source_history,
        )

    def _should_recalculate_budget_autopilot(self, changes):
        ap_campaign_budget_fields = ["b1_sources_group_state", "state", "start_date", "end_date"]
        return self.ad_group.campaign.settings.autopilot and any(
            field in changes for field in ap_campaign_budget_fields
        )

    def _should_recalculate_budget_autopilot_legacy(self, changes):
        ap_ad_group_budget_fields = ["autopilot_daily_budget", "autopilot_state", "b1_sources_group_state"]
        ap_campaign_budget_fields = ["b1_sources_group_state", "state", "start_date", "end_date"]
        return (
            self.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            and any(field in changes for field in ap_ad_group_budget_fields)
        ) or (
            self.ad_group.campaign.settings.autopilot and any(field in changes for field in ap_campaign_budget_fields)
        )

    def _handle_budget_autopilot(self, changes):
        # TODO: RTAP: LEGACY
        if not self.ad_group.campaign.account.agency_uses_realtime_autopilot():
            if not self._should_recalculate_budget_autopilot_legacy(changes):
                return

            from automation import autopilot_legacy

            autopilot_legacy.recalculate_budgets_ad_group(self.ad_group)
        else:
            if not self._should_recalculate_budget_autopilot(changes):
                return

            from automation import autopilot

            autopilot.recalculate_ad_group_budgets(self.ad_group.campaign)

    def _check_if_fields_are_allowed_to_be_changed_with_autopilot_on(self, changes):
        forbidden_fields = ["autopilot_state", "local_autopilot_daily_budget", "start_date", "end_date"]
        if self.ad_group.campaign.settings.autopilot and any(field in changes for field in forbidden_fields):
            raise exc.ForbiddenError(
                "The following fields can't be changed if autopilot is active: {}, {}, {}, {}".format(
                    *[core.models.settings.AdGroupSettings.get_human_prop_name(field) for field in forbidden_fields]
                )
            )

    def _propagate_changes(self, request, new_settings, changes, system_user, k1_sync, skip_notification=False):
        k1_priority = self.state == constants.AdGroupSettingsState.ACTIVE and any(
            field in changes for field in PRIORITY_UPDATE_FIELDS
        )

        core.signals.settings_change.send_robust(
            sender=self.__class__, request=request, instance=new_settings, changes=changes
        )

        if any(field in changes for field in REDIRECTOR_UPDATE_FIELDS):
            redirector_helper.insert_adgroup(self.ad_group)

        if k1_sync:
            k1_helper.update_ad_group(self.ad_group, msg="AdGroupSettings.put", priority=k1_priority)

        if not skip_notification:
            self._send_notification_email(request, new_settings)

        return changes

    def _send_notification_email(self, request, new_settings):
        if not request:
            return
        user = request.user if request else None
        changes_text = self.get_changes_text(self, new_settings, user, separator="\n")
        email_helper.send_ad_group_notification_email(self.ad_group, request, changes_text)

    def add_to_history(self, user, action_type, changes, history_changes_text=None):
        # remove old bid fields from history
        changes.pop("cpc_cc", None)
        changes.pop("local_cpc_cc", None)
        changes.pop("max_cpm", None)
        changes.pop("local_max_cpm", None)

        changes_text = history_changes_text or self.get_changes_text_from_dict(changes)
        self.ad_group.write_history(
            self.changes_text or changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
            system_user=self.system_user,
        )

    def get_external_bid(self, service_fee, license_fee, margin):
        if self.bid is None:
            return decimal.Decimal(0.0)

        return core.features.bcm.calculations.subtract_fees_and_margin(self.bid, service_fee, license_fee, margin)

    def get_external_b1_sources_group_daily_budget(self, service_fee, license_fee, margin):
        return core.features.bcm.calculations.subtract_fees_and_margin(
            self.b1_sources_group_daily_budget, service_fee, license_fee, margin
        )

    def get_currency(self):
        return self.ad_group.campaign.account.currency

    def _recalculate_multicurrency_values_if_necessary(self, changes):
        if "archived" in changes and not changes["archived"]:
            self.recalculate_multicurrency_values()
            for ad_group_source in self.ad_group.adgroupsource_set.all():
                ad_group_source.settings.recalculate_multicurrency_values()

    def recalculate_multicurrency_values(self):
        fields = ["local_" + field for field in self.ad_group.settings.multicurrency_fields]
        updates = {
            field: getattr(self.ad_group.settings, field)
            for field in fields
            if getattr(self.ad_group.settings, field) is not None
        }
        changes = self.ad_group.settings.update(
            None, skip_validation=True, skip_automation=True, skip_permission_check=True, **updates
        )
        return changes
