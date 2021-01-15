from django.db import models
from django.db import transaction

import core.models.tags.creative


class CreativeTagMixin(models.Model):
    class Meta:
        abstract = True

    tags = models.ManyToManyField("CreativeTag")

    @transaction.atomic
    def set_creative_tags(self, request, data):
        tags = []
        for item in data or []:
            if isinstance(item, str):
                tag = core.models.tags.creative.CreativeTag.objects.create(
                    item, agency=self.agency, account=self.account
                )
                tags.append(tag)
            elif isinstance(item, core.models.tags.creative.CreativeTag):
                self._validate_agency(item, agency=self.agency)
                self._validate_account(item, agency=self.agency, account=self.account)
                tags.append(item)

        self.tags.set(tags)
        self.save(request)

    def get_creative_tags(self):
        return list(self.tags.all())

    def clear_creative_tags(self):
        self.tags.clear()

    @staticmethod
    def _validate_agency(creative_tag, agency=None):
        if creative_tag.agency is None:
            return
        if creative_tag.agency != agency:
            raise core.models.tags.creative.InvalidAgency()

    @staticmethod
    def _validate_account(creative_tag, agency=None, account=None):
        if creative_tag.account is None:
            return
        if agency is not None and creative_tag.account.agency != agency:
            raise core.models.tags.creative.InvalidAccount()
        if account is not None and creative_tag.account != account:
            raise core.models.tags.creative.InvalidAccount()
