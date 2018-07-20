from django.db import transaction

import core.entity


@transaction.atomic
def clone(
    request, source_ad_group, content_ads, destination_ad_group, destination_batch_name=None, overridden_state=None
):
    destination_batch = core.entity.UploadBatch.objects.clone(
        request.user, source_ad_group, destination_ad_group, destination_batch_name
    )

    core.entity.ContentAd.objects.bulk_clone(
        request, content_ads, destination_ad_group, destination_batch, overridden_state
    )

    return destination_batch
