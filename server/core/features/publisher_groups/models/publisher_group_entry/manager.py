from django.db import models

import core.models

from .. import PublisherGroup
from . import model


class PublisherGroupEntryManager(models.Manager):
    def bulk_create(self, objs, batch_size=None):
        if len(objs) > 0:
            publisher_group = objs[0].publisher_group
            core.common.entity_limits.enforce(
                model.PublisherGroupEntry.objects.filter(publisher_group=publisher_group),
                publisher_group.account_id,
                create_count=len(objs),
            )
        return super().bulk_create(objs, batch_size)

    def create(self, **kwargs):
        publisher_group = kwargs.get("publisher_group")
        if publisher_group is None:
            publisher_group = PublisherGroup.objects.get(pk=kwargs["publisher_group_id"])
        core.common.entity_limits.enforce(
            model.PublisherGroupEntry.objects.filter(publisher_group=publisher_group), publisher_group.account_id
        )
        return super().create(**kwargs)
