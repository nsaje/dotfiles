from django.db import transaction

import core.models
import dash.features.cloneadgroup.service

from . import exceptions


def clone(
    request,
    source_campaign,
    destination_campaign_name,
    clone_ad_groups,
    clone_ads,
    ad_group_state_override=None,
    ad_state_override=None,
):

    with transaction.atomic():
        if clone_ads and not clone_ad_groups:
            raise exceptions.CanNotCloneAds("Can't clone ads if ad group is not cloned.")

        cloned_campaign = core.models.Campaign.objects.clone(request, source_campaign, destination_campaign_name)

        if clone_ad_groups:
            source_ad_groups = source_campaign.adgroup_set.all().exclude_archived()

            for source_ad_group in source_ad_groups:
                dash.features.cloneadgroup.service.clone(
                    request,
                    source_ad_group,
                    cloned_campaign,
                    source_ad_group.name,
                    clone_ads,
                    ad_group_state_override,
                    ad_state_override,
                )

    return cloned_campaign
