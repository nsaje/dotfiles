import decimal

from django.db import transaction
from django.db.models import Sum
from django.db.models import Value
from django.db.models.functions import Coalesce

import core.common
import core.features.audiences
import core.features.history
import core.models
import core.signals
from dash import constants
from utils import decimal_helpers
from utils import email_helper
from utils import exc
from utils import k1_helper
from utils import zlogging

from . import exceptions
from . import helpers

PRIORITY_UPDATE_FIELDS = ("state", "cpm", "cpc", "b1_sources_group_cpc_cc", "b1_sources_group_cpm")

logger = zlogging.getLogger(__name__)


class AdGroupSettingsMixin(object):
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
        is_create=False,
        **updates,
    ):
        changes = None
        new_settings = None
        with transaction.atomic():
            updates = self._filter_and_remap_input(request, updates, skip_permission_check)
            if not skip_validation:
                self._validate_update(updates)

            updates = self._set_bid_defaults(updates)
            if updates:
                new_settings = self.copy_settings()
                self._apply_updates(new_settings, updates)
                self._handle_legacy_changes(new_settings, skip_validation)
                is_pause = len(updates) == 1 and updates.get("state") == constants.AdGroupSettingsState.INACTIVE
                if not skip_validation and not is_pause:
                    self.clean(new_settings, is_create)
                self._handle_archived(new_settings)
                self._handle_max_autopilot_bid_change(new_settings)
                self._handle_b1_sources_group_adjustments(new_settings)
                self._handle_bid_autopilot_initial_bids(
                    new_settings, skip_notification=skip_notification, write_source_history=write_source_history
                )
                changes = self.get_setting_changes(new_settings)
                if changes:
                    if not skip_field_change_validation_autopilot:
                        self._check_if_fields_are_allowed_to_be_changed_with_autopilot_on(changes)
                    new_settings.save(request, system_user=system_user, write_history=write_history)
                    max_autopilot_bid_changed = helpers.check_max_autopilot_bid_changed(self, changes)
                    helpers.adjust_to_autopilot_bid_if_needed(self, max_autopilot_bid_changed)

                    core.signals.settings_change.send_robust(
                        sender=self.__class__, request=request, instance=new_settings, changes=changes
                    )

                    self._update_ad_group(request, changes)
                    # autopilot reloads settings so changes have to be saved when it is called
                    if not skip_automation:
                        self._handle_budget_autopilot(changes)
                    self._recalculate_multicurrency_values_if_necessary(changes)

        if changes and new_settings:
            self._propagate_changes(
                request, new_settings, changes, system_user, k1_sync, skip_notification=skip_notification
            )

        return changes

    # TODO: RTAP: remove after migration
    def update_daily_budget(self, request):
        if self.b1_sources_group_enabled:
            return

        ad_group_budget_data = self.ad_group.adgroupsource_set.filter_active().aggregate(
            total_local_daily_budget=Coalesce(Sum("settings__local_daily_budget_cc"), Value("0.0"))
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

    def _handle_legacy_changes(self, new_settings, skip_validation=False):
        # TODO: RTAP: remove check after migration
        if not self.ad_group.campaign.account.agency_uses_realtime_autopilot():
            return

        changes = self.get_setting_changes(new_settings)
        if not skip_validation:
            self._validate_legacy_changes(changes, self._multicurrency_bid_fields, "bid")
            self._validate_legacy_changes(changes, self._multicurrency_budget_fields, "budget")

        self._sync_legacy_fields(new_settings, changes)

    def _validate_legacy_changes(self, changes, fields, field_group_name):
        changes_fields = changes.keys() & set(fields)
        values = [changes[f] for f in changes_fields]
        if values and values.count(values[0]) != len(values):
            raise exceptions.LegacyFieldsUpdateMismatch(
                "{} updated with multiple values".format(field_group_name.capitalize())
            )

    def _sync_legacy_fields(self, new_settings, changes):
        budget_update_field = (
            "local_daily_budget" in changes
            and "local_daily_budget"
            or "local_autopilot_daily_budget" in changes
            and "local_autopilot_daily_budget"
            or "local_b1_sources_group_daily_budget" in changes
            and "local_b1_sources_group_daily_budget"
        )
        if budget_update_field:
            budget = changes.get(budget_update_field)
            if budget is not None:
                new_settings.local_daily_budget = budget
                new_settings.local_autopilot_daily_budget = budget
                new_settings.local_b1_sources_group_daily_budget = budget

        bid_field, b1_sources_group_bid_field = (
            ("local_cpc", "local_b1_sources_group_cpc_cc")
            if self.ad_group.bidding_type == constants.BiddingType.CPC
            else ("local_cpm", "local_b1_sources_group_cpm")
        )
        bid_update_field = (
            bid_field in changes
            and bid_field
            or "local_max_autopilot_bid" in changes
            and "local_max_autopilot_bid"
            or b1_sources_group_bid_field in changes
            and b1_sources_group_bid_field
        )
        if bid_update_field:
            bid = changes[bid_update_field]

            setattr(new_settings, bid_field, bid)
            new_settings.local_max_autopilot_bid = bid
            setattr(new_settings, b1_sources_group_bid_field, bid)

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

        uses_realtime_autopilot = self.ad_group.campaign.account.agency_uses_realtime_autopilot()
        is_cpm_bidding = self.ad_group.bidding_type == constants.BiddingType.CPM

        if is_cpm_bidding:
            self._remove_no_change_fields(updates, "cpc_cc")
            self._remove_no_change_fields(updates, "cpc")
        else:
            self._remove_no_change_fields(updates, "max_cpm")
            self._remove_no_change_fields(updates, "cpm")

        if is_cpm_bidding or not uses_realtime_autopilot:
            self._remove_no_change_fields(updates, "b1_sources_group_cpc_cc")
        if not is_cpm_bidding or not uses_realtime_autopilot:
            self._remove_no_change_fields(updates, "b1_sources_group_cpm")

        if "daily_budget_legacy" in updates:
            daily_budget_legacy = updates.pop("daily_budget_legacy")

            # TODO: RTAP: remove at cleanup
            if daily_budget_legacy is not None:
                logger.info(
                    "daily_budget_cc updated with non-default value",
                    agency_id=self.ad_group.campaign.account.agency_id,
                    ad_group_id=self.ad_group.id,
                    daily_budget_cc=daily_budget_legacy,
                )

            if uses_realtime_autopilot:
                if "local_daily_budget" in updates and updates["local_daily_budget"] != daily_budget_legacy:
                    raise exceptions.LegacyFieldsUpdateMismatch("Budget updated with multiple values")

                updates["local_daily_budget"] = daily_budget_legacy
            else:
                updates["daily_budget_cc"] = daily_budget_legacy

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
        uses_realtime_autopilot = self.ad_group.campaign.account.agency_uses_realtime_autopilot()

        # Turning on RTB-as-one
        if "b1_sources_group_enabled" in changes and changes["b1_sources_group_enabled"]:
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

            if "b1_sources_group_cpc_cc" not in changes and self.ad_group.bidding_type == constants.BiddingType.CPC:
                default_cpc = self.cpc or core.models.AllRTBSource.default_cpc_cc
                new_settings.b1_sources_group_cpc_cc = default_cpc

                # TODO: RTAP: remove check after migration
                if uses_realtime_autopilot:
                    new_settings.cpc = default_cpc
                    new_settings.max_autopilot_bid = default_cpc

            if "b1_sources_group_cpm" not in changes and self.ad_group.bidding_type == constants.BiddingType.CPM:
                default_cpm = self.cpm or core.models.AllRTBSource.default_cpm
                new_settings.b1_sources_group_cpm = default_cpm

                # TODO: RTAP: remove check after migration
                if uses_realtime_autopilot:
                    new_settings.cpm = default_cpm
                    new_settings.max_autopilot_bid = default_cpm

            if "b1_sources_group_daily_budget" not in changes:
                new_settings.b1_sources_group_daily_budget = core.models.AllRTBSource.default_daily_budget_cc
                new_settings.daily_budget = core.models.AllRTBSource.default_daily_budget_cc

                # TODO: RTAP: remove check after migration
                if uses_realtime_autopilot:
                    new_settings.autopilot_daily_budget = core.models.AllRTBSource.default_daily_budget_cc

        # TODO: RTAP: remove after migration
        if not uses_realtime_autopilot and "b1_sources_group_daily_budget" in changes:
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

        # TODO: RTAP: campaign autopilot can set budget to 4 decimals while UI only provides 2
        if (
            "local_autopilot_daily_budget" in changes
            and changes["local_autopilot_daily_budget"]
            and self.local_autopilot_daily_budget
            and decimal_helpers.equal_decimals(
                self.local_autopilot_daily_budget,
                changes.get("local_autopilot_daily_budget"),
                precision=decimal.Decimal("1.00"),
            )
        ):
            forbidden_fields.remove("local_autopilot_daily_budget")

        # TODO: RTAP: remove the field from the check after migration
        if "autopilot_state" in changes and self.ad_group.campaign.account.agency_uses_realtime_autopilot():
            forbidden_fields.remove("autopilot_state")

        if self.ad_group.campaign.settings.autopilot and any(field in changes for field in forbidden_fields):
            raise exc.ForbiddenError(
                "The following fields can't be changed if autopilot is active: {}".format(
                    ", ".join(
                        [core.models.settings.AdGroupSettings.get_human_prop_name(field) for field in forbidden_fields]
                    )
                )
            )

    def _propagate_changes(self, request, new_settings, changes, system_user, k1_sync, skip_notification=False):
        k1_priority = self.state == constants.AdGroupSettingsState.ACTIVE and any(
            field in changes for field in PRIORITY_UPDATE_FIELDS
        )

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
