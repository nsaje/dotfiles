import copy

from django.conf import settings
from django.db import transaction

import core.common
import core.models
import core.models.helpers
import dash.constants
import prodops.hacks
import utils.k1_helper

from . import exceptions
from . import model


class AdGroupManager(core.common.BaseManager):
    def create(
        self,
        request,
        campaign,
        is_restapi=False,
        name=None,
        bidding_type=dash.constants.BiddingType.CPC,
        initial_settings=None,
        sources=None,
        **kwargs,
    ):
        self._validate_archived(campaign)
        self._validate_entity_limits(campaign)

        with transaction.atomic():
            if name is None:
                name = self._create_default_name(campaign)
            if bidding_type is None:
                bidding_type = dash.constants.BiddingType.CPC
            ad_group = self._prepare(campaign, name=name, bidding_type=bidding_type)
            ad_group.save(request)

            if is_restapi:
                ad_group.settings = core.models.settings.AdGroupSettings.objects.create_restapi_default(
                    ad_group, name=name
                )
            else:
                ad_group.settings = core.models.settings.AdGroupSettings.objects.create_default(ad_group, name=name)
            ad_group.save(request)

            apply_ad_group_bids = False
            autopilot_inactive = (
                initial_settings.get("autopilot_state", ad_group.settings.autopilot_state)
                if initial_settings
                else ad_group.settings.autopilot_state
            ) == dash.constants.AdGroupSettingsAutopilotState.INACTIVE

            if autopilot_inactive:
                apply_ad_group_bids = True
            elif initial_settings is not None:
                if initial_settings.get("max_autopilot_bid") is not None:
                    apply_ad_group_bids = True
                    initial_settings["bid"] = initial_settings["max_autopilot_bid"]
                elif initial_settings.get("local_max_autopilot_bid") is not None:
                    apply_ad_group_bids = True
                    initial_settings["local_bid"] = initial_settings["local_max_autopilot_bid"]

            if initial_settings:
                settings_updates = copy.copy(initial_settings)
                self._set_initial_bids_if_necessary(ad_group, settings_updates)
                ad_group.settings.update(
                    request,
                    **settings_updates,
                    skip_field_change_validation_autopilot=True,
                    skip_automation=True,
                    is_create=True,
                )  # automation is ran in _post_create

            if campaign.account_id != settings.HARDCODED_ACCOUNT_ID_OEN:
                core.models.AdGroupSource.objects.bulk_create_on_allowed_sources(
                    request,
                    ad_group,
                    sources=sources,
                    write_history=False,
                    k1_sync=False,
                    apply_ad_group_bids=apply_ad_group_bids,
                )

            if ad_group.amplify_review:
                ad_group.ensure_amplify_review_source(request)

        self._post_create(ad_group)
        ad_group.write_history_created(request)
        return ad_group

    def clone(self, request, source_ad_group, campaign, new_name, state_override=None):
        if (
            source_ad_group.campaign.type == dash.constants.CampaignType.VIDEO
            or campaign.type == dash.constants.CampaignType.VIDEO
            or source_ad_group.campaign.type == dash.constants.CampaignType.DISPLAY
            or campaign.type == dash.constants.CampaignType.DISPLAY
        ) and source_ad_group.campaign.type != campaign.type:
            raise exceptions.CampaignTypesDoNotMatch("Source and destination campaign types do not match.")

        core.common.entity_limits.enforce(
            model.AdGroup.objects.filter(campaign=campaign).exclude_archived(), campaign.account_id
        )

        with transaction.atomic():
            ad_group = self._prepare(campaign, name=new_name)
            for field in set(self.model._clone_fields):
                setattr(ad_group, field, getattr(source_ad_group, field))
            ad_group.save(request)

            ad_group.settings = core.models.settings.AdGroupSettings.objects.clone(
                request, ad_group, source_ad_group.get_current_settings(), state_override=state_override
            )
            ad_group.save(request)

            core.models.AdGroupSource.objects.bulk_clone_on_allowed_sources(
                request, ad_group, source_ad_group, write_history=False, k1_sync=False
            )
            if ad_group.amplify_review:
                ad_group.ensure_amplify_review_source(request)

            for deal_connection in source_ad_group.directdealconnection_set.all():
                core.features.deals.DirectDealConnection.objects.clone(request, deal_connection, adgroup=ad_group)

            bid_modifiers = list(
                source_ad_group.bidmodifier_set.exclude(type=core.features.bid_modifiers.constants.BidModifierType.AD)
            )
            if bid_modifiers:
                core.features.bid_modifiers.set_bulk(
                    ad_group, bid_modifiers, user=request.user, write_history=False, propagate_to_k1=False
                )

        self._post_create(ad_group)
        ad_group.write_history_cloned_from(request, source_ad_group)
        source_ad_group.write_history_cloned_to(request, ad_group)
        prodops.hacks.apply_ad_group_create_hacks(request, ad_group)
        return ad_group

    def get_default(self, request, campaign):
        ad_group = self._prepare(campaign, name="")
        ad_group.settings = core.models.settings.AdGroupSettings.objects.get_default(ad_group, name="")
        return ad_group

    def _create_default_name(self, campaign):
        return core.models.helpers.create_default_name(model.AdGroup.objects.filter(campaign=campaign), "New ad group")

    def _prepare(self, campaign, name, **kwargs):
        ad_group = model.AdGroup(campaign=campaign, name=name, **kwargs)
        if (
            settings.AMPLIFY_REVIEW
            and (
                campaign.account.amplify_review
                and (campaign.account.agency.amplify_review if campaign.account.agency else True)
            )
            and campaign.type != dash.constants.CampaignType.VIDEO
            and campaign.type != dash.constants.CampaignType.DISPLAY
        ):
            ad_group.amplify_review = True

        if campaign.type == dash.constants.CampaignType.VIDEO:
            ad_group.bidding_type = dash.constants.BiddingType.CPM

        return ad_group

    def _post_create(self, ad_group):
        # TODO: RTAP: LEGACY
        if not ad_group.campaign.account.agency_uses_realtime_autopilot():
            if (
                ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
                or ad_group.campaign.settings.autopilot
            ):
                from automation import autopilot_legacy

                autopilot_legacy.recalculate_budgets_ad_group(ad_group)
        else:
            if ad_group.campaign.settings.autopilot:
                from automation import autopilot

                autopilot.recalculate_ad_group_budgets(ad_group.campaign)

        utils.k1_helper.update_ad_group(ad_group, msg="Campaignmodel.AdGroups.put")

    def _validate_archived(self, campaign):
        if campaign.is_archived():
            raise exceptions.CampaignIsArchived("Can not create an ad group on an archived campaign.")

    def _validate_entity_limits(self, campaign):
        core.common.entity_limits.enforce(
            model.AdGroup.objects.filter(campaign=campaign).exclude_archived(), campaign.account_id
        )

    def _set_initial_bids_if_necessary(self, ad_group, settings_updates):
        if ad_group.bidding_type == dash.constants.BiddingType.CPC and not (
            settings_updates.get("cpc") or settings_updates.get("local_cpc")
        ):
            settings_updates["cpc"] = core.models.settings.AdGroupSettings.DEFAULT_CPC_VALUE
        elif ad_group.bidding_type == dash.constants.BiddingType.CPM and not (
            settings_updates.get("cpm") or settings_updates.get("local_cpm")
        ):
            settings_updates["cpm"] = core.models.settings.AdGroupSettings.DEFAULT_CPM_VALUE
