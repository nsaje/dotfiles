# -*- coding: utf-8 -*-

from django.db import models

from . import instance
from . import manager
from . import queryset


class PublisherGroupEntry(instance.PublisherGroupsEntryMixin, models.Model):
    class Meta:
        app_label = "dash"
        ordering = ("pk",)

    id = models.AutoField(primary_key=True)
    publisher_group = models.ForeignKey("PublisherGroup", related_name="entries", on_delete=models.CASCADE)

    source = models.ForeignKey("Source", null=True, blank=True, on_delete=models.PROTECT)
    publisher = models.CharField(max_length=127, blank=False, null=False, verbose_name="Publisher name or domain")
    include_subdomains = models.BooleanField(default=True)
    placement = models.CharField(max_length=127, null=True, blank=True)

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

    objects = manager.PublisherGroupEntryManager.from_queryset(queryset.PublisherGroupEntryQuerySet)()

    def __str__(self):
        return "{} ({})".format(self.publisher, self.source if self.source else "All sources")
