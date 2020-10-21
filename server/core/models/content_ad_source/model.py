# -*- coding: utf-8 -*-

from django.db import models

from dash import constants

from . import instance
from . import manager
from . import prodops_mixin
from . import queryset


class ContentAdSource(instance.ContentAdSourceMixin, models.Model, prodops_mixin.ProdopsMixin):
    class Meta:
        app_label = "dash"
        indexes = [
            models.Index(fields=["content_ad", "source"], name="dash_contentadsource_cadid_sid"),
            models.Index(fields=["source", "submission_status"], name="dash_contentadsource_sid_ss"),
        ]

    source = models.ForeignKey("Source", on_delete=models.PROTECT)
    content_ad = models.ForeignKey("ContentAd", on_delete=models.PROTECT)

    submission_status = models.IntegerField(
        default=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
        choices=constants.ContentAdSubmissionStatus.get_choices(),
    )
    submission_errors = models.TextField(blank=True, null=True)

    state = models.IntegerField(
        null=True, default=constants.ContentAdSourceState.INACTIVE, choices=constants.ContentAdSourceState.get_choices()
    )
    source_state = models.IntegerField(
        null=True, default=constants.ContentAdSourceState.INACTIVE, choices=constants.ContentAdSourceState.get_choices()
    )

    source_content_ad_id = models.CharField(max_length=50, null=True, db_index=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")

    objects = manager.ContentAdSourceManager.from_queryset(queryset.ContentAdSourceQuerySet)()
