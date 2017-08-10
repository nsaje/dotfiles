from django.contrib import admin
from django.core import urlresolvers

import models


class IsScheduledListFilter(admin.SimpleListFilter):
    title = 'is scheduled report'
    parameter_name = 'is_scheduled'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(scheduled_report__isnull=False)
        if self.value() == 'no':
            return queryset.filter(scheduled_report__isnull=True)


class ReportJobAdmin(admin.ModelAdmin):
    model = models.ReportJob
    list_display = (
        'id',
        'created_dt',
        'user',
        'status',
        'result',
        'is_scheduled',
        'is_email',
    )

    list_filter = (
        'status',
        IsScheduledListFilter,
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
        return u'<a href="%s">%s</a>' % (link, obj.scheduled_report.name)
    link_to_scheduled_report.allow_tags = True

    def is_scheduled(self, obj):
        return obj.scheduled_report is not None
    is_scheduled.boolean = True

    def is_email(self, obj):
        return 'options' in obj.query and \
            'recipients' in obj.query['options'] and \
            len(obj.query['options']['recipients']) > 0
    is_email.boolean = True


admin.site.register(models.ReportJob, ReportJobAdmin)
