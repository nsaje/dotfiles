from django.contrib import admin

import models


class SupplyReportRecipientAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'email', 'source__name']
    list_display = (
        'email',
        'first_name',
        'last_name',
        'source',
        'created_dt',
        'modified_dt',
    )
    readonly_fields = ('created_dt', 'modified_dt')

admin.site.register(models.SupplyReportRecipient, SupplyReportRecipientAdmin)
