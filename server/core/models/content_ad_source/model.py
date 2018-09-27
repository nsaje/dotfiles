# -*- coding: utf-8 -*-

from django.db import models, transaction

from dash import constants

from . import prodops_mixin


class ContentAdSourceManager(models.Manager):
    def create(self, content_ad, source):
        content_ad_source = ContentAdSource(content_ad=content_ad, source=source, state=content_ad.state)

        content_ad_source.save()

        return content_ad_source

    @transaction.atomic
    def bulk_create(self, content_ad, sources):
        content_ad_sources = []
        for source in sources:
            content_ad_sources.append(self.create(content_ad, source))

        return content_ad_sources


class ContentAdSource(models.Model, prodops_mixin.ProdopsMixin):
    class Meta:
        app_label = "dash"

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

    def get_submission_status(self):
        if (
            self.submission_status != constants.ContentAdSubmissionStatus.APPROVED
            and self.submission_status != constants.ContentAdSubmissionStatus.REJECTED
        ):
            return constants.ContentAdSubmissionStatus.PENDING
        return self.submission_status

    def get_source_id(self):
        if self.source.source_type and self.source.source_type.type in [
            constants.SourceType.B1,
            constants.SourceType.GRAVITY,
        ]:
            return self.content_ad_id
        else:
            return self.source_content_ad_id

    def __str__(self):
        return "{}(id={}, content_ad={}, source={}, state={}, source_state={}, submission_status={}, source_content_ad_id={})".format(
            self.__class__.__name__,
            self.id,
            self.content_ad,
            self.source,
            self.state,
            self.source_state,
            self.submission_status,
            self.source_content_ad_id,
        )

    class QuerySet(models.QuerySet):
        def filter_by_sources(self, sources):
            return self.filter(source__in=sources)

    objects = ContentAdSourceManager.from_queryset(QuerySet)()
