from django.core.urlresolvers import reverse
from django.contrib import admin
from django.utils.html import format_html

from . import models


class CampaignBudgetDepletionNotificationAdmin(admin.ModelAdmin):
    search_fields = ['campaign__name']
    list_display = (
        'account_manager',
        'campaign',
        'available_budget',
        'yesterdays_spend',
        'stopped',
        'created_dt'
    )
    readonly_fields = ['created_dt']

admin.site.register(models.CampaignBudgetDepletionNotification, CampaignBudgetDepletionNotificationAdmin)


class AutopilotAdGroupSourceBidCpcLogAdmin(admin.ModelAdmin):
    search_fields = ['ad_group__name']
    list_display = (
        'campaign',
        'ad_group',
        'ad_group_source',
        'previous_cpc_cc',
        'new_cpc_cc',
        'yesterdays_spend_cc',
        'current_daily_budget_cc',
        'yesterdays_clicks',
        'created_dt',
        'comments'
    )
    readonly_fields = ['created_dt']

admin.site.register(models.AutopilotAdGroupSourceBidCpcLog, AutopilotAdGroupSourceBidCpcLogAdmin)


class AutopilotLogAdmin(admin.ModelAdmin):
    search_fields = ['ad_group__name']
    list_display = (
        'get_campaign',
        'ad_group',
        'ad_group_source',
        'autopilot_type',
        'campaign_goal',
        'previous_cpc_cc',
        'new_cpc_cc',
        'previous_daily_budget',
        'new_daily_budget',
        'yesterdays_spend_cc',
        'goal_value',
        'yesterdays_clicks',
        'created_dt',
        'cpc_comments',
        'budget_comments'
    )
    readonly_fields = ['created_dt']

    def get_campaign(self, obj):
        return obj.ad_group.campaign
    get_campaign.short_description = 'Campaign'

admin.site.register(models.AutopilotLog, AutopilotLogAdmin)


class CampaignStopLogAdmin(admin.ModelAdmin):
    search_fields = ['campaign__name']
    list_display = (
        'id',
        'campaign_link',
        'formatted_notes',
        'created_dt',
    )
    readonly_fields = ['created_dt']

    def formatted_notes(self, obj):
        return format_html('<div style="white-space: pre-wrap">{}</div>', obj.notes)
    formatted_notes.short_description = 'Notes'

    def campaign_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:dash_campaign_change', args=(obj.campaign_id,)),
            obj.campaign.name
        )
    campaign_link.short_description = 'Campaign'

admin.site.register(models.CampaignStopLog, CampaignStopLogAdmin)
