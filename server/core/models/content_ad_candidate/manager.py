from django.db import models
from django.db import transaction

from . import exceptions


class ContentAdCandidateManager(models.Manager):
    @transaction.atomic
    def create(self, ad_group=None, *args, **kwargs):
        self._validate_archived(ad_group)
        return super().create(ad_group=ad_group, *args, **kwargs)

    def _validate_archived(self, ad_group):
        if ad_group and ad_group.is_archived():
            raise exceptions.AdGroupIsArchived("Can not create a content ad on an archived ad group.")
