from django.contrib import admin
from django.core import urlresolvers
from django.db.models import Prefetch

from dash.features import reports
from utils import dates_helper

import models


class ScheduledReportAdmin(admin.ModelAdmin):
    model = models.ScheduledReport
    list_display = (
        'name',
        'user',
        'account',
        'state',
        'today_job_status',
        'sending_frequency',
        'day_of_week',
        'time_period',
        'get_recipients',
    )

    list_filter = (
        'state',
        'sending_frequency',
        'day_of_week',
        'time_period'
    )

    readonly_fields = ('created_dt', 'user')

    ordering = ('-created_dt', )

    def get_queryset(self, request):
        today = dates_helper.utc_today()
        qs = super(ScheduledReportAdmin, self).get_queryset(request)
        qs = qs.select_related('account', 'user')
        return qs.prefetch_related(
            Prefetch('jobs', to_attr='last_job', queryset=(
                reports.ReportJob.objects
                .order_by('scheduled_report_id', '-created_dt')
                .filter(scheduled_report__isnull=False, created_dt__gt=today)
                .distinct('scheduled_report_id'))
            )
        )

    def today_job_status(self, obj):
        if len(obj.last_job) > 0:
            link = urlresolvers.reverse("admin:dash_reportjob_change", args=[obj.last_job[0].id])
            return u'<a href="%s">%s</a>' % (link, reports.constants.ReportJobStatus.get_text(obj.last_job[0].status))
    today_job_status.allow_tags = True


admin.site.register(models.ScheduledReport, ScheduledReportAdmin)
