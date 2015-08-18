from django.contrib import admin

from . import models

class CampaignBudgetDepletionSettingsAdmin(admin.ModelAdmin):
    search_fields = ['account_manager', 'campaign']
    list_display = (
        'account_manager',
        'campaign',
        'available_budget',
        'yesterdays_spendt',
        'created_dt'
    )
    readonly_fields = ['created_dt']

admin.site.register(models.CampaignBudgetDepletionSettings, CampaignBudgetDepletionSettingsAdmin)
