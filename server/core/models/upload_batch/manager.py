from django.db import models

import core.common
import dash.constants

from . import model


class UploadBatchManager(models.Manager):
    def create(
        self,
        user,
        account,
        name,
        ad_group=None,
        batch_type=dash.constants.UploadBatchType.INSERT,
        state_override=dash.constants.ContentAdSourceState.ACTIVE,
    ):
        if ad_group is not None:
            core.common.entity_limits.enforce(
                core.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived(), account.id
            )

        batch = model.UploadBatch(
            account=account, name=name, ad_group=ad_group, type=batch_type, state_override=state_override
        )

        batch.save(user=user)
        return batch

    def clone(
        self,
        user,
        source_ad_group,
        ad_group,
        new_batch_name=None,
        state_override=dash.constants.ContentAdSourceState.ACTIVE,
    ):
        account = ad_group.campaign.account
        return self.create(
            user,
            account,
            new_batch_name or model.UploadBatch.generate_cloned_name(source_ad_group),
            ad_group,
            batch_type=dash.constants.UploadBatchType.CLONE,
            state_override=state_override,
        )

    def create_for_file(
        self,
        user,
        account,
        name,
        ad_group,
        original_filename,
        auto_save,
        batch_type=dash.constants.UploadBatchType.INSERT,
        state_override=dash.constants.ContentAdSourceState.ACTIVE,
    ):
        core.common.entity_limits.enforce(
            core.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived(), account.id
        )
        batch = model.UploadBatch(
            account=account,
            name=name,
            ad_group=ad_group,
            original_filename=original_filename,
            auto_save=auto_save,
            type=batch_type,
            state_override=state_override,
        )

        batch.save(user=user)
        return batch
