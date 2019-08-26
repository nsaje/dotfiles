from django.db import transaction

import core.models
from core.models.account.exceptions import AccountDoesNotMatch
from utils import k1_helper
from utils import sspd_client


@transaction.atomic
def clone(
    request, source_ad_group, content_ads, destination_ad_group, destination_batch_name=None, overridden_state=None
):
    _validate_same_account(source_ad_group, destination_ad_group)

    destination_batch = core.models.UploadBatch.objects.clone(
        request.user, source_ad_group, destination_ad_group, destination_batch_name
    )

    core.models.ContentAd.objects.bulk_clone(
        request, content_ads, destination_ad_group, destination_batch, overridden_state
    )

    sspd_client.sync_batch(destination_batch)
    k1_helper.update_ad_group(destination_batch.ad_group, msg="clonecontent.clone")

    return destination_batch


def _validate_same_account(source_ad_group, destination_ad_group):
    if source_ad_group.campaign.account != destination_ad_group.campaign.account:
        raise AccountDoesNotMatch(errors={"account": "Can not clone into a different account"})
