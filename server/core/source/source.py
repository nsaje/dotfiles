# -*- coding: utf-8 -*-

from decimal import Decimal
from django.db import models
from django.utils.translation import ugettext_lazy as _

import core.common
import core.entity
from dash import constants

import core.common
import core.entity
import utils.exc


class Source(models.Model):
    class Meta:
        app_label = "dash"

    id = models.AutoField(primary_key=True)
    source_type = models.ForeignKey("SourceType", null=True)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    tracking_slug = models.CharField(max_length=50, null=False, blank=False, unique=True, verbose_name="Tracking slug")
    bidder_slug = models.CharField(max_length=50, null=True, blank=True, unique=True, verbose_name="B1 Slug")
    maintenance = models.BooleanField(default=True)
    deprecated = models.BooleanField(default=False, null=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    released = models.BooleanField(default=True)

    supports_retargeting = models.BooleanField(
        default=False, help_text=_("Designates whether source supports retargeting automatically.")
    )
    supports_retargeting_manually = models.BooleanField(
        default=False, help_text=_("Designates whether source supports retargeting via manual action.")
    )

    supports_video = models.BooleanField(default=False, help_text=_("Designates whether source supports video."))

    impression_trackers_count = models.PositiveSmallIntegerField(
        default=0, help_text=_("Number of impression trackers we know this source supports.")
    )

    content_ad_submission_type = models.IntegerField(
        default=constants.SourceSubmissionType.DEFAULT, choices=constants.SourceSubmissionType.get_choices()
    )
    content_ad_submission_policy = models.IntegerField(
        default=constants.SourceSubmissionPolicy.AUTOMATIC,
        choices=constants.SourceSubmissionPolicy.get_choices(),
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

    default_daily_budget_cc = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("10.00"), verbose_name="Default daily spend cap"
    )

    objects = core.common.QuerySetManager()

    def get_clean_slug(self):
        return self.bidder_slug[3:] if self.bidder_slug.startswith("b1_") else self.bidder_slug

    def can_update_state(self):
        return self.source_type.can_update_state() and not self.maintenance and not self.deprecated

    def can_update_cpc(self):
        return self.source_type.can_update_cpc() and not self.maintenance and not self.deprecated

    def can_update_daily_budget_manual(self):
        return self.source_type.can_update_daily_budget_manual() and not self.maintenance and not self.deprecated

    def can_update_daily_budget_automatic(self):
        return self.source_type.can_update_daily_budget_automatic() and not self.maintenance and not self.deprecated

    def can_manage_content_ads(self):
        return self.source_type.can_manage_content_ads() and not self.maintenance and not self.deprecated

    def has_3rd_party_dashboard(self):
        return self.source_type.has_3rd_party_dashboard()

    def can_modify_start_date(self):
        return self.source_type.can_modify_start_date() and not self.maintenance and not self.deprecated

    def can_modify_end_date(self):
        return self.source_type.can_modify_end_date() and not self.maintenance and not self.deprecated

    def can_modify_device_targeting(self):
        return self.source_type.can_modify_device_targeting() and not self.maintenance and not self.deprecated

    def can_modify_targeting_for_region_type_automatically(self, region_type):
        return self.source_type.can_modify_targeting_for_region_type_automatically(region_type)

    def can_modify_targeting_for_region_type_manually(self, region_type):
        return self.source_type.can_modify_targeting_for_region_type_manually(region_type)

    def can_modify_ad_group_name(self):
        return self.source_type.can_modify_ad_group_name() and not self.maintenance and not self.deprecated

    def can_modify_ad_group_iab_category_automatic(self):
        return (
            self.source_type.can_modify_ad_group_iab_category_automatic()
            and not self.maintenance
            and not self.deprecated
        )

    def can_modify_ad_group_iab_category_manual(self):
        return (
            self.source_type.can_modify_ad_group_iab_category_manual() and not self.maintenance and not self.deprecated
        )

    def update_tracking_codes_on_content_ads(self):
        return self.source_type.update_tracking_codes_on_content_ads()

    def can_fetch_report_by_publisher(self):
        return self.source_type.can_fetch_report_by_publisher()

    def can_modify_publisher_blacklist_automatically(self):
        return (
            self.source_type.can_modify_publisher_blacklist_automatically()
            and not self.maintenance
            and not self.deprecated
        )

    def can_modify_retargeting_automatically(self):
        return self.supports_retargeting and not self.maintenance and not self.deprecated

    def can_modify_retargeting_manually(self):
        return self.supports_retargeting_manually and not self.maintenance and not self.deprecated

    def can_set_max_cpm(self):
        return self.source_type.can_set_max_cpm() and not self.maintenance and not self.deprecated

    def get_default_settings(self):
        try:
            default_settings = self.defaultsourcesettings
        except core.source.DefaultSourceSettings.DoesNotExist:
            raise utils.exc.MissingDataError("No default settings set for {}.".format(self.name))

        if not default_settings.credentials:
            raise utils.exc.MissingDataError("No default credentials set in {}.".format(default_settings))

        return default_settings

    class QuerySet(models.QuerySet):
        def filter_can_manage_content_ads(self):
            return self.filter(id__in=[x.id for x in self.select_related("source_type") if x.can_manage_content_ads()])

    def __str__(self):
        return self.name
