from django.conf import settings
from django.db import transaction

import core.common
import core.models
import core.models.helpers
import dash.constants
import utils.k1_helper
import utils.redirector_helper

from . import exceptions
from . import model

AMPLIFY_REVIEW_AGENCIES_DISABLED = {55}  # Outbrain
AMPLIFY_REVIEW_ACCOUNTS_DISABLED = {490}  # inPowered


class AdGroupManager(core.common.BaseManager):
    def _create_default_name(self, campaign):
        return core.models.helpers.create_default_name(model.AdGroup.objects.filter(campaign=campaign), "New ad group")

    def _create(self, request, campaign, name, do_save=True, **kwargs):
        ad_group = model.AdGroup(campaign=campaign, name=name, **kwargs)
        if (
            settings.AMPLIFY_REVIEW
            and campaign.account_id not in AMPLIFY_REVIEW_ACCOUNTS_DISABLED
            and campaign.account.agency_id not in AMPLIFY_REVIEW_AGENCIES_DISABLED
            and campaign.type != dash.constants.CampaignType.VIDEO
            and campaign.type != dash.constants.CampaignType.DISPLAY
        ):
            ad_group.amplify_review = True
        if do_save:
            ad_group.save(request)
        return ad_group

    def _post_create(self, ad_group):
        if (
            ad_group.settings.autopilot_state == dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
            or ad_group.campaign.settings.autopilot
        ):
            from automation import autopilot

            autopilot.recalculate_budgets_ad_group(ad_group)

        utils.k1_helper.update_ad_group(ad_group, msg="Campaignmodel.AdGroups.put")
        utils.redirector_helper.insert_adgroup(ad_group)

    def create(self, request, campaign, is_restapi=False, name=None, **kwargs):
        core.common.entity_limits.enforce(
            model.AdGroup.objects.filter(campaign=campaign).exclude_archived(), campaign.account_id
        )
        with transaction.atomic():
            if name is None:
                name = self._create_default_name(campaign)
            ad_group = self._create(request, campaign, name=name)

            if is_restapi:
                ad_group.settings = core.models.settings.AdGroupSettings.objects.create_restapi_default(
                    ad_group, name=name
                )
            else:
                ad_group.settings = core.models.settings.AdGroupSettings.objects.create_default(ad_group, name=name)
            ad_group.save(request)

            core.models.AdGroupSource.objects.bulk_create_on_allowed_sources(
                request, ad_group, write_history=False, k1_sync=False
            )
            if ad_group.amplify_review:
                ad_group.ensure_amplify_review_source(request)

        self._post_create(ad_group)
        ad_group.write_history_created(request)
        return ad_group

    def clone(self, request, source_ad_group, campaign, new_name):
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
            ad_group = self._create(request, campaign, name=new_name)
            ad_group.settings = core.models.settings.AdGroupSettings.objects.clone(
                request, ad_group, source_ad_group.get_current_settings()
            )
            ad_group.save(request)

            core.models.AdGroupSource.objects.bulk_clone_on_allowed_sources(
                request, ad_group, source_ad_group, write_history=False, k1_sync=False
            )
            if ad_group.amplify_review:
                ad_group.ensure_amplify_review_source(request)

        self._post_create(ad_group)
        ad_group.write_history_cloned_from(request, source_ad_group)
        source_ad_group.write_history_cloned_to(request, ad_group)
        return ad_group

    def get_restapi_default(self, request, campaign):
        name = self._create_default_name(campaign)
        ad_group = self._create(request, campaign, name=name, do_save=False)
        ad_group.settings = core.models.settings.AdGroupSettings.objects.get_restapi_default(ad_group, name=name)
        return ad_group