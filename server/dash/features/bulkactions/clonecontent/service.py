from django.db import transaction

import core.models


@transaction.atomic
def clone(
    request, source_ad_group, content_ads, destination_ad_group, destination_batch_name=None, overridden_state=None
):
    destination_batch = core.models.UploadBatch.objects.clone(
        request.user, source_ad_group, destination_ad_group, destination_batch_name
    )

    core.models.ContentAd.objects.bulk_clone(
        request, content_ads, destination_ad_group, destination_batch, overridden_state
    )

    return destination_batch
