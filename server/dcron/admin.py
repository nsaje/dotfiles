from django.contrib import admin
from django.utils.html import format_html

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
        "warning_wait",
        "max_duration",
        "min_separation",
        "manual_override",
        "pause_execution",
    )
    search_fields = ("job__command_name",)
    list_filter = ("job__alert", "enabled", "severity", "manual_override", "pause_execution")
    readonly_fields = ("job", "schedule", "full_command", "enabled")
