from django.contrib import admin

from . import models

class CampaignBudgetDepletionNotifactionAdmin(admin.ModelAdmin):
    search_fields = ['account_manager', 'campaign']
    list_display = (
        'account_manager',
        'campaign',
        'available_budget',
        'yesterdays_spend',
        'created_dt'
    )
    readonly_fields = ['created_dt']

admin.site.register(models.CampaignBudgetDepletionNotifaction, CampaignBudgetDepletionNotifactionAdmin)
