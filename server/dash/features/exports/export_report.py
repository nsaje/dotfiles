# -*- coding: utf-8 -*-
import jsonfield
from django.conf import settings
from django.db import models

import core.models
from dash import constants
from utils.json_helper import JSONFIELD_DUMP_KWARGS


class ExportReport(models.Model):
    id = models.AutoField(primary_key=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", null=False, blank=False, on_delete=models.PROTECT
    )

    ad_group = models.ForeignKey("AdGroup", blank=True, null=True, on_delete=models.PROTECT)
    campaign = models.ForeignKey("Campaign", blank=True, null=True, on_delete=models.PROTECT)
    account = models.ForeignKey("Account", blank=True, null=True, on_delete=models.PROTECT)

    granularity = models.IntegerField(
        default=constants.ScheduledReportGranularity.CONTENT_AD,
        choices=constants.ScheduledReportGranularity.get_choices(),
    )

    breakdown_by_day = models.BooleanField(null=False, blank=False, default=False)
    breakdown_by_source = models.BooleanField(null=False, blank=False, default=False)
    include_model_ids = models.BooleanField(null=False, blank=False, default=False)
    include_totals = models.BooleanField(null=False, blank=False, default=False)
    include_missing = models.BooleanField(null=False, blank=False, default=False)

    order_by = models.CharField(max_length=20, null=True, blank=True)
    additional_fields = models.TextField(null=True, blank=True)
    filtered_sources = models.ManyToManyField(core.models.Source, blank=True)
    filtered_agencies = models.ManyToManyField(core.models.Agency, blank=True)
    filtered_account_types = jsonfield.JSONField(blank=True, default=[], dump_kwargs=JSONFIELD_DUMP_KWARGS)

    def __str__(self):
        return " ".join(
            [
                _f
                for _f in (
                    constants.ScheduledReportLevel.get_text(self.level),
                    "(",
                    (self.account.name if self.account else ""),
                    (self.campaign.name if self.campaign else ""),
                    (self.ad_group.name if self.ad_group else ""),
                    ") - by",
                    constants.ScheduledReportGranularity.get_text(self.granularity),
                    ("by Source" if self.breakdown_by_source else ""),
                    ("by Day" if self.breakdown_by_day else ""),
                )
                if _f
            ]
        )

    @property
    def level(self):
        if self.account:
            return constants.ScheduledReportLevel.ACCOUNT
        elif self.campaign:
            return constants.ScheduledReportLevel.CAMPAIGN
        elif self.ad_group:
            return constants.ScheduledReportLevel.AD_GROUP
        return constants.ScheduledReportLevel.ALL_ACCOUNTS

    def get_exported_entity_name(self):
        if self.account:
            return self.account.name
        elif self.campaign:
            return self.campaign.name
        elif self.ad_group:
            return self.ad_group.name
        return "All Accounts"

    def get_additional_fields(self):
        import dash.views.helpers

        return dash.views.helpers.get_additional_columns(self.additional_fields)

    def get_filtered_sources(self):
        all_sources = core.models.Source.objects.all()
        if len(self.filtered_sources.all()) == 0:
            return all_sources
        return all_sources.filter(id__in=[source.id for source in self.filtered_sources.all()])

    def get_filtered_agencies(self):
        if len(self.filtered_agencies.all()) == 0:
            return core.models.Agency.objects.all()
        return self.filtered_agencies.all()

    def get_filtered_account_types(self):
        if len(self.filtered_account_types or []) == 0:
            return [constants.AccountType.get_text(c) for c in constants.AccountType.get_all()]
        return [constants.AccountType.get_text(c) for c in self.filtered_account_types]
