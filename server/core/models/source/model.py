# -*- coding: utf-8 -*-

from decimal import Decimal

import tagulous
from django.db import models
from django.utils.translation import ugettext_lazy as _

import dash.constants
from core.common import BaseManager

from . import instance
from . import queryset


class Source(instance.SourceMixin, models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    source_type = models.ForeignKey("SourceType", null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    tracking_slug = models.CharField(max_length=50, null=False, blank=False, unique=True, verbose_name="Tracking slug")
    bidder_slug = models.CharField(max_length=50, null=False, blank=False, unique=True, verbose_name="B1 Slug")
    maintenance = models.BooleanField(default=True)
    deprecated = models.BooleanField(default=False, null=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    released = models.BooleanField(default=False)

    supports_retargeting = models.BooleanField(
        default=False, help_text=_("Designates whether source supports retargeting automatically.")
    )

    supports_video = models.BooleanField(default=False, help_text=_("Designates whether source supports video."))
    supports_display = models.BooleanField(
        default=False, help_text=_("Designates whether source supports display ads.")
    )

    impression_trackers_count = models.PositiveSmallIntegerField(
        default=0, help_text=_("Number of impression trackers we know this source supports.")
    )

    content_ad_submission_type = models.IntegerField(
        default=dash.constants.SourceSubmissionType.DEFAULT, choices=dash.constants.SourceSubmissionType.get_choices()
    )
    content_ad_submission_policy = models.IntegerField(
        default=dash.constants.SourceSubmissionPolicy.AUTOMATIC,
        choices=dash.constants.SourceSubmissionPolicy.get_choices(),
        help_text=_("Designates weather content ads are submitted automatically"),
    )

    default_cpc_cc = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0.15"), verbose_name="Default CPC"
    )
    default_mobile_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0.15"),
        verbose_name="Default CPC (if ad group is targeting mobile only)",
    )

    default_cpm = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("1.00"), verbose_name="Default CPM"
    )
    default_mobile_cpm = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("1.00"),
        verbose_name="Default CPM (if ad group is targeting mobile only)",
    )

    default_daily_budget_cc = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("10.00"), verbose_name="Default daily spend cap"
    )

    entity_tags = tagulous.models.TagField(to="EntityTag", blank=True)

    objects = BaseManager.from_queryset(queryset.SourceQuerySet)()
