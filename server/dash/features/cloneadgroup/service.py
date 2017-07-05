from django.db import transaction

from dash.features.bulkactions import clonecontent

import core.entity
from automation import campaign_stop


@transaction.atomic
def clone(request, source_ad_group, campaign, ad_group_name, clone_ads):
    ad_group = core.entity.AdGroup.objects.clone(request, source_ad_group, campaign, ad_group_name)
    campaign_stop.perform_landing_mode_check(campaign, campaign.get_current_settings())
    if clone_ads:
        content_ads = source_ad_group.contentad_set.all().exclude_archived()

        if content_ads.exists():
            # TODO try catch and return a response
            clonecontent.service.clone(request, source_ad_group, content_ads, ad_group)

    return ad_group
