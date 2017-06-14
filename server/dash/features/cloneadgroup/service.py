from django.db import transaction

from dash.features.bulkactions import clonecontent

import core.entity


@transaction.atomic
def clone(request, source_ad_group, campaign, ad_group_name):
    ad_group = core.entity.AdGroup.objects.clone(request, source_ad_group, campaign, ad_group_name)

    content_ads = source_ad_group.contentad_set.all().exclude_archived()

    if content_ads.exists():
        clonecontent.service.clone(request, source_ad_group, content_ads, ad_group)

    return ad_group
