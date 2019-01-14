from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

import dash.models

from . import models
from .campaignstop.admin import RealTimeCampaignStopLogAdmin


class CampaignBudgetDepletionNotificationAdmin(admin.ModelAdmin):
    search_fields = ("campaign__name",)
    list_display = ("account_manager", "campaign", "available_budget", "yesterdays_spend", "stopped", "created_dt")
    readonly_fields = ("created_dt",)
    raw_id_fields = ("campaign",)
    autocomplete_fields = ("account_manager",)

    def get_queryset(self, request):
        qs = super(CampaignBudgetDepletionNotificationAdmin, self).get_queryset(request)
        qs = qs.select_related("account_manager", "campaign")
        return qs


admin.site.register(models.CampaignBudgetDepletionNotification, CampaignBudgetDepletionNotificationAdmin)


class AutopilotLogAdmin(admin.ModelAdmin):
    search_fields = ("ad_group__name",)
    list_display = (
        "get_campaign",
        "ad_group",
        "ad_group_source",
        "autopilot_type",
        "is_rtb_as_one",
        "campaign_goal",
        "previous_cpc_cc",
        "new_cpc_cc",
        "previous_daily_budget",
        "new_daily_budget",
        "yesterdays_spend_cc",
        "goal_value",
        "campaign_goal_optimal_value",
        "yesterdays_clicks",
        "created_dt",
        "cpc_comments",
        "budget_comments",
    )
    readonly_fields = ("created_dt",)
    raw_id_fields = ("campaign", "ad_group")
    autocomplete_fields = ("ad_group_source",)

    def get_queryset(self, request):
        qs = super(AutopilotLogAdmin, self).get_queryset(request)
        qs = qs.select_related("ad_group_source__source", "ad_group_source__ad_group", "ad_group__campaign")
        return qs

    def get_campaign(self, obj):
        return obj.ad_group.campaign

    get_campaign.short_description = "Campaign"


admin.site.register(models.AutopilotLog, AutopilotLogAdmin)


class CampaignListFilter(admin.SimpleListFilter):
    title = "Campaign"
    parameter_name = "campaign_id"

    def lookups(self, request, model_admin):
        campaign_ids = models.CampaignStopLog.objects.all().values_list("campaign_id", flat=True)

        lst = []
        campaigns = dash.models.Campaign.objects.filter(id__in=campaign_ids).select_related("account").order_by("-id")
        for campaign in campaigns:
            label = campaign.account.name + " - " + campaign.name + " (id={})".format(campaign.id)
            lst.append((campaign.id, label))
        return lst

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.filter(campaign_id=self.value())

        return queryset


class CampaignStopLogAdmin(admin.ModelAdmin):
    search_fields = ["campaign__name", "campaign_id", "campaign__account_id"]
    list_display = ("id", "campaign_link", "formatted_notes", "created_dt")
    readonly_fields = ["created_dt"]
    list_filter = [CampaignListFilter]
    raw_id_fields = ("campaign",)

    def get_queryset(self, request):
        qs = super(CampaignStopLogAdmin, self).get_queryset(request)
        qs = qs.select_related("campaign")
        return qs

    def formatted_notes(self, obj):
        return format_html('<div style="white-space: pre-wrap">{}</div>', obj.notes)

    formatted_notes.short_description = "Notes"

    def campaign_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>', reverse("admin:dash_campaign_change", args=(obj.campaign_id,)), obj.campaign.name
        )

    campaign_link.short_description = "Campaign"


admin.site.register(models.CampaignStopLog, CampaignStopLogAdmin)
admin.site.register(models.RealTimeCampaignStopLog, RealTimeCampaignStopLogAdmin)
