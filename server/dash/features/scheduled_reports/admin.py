from django.contrib import admin

import models


class ScheduledReportAdmin(admin.ModelAdmin):
    model = models.ScheduledReport
    list_display = (
        'name',
        'created_dt',
        'user',
        'account',
        'state',
        'sending_frequency',
        'day_of_week',
        'time_period',
        'get_recipients'
    )

    list_filter = (
        'state',
        'sending_frequency',
        'day_of_week',
        'time_period'
    )

    readonly_fields = ('created_dt', 'user')

    ordering = ('-created_dt', )


admin.site.register(models.ScheduledReport, ScheduledReportAdmin)
