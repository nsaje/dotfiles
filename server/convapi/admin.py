
from django.contrib import admin

from convapi import models
from convapi import constants


class GAReportLogAdmin(admin.ModelAdmin):

    list_display = (
        'datetime',
        'for_date',
        'state_',
        'no_errors_',
        'ad_groups_',
        'visits_reported',
        'visits_imported_',
        'nomatch',
        'multimatch',
        'multimatch_clicks',
        'email_subject',
        'csv_filename',
    )

    def no_errors_(self, obj):
        return obj.errors is None
    no_errors_.boolean = True

    def state_(self, obj):
        color = '#000'
        if obj.state == constants.GAReportState.SUCCESS:
            color = '#5cb85c'
        if obj.state == constants.GAReportState.FAILED:
            color = '#d9534f'
        if obj.state == constants.GAReportState.EMPTY_REPORT:
            color = '#f0f'
        return '<span style="color:{color}">{state}</span>'.format(
            color=color,
            state=obj.get_state_display(),
        )
    state_.allow_tags = True
    state_.admin_order_field = 'state'

    def visits_imported_(self, obj):
        color = '#000'
        if obj.visits_imported is None or obj.visits_reported is None or obj.visits_imported < obj.visits_reported:
            color = '#f00'
        return '<span style="color:{color}">{visits}</span>'.format(
            color=color,
            visits=obj.visits_imported,
        )
    visits_imported_.allow_tags = True

    def ad_groups_(self, obj):
        if obj.ad_groups is None:
            return '<span style="color:red">None</span>'
        if ',' in obj.ad_groups:
            return '<span style="font-weight:bold">{}</span>'.format(obj.ad_groups)
        return obj.ad_groups
    ad_groups_.allow_tags = True


admin.site.register(models.GAReportLog, GAReportLogAdmin)
