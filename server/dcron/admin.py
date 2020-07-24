from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from dcron import constants
from dcron import models


class DCronJobSettingsInline(admin.StackedInline):
    model = models.DCronJobSettings
    can_delete = False
    readonly_fields = ("schedule", "full_command", "enabled")


@admin.register(models.DCronJob)
class DCronJobAdmin(admin.ModelAdmin):
    ordering = ["command_name"]
    list_display = (
        "command_name",
        "enabled",
        "host",
        "duration",
        "live_logs",
        "logs",
        "history",
        "executed_dt",
        "completed_dt",
        "colored_alert",
        "paused",
    )
    search_fields = ("command_name",)
    list_filter = (
        "alert",
        "dcronjobsettings__enabled",
        "dcronjobsettings__severity",
        "dcronjobsettings__ownership",
        "dcronjobsettings__manual_override",
        "dcronjobsettings__pause_execution",
    )
    readonly_fields = ("command_name", "host", "executed_dt", "completed_dt", "colored_alert")
    exclude = ("alert",)
    list_select_related = ["dcronjobsettings"]
    inlines = [DCronJobSettingsInline]

    def duration(self, obj):
        if obj.executed_dt and obj.completed_dt:
            return obj.completed_dt - obj.executed_dt

        return "-"

    duration.short_description = "Duration"

    def logs(self, obj):
        log_viewer_link = settings.DCRON.get("log_viewer_link", "{command_name}").format(
            command_name=obj.command_name.replace("_", "")
        )
        return mark_safe('<a href="%s">%s</a>' % (log_viewer_link, "Logs"))

    def live_logs(self, obj):
        log_viewer_link = settings.DCRON.get("log_viewer_link_live", "{command_name},{host}").format(
            command_name=obj.command_name.replace("_", ""), host=obj.host
        )
        return mark_safe('<a href="%s">%s</a>' % (log_viewer_link, "Current execution logs"))

    def history(self, obj):
        return format_html(
            '<a href="{}">History entries</a>',
            reverse("admin:dcron_dcronjobhistory_changelist") + "?command_name=" + obj.command_name,
        )

    def enabled(self, obj):
        return obj.dcronjobsettings.enabled

    enabled.boolean = True
    enabled.short_description = "Enabled"

    def paused(self, obj):
        return obj.dcronjobsettings.pause_execution

    paused.boolean = True
    paused.short_description = "Paused"

    def colored_alert(self, obj):
        if obj.alert in (constants.Alert.EXECUTION, constants.Alert.DURATION, constants.Alert.FAILURE):
            color = "yellow" if obj.alert == constants.Alert.DURATION else "tomato"
            return format_html(
                '<span style="background-color: {};">{}</span>', color, constants.Alert.get_name(obj.alert)
            )
        else:
            return constants.Alert.get_name(obj.alert)

    colored_alert.short_description = "Alert"


@admin.register(models.DCronJobSettings)
class DCronJobSettingsAdmin(admin.ModelAdmin):
    ordering = ["job__command_name"]
    raw_id_fields = ("job",)
    list_display = (
        "job",
        "schedule",
        "full_command",
        "enabled",
        "severity",
        "ownership",
        "warning_wait",
        "max_duration",
        "min_separation",
        "manual_override",
        "pause_execution",
    )
    search_fields = ("job__command_name",)
    list_filter = ("job__alert", "enabled", "severity", "ownership", "manual_override", "pause_execution")
    readonly_fields = ("job", "schedule", "full_command", "enabled")


@admin.register(models.DCronJobHistory)
class DCronJobHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "command_name",
        "command_definition",
        "colored_status",
        "host",
        "duration",
        "executed_dt",
        "completed_dt",
        "expected_max_duration",
    )
    search_fields = ("command_name",)
    list_filter = ("command_name",)
    readonly_fields = ("command_name", "status", "host", "executed_dt", "completed_dt", "expected_max_duration")

    def command_definition(self, obj):
        return format_html(
            '<a href="{}">Definition</a>', reverse("admin:dcron_dcronjob_changelist") + "?q=" + obj.command_name
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def duration(self, obj):
        duration = obj.completed_dt - obj.executed_dt
        if duration.total_seconds() > obj.expected_max_duration:
            return format_html('<span style="background-color: yellow;">{}</span>', str(duration))
        else:
            return str(duration)

    duration.short_description = "Duration"

    def colored_status(self, obj):
        color = "tomato" if obj.status == constants.Alert.FAILURE else "lime"

        return format_html('<span style="background-color: {};">{}</span>', color, constants.Alert.get_name(obj.status))

    colored_status.short_description = "Status"
