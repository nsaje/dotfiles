# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.functions import Concat

import core.common
import core.models

from .publisher_group import PublisherGroup


class PublisherGroupEntryManager(core.common.QuerySetManager):
    def bulk_create(self, objs, batch_size=None):
        publisher_group = objs[0].publisher_group
        core.common.entity_limits.enforce(
            PublisherGroupEntry.objects.filter(publisher_group=publisher_group),
            publisher_group.account_id,
            create_count=len(objs),
        )
        return super(PublisherGroupEntryManager, self).bulk_create(objs, batch_size)

    def create(self, **kwargs):
        publisher_group = kwargs.get("publisher_group")
        if publisher_group is None:
            publisher_group = PublisherGroup.objects.get(pk=kwargs["publisher_group_id"])
        core.common.entity_limits.enforce(
            PublisherGroupEntry.objects.filter(publisher_group=publisher_group), publisher_group.account_id
        )
        return super(PublisherGroupEntryManager, self).create(**kwargs)


class PublisherGroupEntry(models.Model):
    class Meta:
        app_label = "dash"
        ordering = ("pk",)

    id = models.AutoField(primary_key=True)
    publisher_group = models.ForeignKey("PublisherGroup", related_name="entries", on_delete=models.CASCADE)

    publisher = models.CharField(max_length=127, blank=False, null=False, verbose_name="Publisher name or domain")
    source = models.ForeignKey("Source", null=True, blank=True, on_delete=models.PROTECT)
    include_subdomains = models.BooleanField(default=True)

    outbrain_publisher_id = models.CharField(max_length=127, blank=True, verbose_name="Special Outbrain publisher ID")
    outbrain_section_id = models.CharField(max_length=127, blank=True, verbose_name="Special Outbrain section ID")
    outbrain_amplify_publisher_id = models.CharField(
        max_length=127, blank=True, verbose_name="Special Outbrain Amplify publisher ID"
    )
    outbrain_engage_publisher_id = models.CharField(
        max_length=127, blank=True, verbose_name="Special Outbrain Engage publisher ID"
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")

    objects = PublisherGroupEntryManager()

    class QuerySet(models.QuerySet):
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

    def __str__(self):
        return "{} ({})".format(self.publisher, self.source if self.source else "All sources")
