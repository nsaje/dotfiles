from django.contrib import admin

from dash.features.supply_reports.service import send_supply_reports

from . import models


class SupplyReportRecipientAdmin(admin.ModelAdmin):
    search_fields = ["first_name", "last_name", "email", "source__name"]
    list_display = (
        "email",
        "first_name",
        "last_name",
        "source",
        "outbrain_publisher_ids",
        "created_dt",
        "last_sent_dt",
    )
    readonly_fields = ("created_dt", "modified_dt", "last_sent_dt")
    list_filter = ("source",)

    def send_report_externally(self, request, queryset):
        recipient_ids = queryset.values_list("id", flat=True)
        if recipient_ids:
            send_supply_reports(recipient_ids=recipient_ids)

    def send_report_to_user(self, request, queryset):
        recipient_ids = queryset.values_list("id", flat=True)
        if recipient_ids:
            send_supply_reports(recipient_ids=recipient_ids, overwrite_recipients_email=request.user.email)

    send_report_externally.short_description = "Send report to recipient"
    send_report_to_user.short_description = "Send report to me"
    actions = [send_report_externally, send_report_to_user]


admin.site.register(models.SupplyReportRecipient, SupplyReportRecipientAdmin)
