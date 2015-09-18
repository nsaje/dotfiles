from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from convapi import models
from convapi import constants


class TestReportsListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Report Type')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'test-report'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('non-test', _('Reports')),
            ('test', _('Test Reports')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'test':
            return queryset.filter(from_address='test@zemanta.com')
        elif self.value() == 'non-test':
            return queryset.exclude(from_address='test@zemanta.com')
        return queryset


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
        'from_address'
    )

    search_fields = (
        'ad_groups',
        'email_subject',
        'csv_filename',
        'from_address'
    )

    list_filter = (
        'state',
        TestReportsListFilter,
    )

    def no_errors_(self, obj):
        return obj.errors is None
    no_errors_.boolean = True

    def state_(self, obj):
        color = '#000'
        if obj.state == constants.ReportState.SUCCESS:
            color = '#5cb85c'
        if obj.state == constants.ReportState.FAILED:
            color = '#d9534f'
        if obj.state == constants.ReportState.EMPTY_REPORT:
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


class ReportLogAdmin(admin.ModelAdmin):

    list_display = (
        'datetime',
        'for_date',
        'state_',
        'no_errors_',
        'visits_reported',
        'visits_imported_',
        'email_subject',
        'report_filename',
        'from_address'
    )

    search_fields = (
        'email_subject',
        'report_filename',
        'from_address'
    )

    list_filter = (
        'state',
        TestReportsListFilter,
    )

    def no_errors_(self, obj):
        return obj.errors is None
    no_errors_.boolean = True

    def state_(self, obj):
        color = '#000'
        if obj.state == constants.ReportState.SUCCESS:
            color = '#5cb85c'
        if obj.state == constants.ReportState.FAILED:
            color = '#d9534f'
        if obj.state == constants.ReportState.EMPTY_REPORT:
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


admin.site.register(models.GAReportLog, GAReportLogAdmin)
admin.site.register(models.ReportLog, ReportLogAdmin)
