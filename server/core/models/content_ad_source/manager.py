from django.db import models
from django.db import transaction

from . import model


class ContentAdSourceManager(models.Manager):
    def create(self, content_ad, source):
        content_ad_source = model.ContentAdSource(content_ad=content_ad, source=source, state=content_ad.state)

        content_ad_source.save()

        return content_ad_source

    @transaction.atomic
    def bulk_create(self, content_ad, sources):
        content_ad_sources = []
        for source in sources:
            content_ad_sources.append(self.create(content_ad, source))

        return content_ad_sources
