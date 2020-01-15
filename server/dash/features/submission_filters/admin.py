from django.contrib import admin

from core import models
from utils import k1_helper

from . import forms


class SubmissionFilterAdmin(admin.ModelAdmin):
    form = forms.SubmissionFilterForm
    raw_id_fields = ("content_ad", "ad_group", "campaign", "account", "agency")
    list_display = ("state", "source", "_agency", "_account", "_campaign", "_ad_group", "_content_ad")
    list_filter = ("state", "source")
    search_fields = (
        "source__name",
        "agency__id",
        "agency__name",
        "account__name",
        "account__id",
        "campaign__name",
        "campaign__id",
        "ad_group__name",
        "ad_group__id",
        "content_ad__id",
        "content_ad__title",
        "content_ad__brand_name",
    )
    readonly_fields = ("created_dt",)
    autocomplete_fields = ("source", "agency", "account")

    def get_queryset(self, request):
        qs = super(SubmissionFilterAdmin, self).get_queryset(request)
        return qs.select_related("source", "content_ad", "ad_group", "campaign", "account", "agency")

    def _content_ad(self, obj):
        return obj.content_ad and "{}: {}".format(obj.content_ad_id, obj.content_ad.title) or ""

    def _ad_group(self, obj):
        return obj.ad_group and "{}: {}".format(obj.ad_group_id, obj.ad_group.name) or ""

    def _campaign(self, obj):
        return obj.campaign and "{}: {}".format(obj.campaign_id, obj.campaign.name) or ""

    def _account(self, obj):
        return obj.account and "{}: {}".format(obj.account_id, obj.account.name) or ""

    def _agency(self, obj):
        return obj.agency and "{}: {}".format(obj.agency_id, obj.agency.name) or ""

    def save_model(self, request, submission_filter, form, change):
        data = form.cleaned_data
        if data.get("agency"):
            k1_helper.update_ad_groups(
                list(models.AdGroup.objects.filter(campaign__account__agency=data["agency"])),
                msg="update submission_filter",
            )
        elif data.get("account"):
            k1_helper.update_ad_groups(
                list(models.AdGroup.objects.filter(campaign__account=data["account"])), msg="update submission_filter"
            )
        elif data.get("campaign"):
            k1_helper.update_ad_groups(
                list(models.AdGroup.objects.filter(campaign=data["campaign"])), msg="update submission_filter"
            )
        elif data.get("ad_group"):
            k1_helper.update_ad_group(data["ad_group"], msg="update submission_filter")
        elif data.get("content_ad"):
            k1_helper.update_ad_group(
                models.AdGroup.objects.get(contentad__in=[data["content_ad"]]), msg="update submission_filter"
            )
        submission_filter.save()
