from django.contrib import admin

from dash.features.supply_reports.service import send_supply_reports

from . import models


class SupplyReportRecipientAdmin(admin.ModelAdmin):
    search_fields = ["first_name", "last_name", "email", "source__name"]
    list_display = ("email", "first_name", "last_name", "source", "outbrain_publisher_ids", "created_dt", "modified_dt")
    readonly_fields = ("created_dt", "modified_dt", "last_sent_dt")
    list_filter = ("source",)

    def send_report(self, request, queryset):
        recipient_ids = queryset.values_list("id", flat=True)
        if recipient_ids:
            send_supply_reports(recipient_ids=recipient_ids)

    send_report.short_description = "Send report"
    actions = [send_report]


admin.site.register(models.SupplyReportRecipient, SupplyReportRecipientAdmin)
