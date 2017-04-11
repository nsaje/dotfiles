from django.contrib import admin

from restapi import models


class ReportJobAdmin(admin.ModelAdmin):
    model = models.ReportJob
    list_display = (
        'id',
        'created_dt',
        'user',
        'status',
        'result'
    )

    list_filter = (
        'status',
    )

    readonly_fields = ('created_dt', 'user', 'query', 'result')

    ordering = ('-created_dt', )


admin.site.register(models.ReportJob, ReportJobAdmin)
