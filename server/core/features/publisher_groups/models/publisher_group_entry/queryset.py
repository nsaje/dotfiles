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
            q |= models.Q(publisher=entry["publisher"], source=entry["source"], placement=entry.get("placement"))
        return self.filter(q)

    def filter_publisher_or_placement(self, is_placement):
        if is_placement:
            return self.exclude(placement=None)

        return self.filter(placement=None)

    def annotate_entry_id(self, is_placement=False):
        if is_placement:
            return self.annotate(
                entry_id=Concat(
                    "publisher",
                    models.Value("__"),
                    "source_id",
                    models.Value("__"),
                    "placement",
                    output_field=models.CharField(),
                )
            )

        return self.annotate(
            entry_id=Concat("publisher", models.Value("__"), "source_id", output_field=models.CharField())
        )
