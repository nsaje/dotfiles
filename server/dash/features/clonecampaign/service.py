from django.db import transaction

import core.models
import dash.features.cloneadgroup.service


def clone(request, source_campaign, destination_campaign_name, clone_ad_groups, clone_ads):

    with transaction.atomic():
        cloned_campaign = core.models.Campaign.objects.clone(request, source_campaign, destination_campaign_name)

        if clone_ad_groups:
            source_ad_groups = source_campaign.adgroup_set.all().exclude_archived()

            for source_ad_group in source_ad_groups:
                dash.features.cloneadgroup.service.clone(
                    request, source_ad_group, cloned_campaign, source_ad_group.name, clone_ads
                )

    return cloned_campaign
