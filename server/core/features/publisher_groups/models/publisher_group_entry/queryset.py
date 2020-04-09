
from django.db import models
from django.db.models.functions import Concat

import core.models


class PublisherGroupEntryQuerySet(models.QuerySet):
    def filter_by_sources(self, sources, include_wo_source=False):
        if not core.models.helpers.should_filter_by_sources(sources):
            return self

        if not include_wo_source:
            return self.filter(source__in=sources)

        return self.filter(models.Q(source__in=sources) | models.Q(source__isnull=True))

    def filter_by_publisher_source(self, publisher_source_dicts):
        q = models.Q()
        for entry in publisher_source_dicts:
            q |= models.Q(publisher=entry["publisher"], source=entry["source"])
        return self.filter(q)

    def annotate_publisher_id(self):
        return self.annotate(
            publisher_id=Concat("publisher", models.Value("__"), "source_id", output_field=models.CharField())
        )
