import html
import json

from django.contrib import admin
from django.urls import reverse
from django.utils import html as django_html
from django.utils.safestring import mark_safe

import utils.admin_common

from .reportjob import ReportJob


class IsScheduledListFilter(admin.SimpleListFilter):
    title = "is scheduled report"
    parameter_name = "is_scheduled"

    def lookups(self, request, model_admin):
        return (("yes", "Yes"), ("no", "No"))

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(scheduled_report__isnull=False)
        if self.value() == "no":
            return queryset.filter(scheduled_report__isnull=True)


class ReportJobAdmin(admin.ModelAdmin):
    model = ReportJob
    paginator = utils.admin_common.LargeTablePaginator
    show_full_result_count = False
    list_display = (
        "id",
        "created_dt",
        "start_dt",
        "end_dt",
        "user",
        "status",
        "report_fields",
        "result",
        "is_scheduled",
        "is_email",
    )

    list_filter = ("status", IsScheduledListFilter)

    readonly_fields = (
        "created_dt",
        "modified_dt",
        "start_dt",
        "end_dt",
        "user",
        "query_",
        "result",
        "scheduled_report",
        "link_to_scheduled_report",
    )
    fields = readonly_fields

    search_fields = ("user__email", "result")

    def get_queryset(self, request):
        qs = super(ReportJobAdmin, self).get_queryset(request)
        qs = qs.select_related("user")
        return qs

    def report_fields(self, obj):
        try:
            return ", ".join(f["field"] for f in obj.query["fields"])
        except Exception:
            return "malformed query"

    def query_(self, obj):
        body = json.dumps(obj.query, indent=4)
        return django_html.mark_safe('<div style="overflow: hidden;"><pre>' + html.escape(body) + "</pre></div>")

    def link_to_scheduled_report(self, obj):
        if obj.scheduled_report is None:
            return ""
        link = reverse("admin:dash_scheduledreport_change", args=[obj.scheduled_report.id])
        return mark_safe('<a href="%s">%s</a>' % (link, obj.scheduled_report.name))

    def is_scheduled(self, obj):
        return obj.scheduled_report is not None

    is_scheduled.boolean = True

    def is_email(self, obj):
        return (
            "options" in obj.query
            and "recipients" in obj.query["options"]
            and len(obj.query["options"]["recipients"]) > 0
        )

    is_email.boolean = True


admin.site.register(ReportJob, ReportJobAdmin)
