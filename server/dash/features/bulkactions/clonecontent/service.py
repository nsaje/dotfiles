from django.db import transaction

import core.models
import dash.features.contentupload
from core.models.account.exceptions import AccountDoesNotMatch
from utils import k1_helper
from utils import sspd_client


@transaction.atomic
def clone(
    request, source_ad_group, content_ads, destination_ad_group, destination_batch_name=None, overridden_state=None
):
    _validate_same_account(source_ad_group, destination_ad_group)

    destination_batch = core.models.UploadBatch.objects.clone(
        request.user, source_ad_group, destination_ad_group, destination_batch_name, default_state=overridden_state
    )

    core.models.ContentAd.objects.bulk_clone(request, content_ads, destination_ad_group, destination_batch)

    sspd_client.sync_batch(destination_batch)
    k1_helper.update_ad_group(destination_batch.ad_group, msg="clonecontent.clone")

    return destination_batch


@transaction.atomic
def clone_edit(
    request, source_ad_group, content_ads, destination_ad_group, destination_batch_name=None, overridden_state=None
):
    _validate_same_account(source_ad_group, destination_ad_group)

    new_batch_name = destination_batch_name or core.models.UploadBatch.generate_cloned_name(source_ad_group)

    destination_edit_batch, candidates = dash.features.contentupload.upload.insert_clone_edit_candidates(
        request.user, content_ads, destination_ad_group, new_batch_name, overridden_state
    )

    return destination_edit_batch, dash.features.contentupload.upload.get_candidates_with_errors(request, candidates)


def _validate_same_account(source_ad_group, destination_ad_group):
    if source_ad_group.campaign.account != destination_ad_group.campaign.account:
        raise AccountDoesNotMatch(errors={"account": "Can not clone into a different account"})
