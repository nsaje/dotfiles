from django.db import transaction

from dash.features.bulkactions import clonecontent

import core.entity


@transaction.atomic
def clone(request, source_ad_group, campaign):
    ad_group = core.entity.AdGroup.objects.clone(request, source_ad_group, campaign)

    clonecontent.service.clone(
        request.user, source_ad_group, source_ad_group.contentad_set.all().exclude_archived(), ad_group)

    return ad_group
