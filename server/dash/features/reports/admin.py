from django.contrib import admin
from django.core import urlresolvers

import models


class ReportJobAdmin(admin.ModelAdmin):
    model = models.ReportJob
    list_display = (
        'id',
        'created_dt',
        'user',
        'status',
        'result',
        'is_scheduled',
    )

    list_filter = (
        'status',
    )

    readonly_fields = (
        'created_dt',
        'user',
        'query',
        'result',
        'scheduled_report',
        'link_to_scheduled_report',
    )

    ordering = ('-created_dt', )

    def link_to_scheduled_report(self, obj):
        if obj.scheduled_report is None:
            return ''
        link = urlresolvers.reverse("admin:dash_scheduledreport_change", args=[obj.scheduled_report.id])
        print(link)
        return u'<a href="%s">%s</a>' % (link, obj.scheduled_report.name)
    link_to_scheduled_report.allow_tags = True

    def is_scheduled(self, obj):
        return obj.scheduled_report is not None
    is_scheduled.boolean = True


admin.site.register(models.ReportJob, ReportJobAdmin)
